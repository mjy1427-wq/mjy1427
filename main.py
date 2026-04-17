import random
import json
import asyncio
import os
import time
from datetime import datetime, date
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ================= 🌐 [0] 웹 서비스용 포트 서버 (Render 전용) =================
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!"

def run_web():
    # Render는 PORT 환경변수를 사용함
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# ================= 🔐 [1] 설정 및 데이터베이스 =================
BOT_TOKEN = "8484299407:AAFgHyNXSHEqrVaij1ocbf6933DGyp7-f-Y"
ADMIN_ID = 7476630349 
NOTICE_CHANNEL = "https://t.me/GCOIN7777"
CS_LINK = "https://t.me/GCOIN_BOT" 

BASE_URL = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/"
DB_FILE = "casino_data.json"

db = {"users": {}, "vault": 100000000000, "history": []}
mine_cooldowns = {}
next_result_cache = {} 

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

def load_db():
    global db
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                db.update(json.load(f))
        except: pass

load_db()

MINERALS = {
    "1티어": {"아다만티움": 5000000, "오리하르콘": 3000000, "다이아몬드": 2000000},
    "2티어": {"미스릴": 1000000, "흑요석": 700000},
    "3티어": {"백금": 400000, "금": 250000, "티타늄": 180000},
    "4티어": {"은": 100000, "비취": 50000, "황동": 30000},
    "5티어": {"철": 25000, "구리": 15000, "석탄": 10000}
}

# ================= 🃏 [2] 바카라 엔진 (45회차 & 관리자 예고) =================
rooms = {}

def get_deck():
    suits = ['spades', 'hearts', 'diamonds', 'clubs']
    ranks = [('ace',1),('2',2),('3',3),('4',4),('5',5),('6',6),('7',7),('8',8),('9',9),('10',0),('jack',0),('queen',0),('king',0)]
    return [{'file': f"{r[0]}_of_{s}.png", 'score': r[1]} for s in suits for r in ranks]

def predict_next_hand():
    deck = get_deck(); random.shuffle(deck)
    p_cards, b_cards = [deck.pop(), deck.pop()], [deck.pop(), deck.pop()]
    ps, bs = sum(c['score'] for c in p_cards) % 10, sum(c['score'] for c in b_cards) % 10
    if ps < 8 and bs < 8:
        if ps <= 5: p_cards.append(deck.pop()); ps = sum(c['score'] for c in p_cards) % 10
        if bs <= 5: b_cards.append(deck.pop()); bs = sum(c['score'] for c in b_cards) % 10
    res = "플" if ps > bs else "뱅" if bs > ps else "타이"
    symbol = "🔴" if res=="플" else "🔵" if res=="뱅" else "🟢"
    return res, symbol

async def baccarat_logic(chat_id, context):
    room = rooms[chat_id]
    round_num = room['round']
    win, win_symbol = next_result_cache.get(chat_id, predict_next_hand())

    await asyncio.sleep(30) 
    await context.bot.send_message(chat_id, f"<b>{round_num}회차 베팅 마감!</b>", parse_mode='HTML')
    
    deck = get_deck(); random.shuffle(deck)
    p_cards, b_cards = [deck.pop(), deck.pop()], [deck.pop(), deck.pop()]
    await context.bot.send_media_group(chat_id, [InputMediaPhoto(BASE_URL + c['file']) for c in p_cards])
    await asyncio.sleep(1)
    await context.bot.send_media_group(chat_id, [InputMediaPhoto(BASE_URL + c['file']) for c in b_cards])

    db["history"].append(win_symbol)
    if len(db["history"]) > 45: db["history"].pop(0)

    for bet in room['bets']:
        u = db["users"].get(str(bet['uid']))
        if u:
            if bet['type'] == win:
                rate = 1.95 if win=="뱅" else 2.0 if win=="플" else 8.0
                win_amt = int(bet['amt'] * rate)
                u['money'] += win_amt
                db['vault'] -= (win_amt - bet['amt'])
            else: db['vault'] += bet['amt']

    await context.bot.send_photo(chat_id, photo=BASE_URL+"grid.png.JPG", 
                                 caption=f"🏆 <b>{round_num}회차 결과: {win_symbol} {win} 승리!</b>", parse_mode='HTML')
    
    n_win, n_sym = predict_next_hand()
    next_result_cache[chat_id] = (n_win, n_sym)
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"📢 <b>다음 {round_num+1}회차 예정 결과:</b>\n{n_sym} {n_win}", parse_mode='HTML')
    
    rooms[chat_id] = {"status": "IDLE", "bets": []}
    save_db()

# ================= 🛠 [3] 메인 핸들러 =================
async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    msg, uid, chat_id = update.message.text, str(update.effective_user.id), update.effective_chat.id
    u = db["users"].get(uid)

    if not u:
        now = datetime.now()
        db["users"][uid] = {
            "name": update.effective_user.first_name, "money": 0, "inv": {}, "mine_count": 0, 
            "durability": 100, "max_durability": 100, "pickaxe_name": "기본 곡괭이",
            "joined": False, "join_date": now.strftime("%Y-%m-%d"), "join_time": now.strftime("%H:%M:%S")
        }
        u = db["users"][uid]

    # --- 명령어 분기 ---
    if msg == ".가입":
        if not u["joined"]: u.update({"joined": True, "money": 100000}); await update.message.reply_text("✅ 가입되었습니다. 10만 G 지급!")

    elif msg == ".명령어":
        help_text = (
            "📜 <b>G-COIN 전체 명령어 리스트</b>\n\n"
            "⛏ <b>[경제/광산]</b>\n"
            ".가입 - 10만 G코인 받고 시작하기\n"
            ".내정보 - 내 잔액, 아이디, 가입정보 확인\n"
            ".출석 - 매일 5만 G코인 보너스\n"
            ".채광 - 40초마다 광물 캐기 (내구도 소모)\n"
            ".인벤 - 보유한 광물 목록 및 가격 확인\n"
            ".판매 - 보유 광물 전체 판매 (버튼 UI)\n"
            ".송금 [ID] [금액] - 유저 간 코인 보내기\n"
            ".랭킹 - 서버 재력가 TOP 10 확인\n\n"
            "🎰 <b>[카지노]</b>\n"
            ".바카라 - 45회차 전적판 확인\n"
            ".플 [금액] - 플레이어 승리에 베팅\n"
            ".뱅 [금액] - 뱅커 승리에 베팅\n"
            ".타이 [금액] - 무승부에 베팅\n\n"
            "💬 <b>[기타]</b>\n"
            "일반 채팅 - 관리자 1:1 상담 접수"
        )
        await update.message.reply_text(help_text, parse_mode='HTML')

    elif msg == ".내정보":
        kb = [[InlineKeyboardButton("📢 공지채널", url=NOTICE_CHANNEL), InlineKeyboardButton("💬 상담채널", url=CS_LINK)]]
        text = f"👤 이름: {u['name']}\n🆔 아이디: {uid}\n💰 G코인: {u['money']:,} G\n📅 가입일자: {u['join_date']}\n⏰ 가입시간: {u['join_time']}"
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

    elif msg == ".채광":
        now_ts = time.time()
        if now_ts - mine_cooldowns.get(uid, 0) < 40: return await update.message.reply_text("⏳ 40초 대기 중...")
        if u["durability"] <= 0: return await update.message.reply_text("❌ 수리 필요!")
        mine_cooldowns[uid] = now_ts; u["durability"] -= 1; u["mine_count"] += 1
        tier = random.choices(list(MINERALS.keys()), weights=[1, 5, 14, 30, 50])[0]
        m_name = random.choice(list(MINERALS[tier].keys())); m_price = MINERALS[tier][m_name]
        u["inv"][m_name] = u["inv"].get(m_name, 0) + 1
        await update.message.reply_text(f"⛏ <b>광물획득!</b>\n💎 {m_name}\n💵 가격: {m_price:,} G\n🛠 {u['pickaxe_name']}\n🔋 내구도: {u['durability']}/{u['max_durability']}", parse_mode='HTML')

    elif msg == ".인벤":
        inv_text = "🎒 <b>보유 광물 목록</b>\n\n"
        for name, count in u["inv"].items():
            if count > 0: inv_text += f"📦 {name} | {count}개\n"
        await update.message.reply_text(inv_text or "🎒 비어 있음", parse_mode='HTML')

    elif msg == ".판매":
        kb = [[InlineKeyboardButton("💰 전체 판매", callback_data="sell_all")]]
        await update.message.reply_text("🛒 보유 광물을 모두 판매하시겠습니까?", reply_markup=InlineKeyboardMarkup(kb))

    elif msg == ".바카라":
        hist_list = db["history"][-45:]
        hist = "".join([f"{h} " + ("\n" if (i+1)%9==0 else "") for i, h in enumerate(hist_list)])
        await update.message.reply_photo(photo=BASE_URL+"grid.png.JPG", caption=f"📊 <b>최근 45회차 전적</b>\n━━━━━━━━━━\n{hist}\n━━━━━━━━━━", parse_mode='HTML')

    elif msg.startswith((".플 ", ".뱅 ", ".타이 ")):
        try:
            amt = int(msg.split()[1]); b_type = "플" if ".플" in msg else "뱅" if ".뱅" in msg else "타이"
            if u["money"] >= amt:
                u["money"] -= amt
                if chat_id not in rooms or rooms[chat_id]['status'] == "IDLE":
                    rooms[chat_id] = {"status": "BETTING", "bets": [], "round": len(db["history"])+1}
                    asyncio.create_task(baccarat_logic(chat_id, context))
                rooms[chat_id]['bets'].append({"uid": uid, "type": b_type, "amt": amt})
                await update.message.reply_text(f"✅ {b_type} {amt:,}G 베팅!")
        except: pass

    elif int(uid) == ADMIN_ID and msg == ".금고":
        await update.message.reply_text(f"🏦 금고: {db['vault']:,} G")

    save_db()

# 콜백 핸들러
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); u = db["users"].get(uid)
    if query.data == "sell_all" and u:
        total = sum(price * u["inv"].get(name, 0) for tier in MINERALS.values() for name, price in tier.items())
        for tier in MINERALS.values():
            for name in tier: u["inv"][name] = 0
        u["money"] += total; await query.answer(f"{total:,} G 지급!"); await query.edit_message_text(f"💰 전체 판매 완료: {total:,} G")

# ================= 🚀 [4] 실행 =================
def main():
    keep_alive() # 웹 서비스 포트 유지
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), main_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    print("🚀 G-COIN WEB SERVICE RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()
