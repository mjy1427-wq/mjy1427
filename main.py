import random
import json
import asyncio
import os
import time
from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ================= 🔐 [1] 설정 및 데이터베이스 =================
BOT_TOKEN = "8484299407:AAHJZfme3lYEoPAwAWie9ksgQGzYB8QlH8I"
ADMIN_ID = 7476630349 
NOTICE_CHANNEL = "https://t.me/GCOIN7777"
CS_LINK = "https://t.me/GCOINZBOT" 

# GitHub 이미지 및 데이터 파일 경로
BASE_URL = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/"
DB_FILE = "casino_data.json"

# 초기 데이터: 금고 1,000억 G코인 설정
db = {"users": {}, "vault": 100000000000, "history": []}
mine_cooldowns = {}

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

# 광물 정보 및 시세
MINERALS = {
    "1티어": {"아다만티움": 5000000, "오리하르콘": 3000000, "다이아몬드": 2000000},
    "2티어": {"미스릴": 1000000, "흑요석": 700000},
    "3티어": {"백금": 400000, "금": 250000, "티타늄": 180000},
    "4티어": {"은": 100000, "비취": 50000, "황동": 30000},
    "5티어": {"철": 25000, "구리": 15000, "석탄": 10000}
}

# ================= 🃏 [2] 바카라 엔진 (비밀 정산 및 격자판 연출) =================
rooms = {}

def get_deck():
    suits = ['spades', 'hearts', 'diamonds', 'clubs']
    ranks = [('ace',1),('2',2),('3',3),('4',4),('5',5),('6',6),('7',7),('8',8),('9',9),('10',0),('jack',0),('queen',0),('king',0)]
    return [{'file': f"{r[0]}_of_{s}.png", 'score': r[1]} for s in suits for r in ranks]

async def baccarat_logic(chat_id, context):
    room = rooms[chat_id]
    round_num = room['round']
    await asyncio.sleep(30) # 베팅 대기 시간
    
    await context.bot.send_message(chat_id, f"**{round_num}회차 베팅 마감!** (카드 공개 중...)")
    await asyncio.sleep(3)
    
    deck = get_deck(); random.shuffle(deck)
    p_cards, b_cards = [deck.pop(), deck.pop()], [deck.pop(), deck.pop()]
    
    # [연출] 초기 카드 2장씩 앨범 형태로 공개
    await context.bot.send_media_group(chat_id, [InputMediaPhoto(BASE_URL + c['file']) for c in p_cards])
    await asyncio.sleep(1.5)
    await context.bot.send_media_group(chat_id, [InputMediaPhoto(BASE_URL + c['file']) for c in b_cards])
    await asyncio.sleep(2)

    ps, bs = sum(c['score'] for c in p_cards) % 10, sum(c['score'] for c in b_cards) % 10
    
    # 바카라 3rd 카드 룰 적용 및 추가 카드 공개
    if ps < 8 and bs < 8:
        if ps <= 5:
            p3 = deck.pop(); p_cards.append(p3)
            await context.bot.send_photo(chat_id, BASE_URL + p3['file'], caption="➕ 플레이어 추가 카드")
            ps = sum(c['score'] for c in p_cards) % 10
            await asyncio.sleep(1.5)
        if bs <= 5:
            b3 = deck.pop(); b_cards.append(b3)
            await context.bot.send_photo(chat_id, BASE_URL + b3['file'], caption="➕ 뱅커 추가 카드")
            bs = sum(c['score'] for c in b_cards) % 10
            await asyncio.sleep(1.5)

    win = "플" if ps > bs else "뱅" if bs > ps else "타"
    win_symbol = "🔴" if win=="플" else "🔵" if win=="뱅" else "🟢"
    db["history"].append(win_symbol)
    if len(db["history"]) > 60: db["history"].pop(0)

    # 🤫 [비밀 정산 로직] 유저 몰래 금고와 동기화
    for bet in room['bets']:
        u = db["users"].get(str(bet['uid']))
        if u:
            if bet['type'] == win:
                # 당첨 시: 금고 차감 후 유저 잔액 합산 (뱅커는 수수료 5% 제외 1.95배)
                rate = 1.95 if win=="뱅" else 2.0 if win=="플" else 8.0
                win_amt = int(bet['amt'] * rate)
                u['money'] += win_amt
                db['vault'] -= (win_amt - bet['amt'])
            else:
                # 패배 시: 유저 베팅금 즉시 금고로 전송 (이미 베팅 시 차감되었으므로 금고 수치만 올림)
                db['vault'] += bet['amt']

    # 최종 결과 발표 (격자판 이미지 배경 사용)
    await context.bot.send_photo(chat_id, photo=BASE_URL+"grid.png.JPG", 
                                 caption=f"🏆 **{round_num}회차 결과: {win_symbol} {win} 승리!**\n\n플레이어 **{ps}** : 뱅커 **{bs}**", parse_mode='Markdown')
    rooms[chat_id] = {"status": "IDLE", "bets": []}
    save_db()

# ================= 🛠 [3] 메인 핸들러 (명령어 및 상담 통합) =================
async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    msg, uid, chat_id = update.message.text, str(update.effective_user.id), update.effective_chat.id
    uname = update.effective_user.first_name

    if uid not in db["users"]:
        db["users"][uid] = {"name": uname, "money": 0, "inv": {}, "mine_count": 0, "joined": False}
    u = db["users"][uid]

    # 관리자 답장 (Reply 기능)
    if int(uid) == ADMIN_ID and update.message.reply_to_message:
        try:
            target_id = int(update.message.reply_to_message.text.split("유저ID: ")[1].split("\n")[0])
            await context.bot.send_message(chat_id=target_id, text=f"💬 **관리자 답변**\n\n{msg}")
            return await update.message.reply_text("✅ 답변 전송 완료")
        except: pass

    # --- 명령어 분기 ---
    if msg == ".가입":
        if u.get("joined"): return await update.message.reply_text("❌ 이미 가입된 계정입니다.")
        u.update({"joined": True, "money": 100000, "join_date": str(date.today())})
        await update.message.reply_text("🎉 가입 완료! 10만 G코인이 지급되었습니다.")

    elif msg == ".출석":
        if u.get("last_attend") == str(date.today()): return await update.message.reply_text("❌ 오늘 이미 출석하셨습니다.")
        u["money"] += 50000; u["last_attend"] = str(date.today())
        await update.message.reply_text("✅ 출석 완료! (+50,000 G코인)")

    elif msg == ".내정보":
        kb = [[InlineKeyboardButton("📢 공지채널", url=NOTICE_CHANNEL), InlineKeyboardButton("💬 1:1 상담", url=CS_LINK)]]
        await update.message.reply_text(f"**[ 내 정보 ]**\n💰 잔액: {u['money']:,} G코인\n⛏ 채광: {u['mine_count']:,}회\n🆔 ID: `{uid}`", 
                                         reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

    elif msg == ".채광":
        if not u["joined"]: return await update.message.reply_text("❌ 가입 먼저 해주세요.")
        now = time.time()
        if now - mine_cooldowns.get(uid, 0) < 40:
            return await update.message.reply_text(f"⏳ 쿨타임! {int(40-(now-mine_cooldowns[uid]))}초 대기")
        
        mine_cooldowns[uid] = now
        tier = random.choices(list(MINERALS.keys()), weights=[1, 5, 14, 30, 50])[0]
        name = random.choice(list(MINERALS[tier].keys()))
        u["inv"][name] = u["inv"].get(name, 0) + 1; u["mine_count"] += 1
        await update.message.reply_text(f"⛏ **채광 성공!**\n[{tier}] **{name}** 획득! (40초 후 다시 가능)")

    elif msg == ".인벤":
        items = [f"• {k} x{v}" for k, v in u["inv"].items() if v > 0]
        await update.message.reply_text("🎒 **인벤토리**\n" + ("\n".join(items) if items else "비어있음"), parse_mode='Markdown')

    elif msg == ".바카라":
        # 격자판 이미지와 함께 텍스트 히스토리 출력
        hist = "".join([f"{h} " + ("\n" if (i+1)%10==0 else "") for i, h in enumerate(db["history"][-60:])])
        await update.message.reply_photo(photo=BASE_URL+"grid.png.JPG", caption=f"📊 **최근 격자판 전적**\n━━━━━━━━━━\n{hist}\n━━━━━━━━━━", parse_mode='Markdown')

    elif msg.startswith((".플 ", ".뱅 ", ".타이 ")):
        try:
            amt = int(msg.split()[1]); b_type = "플" if ".플" in msg else "뱅" if ".뱅" in msg else "타"
            if u["money"] < amt: return await update.message.reply_text("❌ 잔액 부족")
            u["money"] -= amt # 베팅금 즉시 차감
            if chat_id not in rooms or rooms[chat_id]['status'] == "IDLE":
                rooms[chat_id] = {"status": "BETTING", "bets": [], "round": len(db["history"])+1}
                asyncio.create_task(baccarat_logic(chat_id, context))
            rooms[chat_id]['bets'].append({"uid": uid, "type": b_type, "amt": amt})
            await update.message.reply_text(f"✅ 베팅 완료: {b_type} ({amt:,} G코인)")
        except: pass

    elif msg.startswith(".송금 "):
        try:
            _, tid, tamt = msg.split(); tamt = int(tamt)
            if u["money"] >= tamt > 0 and tid in db["users"]:
                u["money"] -= tamt; db["users"][tid]["money"] += tamt
                await update.message.reply_text(f"✅ {db['users'][tid]['name']}님께 {tamt:,} G코인 전송 완료")
        except: pass

    elif msg == ".랭킹":
        top = sorted(db["users"].items(), key=lambda x: x[1]['money'], reverse=True)[:10]
        res = "🏆 **G코인 부자 랭킹**\n" + "\n".join([f"{i+1}. {v['name']}: {v['money']:,} G" for i, (k, v) in enumerate(top)])
        await update.message.reply_text(res, parse_mode='Markdown')

    # --- 관리자 기능 ---
    elif int(uid) == ADMIN_ID:
        if msg == ".금고":
            await update.message.reply_text(f"🏦 **금고 잔액**: {db['vault']:,} G코인\n(수수료 수익 누적 포함)")
        elif msg.startswith(".지급 "):
            try:
                _, tid, tamt = msg.split(); db["users"][tid]["money"] += int(tamt)
                await update.message.reply_text(f"✅ {tid} 유저에게 {int(tamt):,} G 지급 완료")
            except: pass

    # --- 상담 전달 ---
    elif not msg.startswith("."):
        if int(uid) == ADMIN_ID: return
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"📩 **상담 요청**\n👤 유저ID: {uid}\n💬 내용: {msg}")
        await update.message.reply_text("✅ 관리자에게 전달되었습니다. 잠시만 기다려주세요.")

    save_db()

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), main_handler))
    print("🚀 G-COIN 통합 시스템(Secret 정산 버전) 구동 중...")
    app.run_polling()

if __name__ == "__main__":
    main()
