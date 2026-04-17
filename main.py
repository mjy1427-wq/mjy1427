import random
import json
import asyncio
import os
import time
from datetime import datetime
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ================= 🌐 [0] 웹 서버 (Render 유지용) =================
app = Flask('')
@app.route('/')
def home(): return "G-COIN Bot Running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web); t.daemon = True; t.start()

# ================= 🔐 [1] 설정 및 데이터베이스 =================
BOT_TOKEN = "8484299407:AAFe6uAoKOhYQJmb_Fdh-oraYEtDhJd4cNw" 
ADMIN_ID = 7476630349 
NOTICE_CHANNEL = "https://t.me/GCOIN7777"
CS_LINK = "https://t.me/GCOINZ_BOT" 

BASE_URL = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/"
DB_FILE = "casino_data.json"

# 초기 DB 구조: 금고와 방 목록 추가
db = {"users": {}, "vault": 500000000000, "history": [], "active_rooms": []}
mine_cooldowns = {}
pending_replies = {} 

SHOP_ITEMS = {
    "Onyx": {"price": 1000000, "durability": 100, "repair": 200000},
    "Sapphire": {"price": 5000000, "durability": 300, "repair": 1000000},
    "Topaz": {"price": 15000000, "durability": 500, "repair": 3000000},
    "Emerald": {"price": 50000000, "durability": 1000, "repair": 10000000},
    "Ruby": {"price": 250000000, "durability": 5000, "repair": 50000000},
    "Opal": {"price": 1000000000, "durability": 10000, "repair": 200000000},
    "Diamond": {"price": 2000000000, "durability": 25000, "repair": 400000000}
}

MINERALS = {
    "1티어": {"아다만티움": 5000000, "오리하르콘": 3000000, "다이아몬드": 2000000},
    "2티어": {"미스릴": 1000000, "흑요석": 700000},
    "3티어": {"백금": 400000, "금": 250000, "티타늄": 180000},
    "4티어": {"은": 100000, "비취": 50000, "황동": 30000},
    "5티어": {"철": 25000, "구리": 15000, "석탄": 10000}
}

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                db.update(json.load(f))
        except: pass

load_db()

# ================= 🃏 [2] 바카라 엔진 (금고 정산 포함) =================
def get_baccarat_result():
    p_score = (random.randint(1, 9) + random.randint(1, 9)) % 10
    b_score = (random.randint(1, 9) + random.randint(1, 9)) % 10
    if p_score <= 5: p_score = (p_score + random.randint(1, 9)) % 10
    if b_score <= 5: b_score = (b_score + random.randint(1, 9)) % 10
    
    if p_score > b_score: return "플", "🔴"
    elif b_score > p_score: return "뱅", "🔵"
    else: return "타이", "🟢"

# ================= 🛠 [3] 메인 핸들러 =================
async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    msg, uid, cid = update.message.text, update.effective_user.id, update.effective_chat.id
    u = db["users"].get(str(uid))

    # 현황 파악을 위한 방 기록
    if cid not in db["active_rooms"]:
        db["active_rooms"].append(cid)

    # [관리자 답장 모드]
    if uid == ADMIN_ID and uid in pending_replies:
        target_id = pending_replies[uid]
        await context.bot.send_message(chat_id=target_id, text=f"📞 <b>상담 답변:</b>\n\n{msg}", parse_mode='HTML')
        await update.message.reply_text("✅ 답변 전달 완료.")
        del pending_replies[uid]
        return

    if not u:
        now = datetime.now()
        db["users"][str(uid)] = {
            "name": update.effective_user.first_name, "money": 100000, "inv": {}, "last_check": "",
            "durability": 100, "max_durability": 100, "pickaxe_name": "Onyx",
            "joined": True, "join_date": now.strftime("%Y-%m-%d"), "join_time": now.strftime("%H:%M:%S")
        }
        u = db["users"][str(uid)]

    # [상담 전달] 일반 채팅 -> 관리자
    if not msg.startswith("."):
        if uid == ADMIN_ID: return
        kb = [[InlineKeyboardButton("✉️ 답변하기", callback_data=f"reply_{uid}")]]
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"🔴 <b>상담 요청</b>\n유저: {u['name']}\nID: <code>{uid}</code>\n내용: {msg}", reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')
        await update.message.reply_text("✅ 문의가 전달되었습니다.")
        return

    # --- 명령어 분기 ---
    if msg == ".내정보":
        kb = [[InlineKeyboardButton("📢 공지채널", url=NOTICE_CHANNEL), InlineKeyboardButton("💬 상담하기", url=CS_LINK)]]
        text = (f"👤 <b>이름:</b> {u['name']}\n🆔 <b>아이디:</b> <code>{uid}</code>\n"
                f"💰 <b>G코인:</b> {u['money']:,} G\n\n"
                f"📅 <b>가입일자:</b> {u['join_date']}\n⏰ <b>가입시간:</b> {u['join_time']}")
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')

    elif msg == ".채광":
        now_ts = time.time()
        if now_ts - mine_cooldowns.get(str(uid), 0) < 40: return await update.message.reply_text("⏳ 40초 대기 중...")
        if u["durability"] <= 0: return await update.message.reply_text("❌ 내구도 부족! .수리 가 필요합니다.")
        mine_cooldowns[str(uid)] = now_ts; u["durability"] -= 1
        tier = random.choices(list(MINERALS.keys()), weights=[1, 5, 14, 30, 50])[0]
        m_name = random.choice(list(MINERALS[tier].keys())); m_price = MINERALS[tier][m_name]
        u["inv"][m_name] = u["inv"].get(m_name, 0) + 1
        await update.message.reply_text(f"⛏ <b>광물획득!</b>\n\n💎 <b>명칭:</b> {m_name}\n💵 <b>가격:</b> {m_price:,} G\n🛠 <b>곡괭이:</b> {u['pickaxe_name']}\n🔋 <b>내구도:</b> {u['durability']} / {u['max_durability']}", parse_mode='HTML')

    elif msg == ".판매":
        text = "💰 <b>광물 판매 시스템</b>"
        kb = [
            [InlineKeyboardButton("💎 1티어", callback_data="sell_1"), InlineKeyboardButton("✨ 2티어", callback_data="sell_2")],
            [InlineKeyboardButton("📀 3티어", callback_data="sell_3"), InlineKeyboardButton("🥈 4티어", callback_data="sell_4")],
            [InlineKeyboardButton("🪵 5티어", callback_data="sell_5"), InlineKeyboardButton("💰 전체 판매", callback_data="sell_all")]
        ]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')

    elif msg == ".랭킹":
        sorted_users = sorted(db["users"].items(), key=lambda x: x[1]['money'], reverse=True)[:10]
        rank_text = "🏆 <b>G코인 보유 랭킹 (TOP 10)</b>\n\n"
        for i, (userid, userdata) in enumerate(sorted_users, 1):
            rank_text += f"{i}위. <b>{userdata['name']}</b> | {userdata['money']:,} G\n"
        await update.message.reply_text(rank_text, parse_mode='HTML')

    elif msg.startswith(".송금"):
        try:
            _, target_id, amount = msg.split()
            amount = int(amount)
            if u["money"] < amount: return await update.message.reply_text("❌ 잔액이 부족합니다.")
            if target_id == str(uid): return await update.message.reply_text("❌ 본인에게 송금할 수 없습니다.")
            
            fee = int(amount * 0.08)
            net_amount = amount - fee
            if str(target_id) in db["users"]:
                u["money"] -= amount
                db["users"][str(target_id)]["money"] += net_amount
                db["vault"] += fee # 수수료 금고 입금
                await update.message.reply_text(f"✅ <b>송금 완료</b>\n\n👤 대상: {db['users'][str(target_id)]['name']}\n💵 금액: {net_amount:,} G\n💸 수수료(8%): {fee:,} G")
            else: await update.message.reply_text("❌ 존재하지 않는 유저 ID입니다.")
        except: await update.message.reply_text("형식: .송금 아이디 금액")

    elif msg.startswith((".플", ".뱅", ".타이")):
        try:
            bet_amt = int(msg.split()[1])
            if u["money"] < bet_amt: return await update.message.reply_text("❌ 잔액 부족")
            u["money"] -= bet_amt
            res, sym = get_baccarat_result()
            
            # 결과 기록 및 예고 (관리자)
            db["history"].append(sym)
            if len(db["history"]) > 45: db["history"].pop(0)
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"📢 <b>바카라 예고:</b> {sym} {res}")
            
            is_win = (msg.startswith(".플") and res == "플") or (msg.startswith(".뱅") and res == "뱅") or (msg.startswith(".타이") and res == "타이")
            
            if is_win:
                rate = 8.0 if res == "타이" else 1.95 if res == "뱅" else 2.0
                win_money = int(bet_amt * rate)
                u["money"] += win_money
                # 뱅커 승리 수수료 및 금고 차액 정산 (보이지 않게)
                db["vault"] -= (win_money - bet_amt)
                await update.message.reply_text(f"🎊 <b>승리! {sym} {res}</b>\n💰 당첨금: {win_money:,} G")
            else:
                db["vault"] += bet_amt # 실패 금액 금고 입금
                await update.message.reply_text(f"💀 <b>패배... {sym} {res}</b>\n💸 손실액: {bet_amt:,} G")
        except: await update.message.reply_text("형식: .플 금액")

    # --- 관리자 전용 명령어 ---
    elif uid == ADMIN_ID:
        if msg.startswith(".지급"):
            try:
                amt = int(msg.split()[1])
                if db["vault"] >= amt:
                    db["vault"] -= amt
                    u["money"] += amt
                    await update.message.reply_text(f"✅ 금고에서 {amt:,} G를 인출하여 본인에게 지급했습니다.")
                else: await update.message.reply_text("❌ 금고 잔액이 부족합니다.")
            except: pass
        elif msg == ".금고":
            await update.message.reply_text(f"🏦 <b>현재 금고 잔액:</b> {db['vault']:,} G")
        elif msg == ".현황":
            user_count = len(db["users"])
            room_count = len(db["active_rooms"])
            await update.message.reply_text(f"📊 <b>봇 이용 현황</b>\n\n👥 전체 유저: {user_count}명\n🌐 활성화된 방: {room_count}개")

    save_db()

# ================= 🖱 [4] 콜백 핸들러 =================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); u = db["users"].get(uid); data = query.data
    await query.answer()

    if data.startswith("sell_"):
        tier = data.split("_")[1]
        gain = 0
        for t_name, minerals in MINERALS.items():
            if tier == "all" or tier in t_name:
                for m_name, m_price in minerals.items():
                    cnt = u["inv"].get(m_name, 0)
                    if cnt > 0:
                        gain += (m_price * cnt); u["inv"][m_name] = 0
        if gain > 0:
            u["money"] += gain
            await query.edit_message_text(f"✅ <b>판매 완료!</b>\n💵 정산금액: {gain:,} G\n💰 현재잔액: {u['money']:,} G")
        else: await query.answer("❌ 판매할 광물이 없습니다.")
    
    elif data.startswith("reply_") and int(uid) == ADMIN_ID:
        pending_replies[ADMIN_ID] = int(data.split("_")[1])
        await query.message.reply_text("✍️ 답장 내용을 입력하세요.")
    save_db()

def main():
    keep_alive()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), main_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()

if __name__ == "__main__": main()
