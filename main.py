import random
import json
import asyncio
import os
from datetime import datetime, date
from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# =========================
# 🔐 1. 설정 및 기본 데이터
# =========================
TOKEN = "8484299407:AAERctChjsjN_B4ml7y5UzHMN7lEg_ujrPA" # 제공하신 토큰
ADMIN_ID = 7476630349 # 관리자 ID
BASE_URL = "https://raw.githubusercontent.com/mjy1427/mjy1427/main/"
DB_FILE = "casino_data.json"

# 초기 데이터 (금고 5,000억)
db = {
    "users": {},
    "vault": 500000000000, 
    "history": [] 
}

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

def load_db():
    global db
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db.update(json.load(f))

# 광물 및 곡괭이 설정
MINERALS = {
    "1티어": {"아다만티움": 5000000, "오리하르콘": 3000000, "다이아몬드": 2000000},
    "2티어": {"미스릴": 1000000, "흑요석": 700000},
    "3티어": {"백금": 400000, "금": 250000, "티타늄": 180000},
    "4티어": {"은": 100000, "비취": 50000, "황동": 30000},
    "5티어": {"철": 25000, "구리": 15000, "석탄": 10000}
}
PICKAXE = {
    "우드": (1000000, 100), "스톤": (5000000, 300), "아이언": (15000000, 500),
    "골드": (50000000, 1000), "다이아": (250000000, 5000), "아다만티움": (1000000000, 10000)
}

# =========================
# 🃏 2. 바카라 엔진 (멀티룸 독립 로직)
# =========================
rooms = {} 

def get_deck():
    suits = ['spades', 'hearts', 'diamonds', 'clubs']
    ranks = [('ace',1),('2',2),('3',3),('4',4),('5',5),('6',6),('7',7),('8',8),('9',9),('10',0),('jack',0),('queen',0),('king',0)]
    return [{'file': f"{r[0]}_of_{s}.png", 'score': r[1]} for s in suits for r in ranks]

async def baccarat_logic(chat_id, context):
    room = rooms[chat_id]
    await asyncio.sleep(30) # 30초 베팅
    await context.bot.send_message(chat_id, "⛔ 베팅 마감! 결과를 확인합니다.")
    
    deck = get_deck()
    random.shuffle(deck)
    p_cards, b_cards = [deck.pop(), deck.pop()], [deck.pop(), deck.pop()]
    
    # 점수 계산 및 3번째 카드 (간략화된 표준 룰)
    ps = sum(c['score'] for c in p_cards) % 10
    bs = sum(c['score'] for c in b_cards) % 10
    if ps < 8 and bs < 8:
        if ps <= 5: p_cards.append(deck.pop()); ps = sum(c['score'] for c in p_cards) % 10
        if bs <= 5: b_cards.append(deck.pop()); bs = sum(c['score'] for c in b_cards) % 10

    win = "플" if ps > bs else "뱅" if bs > ps else "타"
    win_symbol = "🔴" if win=="플" else "🔵" if win=="뱅" else "🟢"
    db["history"].append(win_symbol)
    if len(db["history"]) > 50: db["history"].pop(0)

    # 당첨금 정산 (비밀 금고 연동)
    for bet in room['bets']:
        u = db["users"][str(bet['uid'])]
        if bet['type'] == win:
            rate = 2.0 if win=="플" else 1.95 if win=="뱅" else 8.0
            prize = int(bet['amt'] * rate)
            u['money'] += prize
            db['vault'] -= (prize - bet['amt'])
        else:
            db['vault'] += bet['amt']

    # 연출: 격자판 -> 텍스트 결과 -> 카드 앨범
    await context.bot.send_photo(chat_id, photo=BASE_URL+"grid.png", caption=f"🏆 결과: {win_symbol} {win} 승리!\n플레이어 {ps} : 뱅커 {bs}")
    await asyncio.sleep(1)
    
    await context.bot.send_media_group(chat_id, [InputMediaPhoto(BASE_URL + c['file']) for c in p_cards])
    await asyncio.sleep(0.5)
    await context.bot.send_media_group(chat_id, [InputMediaPhoto(BASE_URL + c['file']) for c in b_cards])
    
    room.update({"status": "IDLE", "bets": []})
    save_db()

# =========================
# 🛠 3. 명령어 처리기
# =========================
async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    if not (msg and msg.startswith(".")): return
    
    uid, uname, chat_id = str(update.effective_user.id), update.effective_user.first_name, update.effective_chat.id
    if uid not in db["users"]:
        db["users"][uid] = {"name": uname, "money": 0, "inv": {}, "pickaxe": {"name": "우드", "dur": 100}, "joined": False}
    u = db["users"][uid]

    # [명령어 목록]
    if msg == ".명령어":
        text = "👤 일반: .가입 .내정보 .출석 .송금 .랭킹\n⛏ 채광: .채광 .인벤 .판매 .상점\n🎰 게임: .바카라 .플/뱅/타 [금액]"
        await update.message.reply_text(text)

    # [경제 시스템]
    elif msg == ".가입":
        if u["joined"]: await update.message.reply_text("이미 가입된 계정입니다.")
        else:
            u.update({"joined": True, "money": 1000000, "join_date": str(date.today())})
            await update.message.reply_text("🎉 가입 완료! 100만 G코인이 지급되었습니다.")

    elif msg == ".출석":
        today = str(date.today())
        if u.get("last_attend") == today: await update.message.reply_text("오늘 이미 출석하셨습니다.")
        else:
            u["money"] += 50000; u["last_attend"] = today
            await update.message.reply_text("✅ 출석 완료! 5만 G코인 지급.")

    elif msg == ".내정보":
        await update.message.reply_text(f"👤 {u['name']}\n💰 {u['money']:,} G코인\n⛏ {u['pickaxe']['name']}({u['pickaxe']['dur']})\n📅 {u.get('join_date','-')}")

    # [채광 시스템]
    elif msg == ".채광":
        if u["pickaxe"]["dur"] <= 0: return await update.message.reply_text("곡괭이 파손! 상점에서 구매하세요.")
        u["pickaxe"]["dur"] -= 1
        tier = random.choice(list(MINERALS.keys()))
        item = random.choice(list(MINERALS[tier].keys()))
        u["inv"][item] = u["inv"].get(item, 0) + 1
        await update.message.reply_text(f"⛏ {tier} [{item}] 획득! (내구도: {u['pickaxe']['dur']})")

    elif msg == ".인벤":
        txt = "📦 인벤토리\n"; total = 0
        for k, v in u["inv"].items():
            price = next((MINERALS[t][k] for t in MINERALS if k in MINERALS[t]), 0)
            txt += f"{k} x{v} ({price*v:,}원)\n"; total += price * v
        await update.message.reply_text(f"{txt}\n💰 총 가치: {total:,}원")

    elif msg == ".판매":
        total = 0
        for k, v in u["inv"].items():
            total += next((MINERALS[t][k] for t in MINERALS if k in MINERALS[t]), 0) * v
        u["inv"], u["money"] = {}, u["money"] + total
        await update.message.reply_text(f"💰 판매 완료! +{total:,} G코인")

    # [바카라 베팅]
    elif msg.startswith((".플 ", ".뱅 ", ".타이 ")):
        try:
            amt = int(msg.split()[1])
            b_type = "플" if ".플" in msg else "뱅" if ".뱅" in msg else "타"
            if u["money"] < amt: return await update.message.reply_text("잔액 부족")
            u["money"] -= amt
            if chat_id not in rooms or rooms[chat_id]['status'] == "IDLE":
                rooms[chat_id] = {"status": "BETTING", "bets": [], "round": len(db["history"])+1}
                await update.message.reply_text(f"📢 {rooms[chat_id]['round']}회차 베팅 시작! (30초)")
                asyncio.create_task(baccarat_logic(chat_id, context))
            rooms[chat_id]['bets'].append({"uid": uid, "type": b_type, "amt": amt})
            await update.message.reply_text(f"✅ {b_type} {amt:,} 베팅 완료!")
        except: pass

    elif msg == ".바카라":
        grid = ""; 
        for i, res in enumerate(db["history"]):
            grid += res + " "
            if (i+1)%5==0: grid+="\n"
        await update.message.reply_text(f"📊 **실시간 바카라 전적판**\n\n{grid if grid else '기록 없음'}", parse_mode='Markdown')

    # [관리자 명령어]
    elif msg == ".금고" and int(uid) == ADMIN_ID:
        await update.message.reply_text(f"🏦 금고 잔액: {db['vault']:,}원")

    save_db()

# [상점 버튼 처리]
async def btn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = str(q.from_user.id); data = q.data
    if data.startswith("p_"):
        name = data.split("_")[1]; price, dur = PICKAXE[name]
        if db["users"][uid]["money"] < price: return await q.edit_message_text("돈 부족")
        db["users"][uid]["money"] -= price
        db["users"][uid]["pickaxe"] = {"name": name, "dur": dur}
        save_db(); await q.edit_message_text(f"⛏ {name} 곡괭이 장착 완료!")

# =========================
# 🚀 4. 실행
# =========================
load_db()
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), main_handler))
app.add_handler(CallbackQueryHandler(btn_handler))
print("봇 가동 시작 (관리자 금고 5,000억)")
app.run_polling()
