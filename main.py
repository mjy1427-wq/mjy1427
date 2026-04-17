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
    port = int(os.environ.get("PORT", 10000)) # Render 포트 맞춤
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web); t.daemon = True; t.start()

# ================= 🔐 [1] 설정 및 데이터베이스 =================
BOT_TOKEN = "8484299407:AAGAS9cPCyS7vrrqRS0lePwGFptk4lyC4u4" 
ADMIN_ID = 7476630349 
NOTICE_CHANNEL = "https://t.me/GCOIN7777"
CS_LINK = "https://t.me/GCOINZ_BOT" 

BASE_URL = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/"
DB_FILE = "casino_data.json"

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

# ================= 🃏 [2] 바카라 엔진 (수수료 5% & 금고 연동) =================
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

    if cid not in db["active_rooms"]: db["active_rooms"].append(cid)

    # [관리자 답장 모드]
    if uid == ADMIN_ID and uid in pending_replies:
        target_id = pending_replies[uid]
        await context.bot.send_message(chat_id=target_id, text=f"📞 <b>상담 답변이 도착했습니다:</b>\n\n{msg}", parse_mode='HTML')
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

    # [상담 전달] 일반 채팅
    if not msg.startswith("."):
        if uid == ADMIN_ID: return
        kb = [[InlineKeyboardButton("✉️ 답변하기", callback_data=f"reply_{uid}")]]
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"🔴 <b>새 상담 요청</b>\n유저: {u['name']}\nID: <code>{uid}</code>\n내용: {msg}", reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')
        await update.message.reply_text("✅ 관리자에게 문의가 전달되었습니다.")
        return

    # --- 명령어 ---
    if msg == ".내정보":
        kb = [[InlineKeyboardButton("📢 공지채널", url=NOTICE_CHANNEL), InlineKeyboardButton("💬 상담하기", url=CS_LINK)]]
        await update.message.reply_text(f"👤 <b>이름:</b> {u['name']}\n🆔 <b>아이디:</b> <code>{uid}</code>\n💰 <b>G코인:</b> {u['money']:,} G\n\n📅 <b>가입일자:</b> {u['join_date']}\n⏰ <b>가입시간:</b> {u['join_time']}", reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')

    elif msg == ".채광":
        now_ts = time.time()
        if now_ts - mine_cooldowns.get(str(uid), 0) < 40: return await update.message.reply_text("⏳ 40초 대기 중...")
        if u["durability"] <= 0: return await update.message.reply_text("❌ 내구도 부족! .수리 가 필요합니다.")
        mine_cooldowns[str(uid)] = now_ts; u["durability"] -= 1
        tier = random.choices(list(MINERALS.keys()), weights=[1, 5, 14, 30, 50])[0]
        m_name = random.choice(list(MINERALS[tier].keys())); m_price = MINERALS[tier][m_name]
        u["inv"][m_name] = u["inv"].get(m_name, 0) + 1
        await update.message.reply_text(f"⛏ <b>채광 완료!</b>\n\n💎 <b>광물이름:</b> {m_name}\n💵 <b>광물가격:</b> {m_price:,} G\n🛠 <b>착용곡괭이:</b> {u['pickaxe_name']}\n🔋 <b>내구도:</b> {u['durability']} / {u['max_durability']}", parse_mode='HTML')

    elif msg == ".판매":
        kb = [[InlineKeyboardButton("💎 1티어", callback_data="sell_1"), InlineKeyboardButton("✨ 2티어", callback_data="sell_2")],
              [InlineKeyboardButton("📀 3티어", callback_data="sell_3"), InlineKeyboardButton("🥈 4티어", callback_data="sell_4")],
              [InlineKeyboardButton("🪵 5티어", callback_data="sell_5"), InlineKeyboardButton("💰 전체 판매", callback_data="sell_all")]]
        await update.message.reply_text("💰 <b>판매 티어를 선택하세요.</b>", reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')

    elif msg == ".랭킹":
        top = sorted(db["users"].items(), key=lambda x: x[1]['money'], reverse=True)[:10]
        text = "🏆 <b>G코인 보유 랭킹 (TOP 10)</b>\n\n"
        for i, (id, data) in enumerate(top, 1): text += f"{i}위. <b>{data['name']}</b> | {data['money']:,} G\n"
        await update.message.reply_text(text, parse_mode='HTML')

    elif msg.startswith(".송금"):
        try:
            _, tid, amt = msg.split(); amt = int(amt)
            if u["money"] < amt or tid == str(uid): return await update.message.reply_text("❌ 송금 불가")
            fee = int(amt * 0.08); net = amt - fee
            if tid in db["users"]:
                u["money"] -= amt; db["users"][tid]["money"] += net; db["vault"] += fee
                await update.message.reply_text(f"✅ <b>송금 완료</b>\n👤 대상: {db['users'][tid]['name']}\n💵 금액: {net:,} G\n💸 수수료(8%): {fee:,} G")
            else: await update.message.reply_text("❌ 유저 없음")
        except: await update.message.reply_text(".송금 아이디 금액")

    elif msg == ".바카라":
        hist = "".join([f"{h} " + ("\n" if (i+1)%9==0 else "") for i, h in enumerate(db["history"][-45:])])
        await update.message.reply_photo(photo=BASE_URL+"grid.png.JPG", caption=f"📊 <b>전적 리스트</b>\n{hist}", parse_mode='HTML')

    elif msg.startswith((".플", ".뱅", ".타이")):
        try:
            amt = int(msg.split()[1])
            if u["money"] < amt: return await update.message.reply_text("❌ 잔액 부족")
            u["money"] -= amt
            res, sym = get_baccarat_result()
            db["history"].append(sym)
            if len(db["history"]) > 45: db["history"].pop(0)
            
            # 관리자 비밀 예고
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"📢 <b>다음 결과:</b> {sym} {res}")
            
            win = (msg.startswith(".플") and res == "플") or (msg.startswith(".뱅") and res == "뱅") or (msg.startswith(".타이") and res == "타이")
            if win:
                rate = 8.0 if res == "타이" else 1.95 if res == "뱅" else 2.0
                win_amt = int(amt * rate)
                u["money"] += win_amt
                db["vault"] -= (win_amt - amt) # 당첨금 금고 차감
                await update.message.reply_text(f"🎊 <b>승리! {sym} {res}</b>\n💰 당첨금: {win_amt:,} G")
            else:
                db["vault"] += amt # 패배금 금고 입금
                await update.message.reply_text(f"💀 <b>패배... {sym} {res}</b>")
        except: await update.message.reply_text(".플 금액")

    # --- 관리자 전용 ---
    elif uid == ADMIN_ID:
        if msg.startswith(".지급"):
            try:
                a = int(msg.split()[1])
                if db["vault"] >= a: db["vault"] -= a; u["money"] += a; await update.message.reply_text(f"✅ {a:,} G 지급 완료")
            except: pass
        elif msg == ".금고": await update.message.reply_text(f"🏦 <b>금고 잔액:</b> {db['vault']:,} G")
        elif msg == ".현황": await update.message.reply_text(f"📊 <b>현황</b>\n👥 유저: {len(db['users'])}명\n🌐 방: {len(db['active_rooms'])}개")

    save_db()

# ================= 🖱 [4] 콜백 핸들러 =================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); u = db["users"].get(uid); data = query.data
    await query.answer()

    if data.startswith("sell_"):
        t_num = data.split("_")[1]; gain = 0
        for t_name, mins in MINERALS.items():
            if t_num == "all" or t_num in t_name:
                for m, p in mins.items():
                    c = u["inv"].get(m, 0); gain += (p * c); u["inv"][m] = 0
        if gain > 0: u["money"] += gain; await query.edit_message_text(f"✅ <b>판매 완료!</b>\n💵 정산: {gain:,} G\n💰 잔액: {u['money']:,} G", parse_mode='HTML')
    elif data.startswith("reply_") and int(uid) == ADMIN_ID:
        pending_replies[ADMIN_ID] = int(data.split("_")[1])
        await query.message.reply_text("✍️ 답장을 입력하세요.")
    save_db()

def main():
    keep_alive()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), main_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()

if __name__ == "__main__": main()
