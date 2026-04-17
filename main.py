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

# ================= [0] 웹 서버 (Render 유지용) =================
app = Flask('')
@app.route('/')
def home(): return "G-COIN Bot Running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web); t.daemon = True; t.start()

# ================= [1] 설정 및 데이터베이스 =================
BOT_TOKEN = "8484299407:AAFSYTBzMJKQdl3Osq5JWjSfhVe2I1zz6XY" 
ADMIN_ID = 7476630349 
BASE_URL = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/"
DB_FILE = "casino_data.json"

# 채널 링크 설정
NOTICE_CHANNEL = "https://t.me/your_notice_channel"
SUPPORT_CHANNEL = "https://t.me/your_support_channel"

db = {"users": {}, "vault": 500000000000, "history": [], "game_count": 1, "next_result": None}
mine_cooldowns = {}
room_betting_status = {}

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

# ================= [2] 엔진 및 연출 로직 =================
def get_baccarat_result():
    suits = ["h", "d", "c", "s"]
    p_cards = [{'val': random.randint(1, 13), 'suit': random.choice(suits)} for _ in range(2)]
    b_cards = [{'val': random.randint(1, 13), 'suit': random.choice(suits)} for _ in range(2)]
    p_s = sum([c['val'] if c['val'] < 10 else 0 for c in p_cards]) % 10
    b_s = sum([c['val'] if c['val'] < 10 else 0 for c in b_cards]) % 10
    if p_s <= 5:
        nc = {'val': random.randint(1, 13), 'suit': random.choice(suits)}; p_cards.append(nc)
        p_s = (p_s + (nc['val'] if nc['val'] < 10 else 0)) % 10
    if b_s <= 5:
        nc = {'val': random.randint(1, 13), 'suit': random.choice(suits)}; b_cards.append(nc)
        b_s = (b_s + (nc['val'] if nc['val'] < 10 else 0)) % 10
    res_name = "타이" if p_s == b_s else "플레이어" if p_s > b_s else "뱅커"
    sym = "🟢" if p_s == b_s else "🔴" if p_s > b_s else "🔵"
    return {"name": res_name, "sym": sym, "p_cards": p_cards, "b_cards": b_cards, "p_score": p_s, "b_score": b_s}

if not db.get("next_result"): db["next_result"] = get_baccarat_result()

def get_roadmap(history):
    recent = history[-45:]; grid = [["⬜" for _ in range(9)] for _ in range(5)]
    for i, res in enumerate(recent): grid[i % 5][i // 5] = res
    txt = "📊 <b>바카라 로드맵 (9x5)</b>\n"
    for r in grid: txt += "".join(r) + "\n"
    return txt

async def play_card_animation(context, cid, res, user_name, win_amt, is_win):
    suit_map = {"h": "hearts", "d": "diamonds", "c": "clubs", "s": "spades"}
    for c in res["p_cards"]:
        await context.bot.send_photo(cid, f"{BASE_URL}{c['val']}_of_{suit_map[c['suit']]}.png")
    await context.bot.send_message(cid, "<b>플레이어 카드 공개!</b>", parse_mode='HTML')
    await asyncio.sleep(1)
    for c in res["b_cards"]:
        await context.bot.send_photo(cid, f"{BASE_URL}{c['val']}_of_{suit_map[c['suit']]}.png")
    await context.bot.send_message(cid, "<b>뱅커 카드 공개!</b>", parse_mode='HTML')
    await asyncio.sleep(1)
    
    banner = "player_win.png" if res['name'] == "플레이어" else "banker_win.png" if res['name'] == "뱅커" else "tie_win.png"
    result_txt = f"플레이어 : {res['p_score']}\n뱅커 : {res['b_score']}\n\n<b>{res['sym']} {res['name']} 승 !</b>\n\n🏆 <b>적중자</b>\n- @{user_name} {'+' + str(f'{win_amt:,}') if is_win else '-'} 코인"
    await context.bot.send_photo(cid, f"{BASE_URL}{banner}", caption=result_txt, parse_mode='HTML')
    await asyncio.sleep(1)
    await context.bot.send_message(cid, get_roadmap(db["history"]) + "\n<b>바카라 그림장</b>", parse_mode='HTML')

# ================= [3] 메인 핸들러 (모든 명령어 복구) =================
async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    msg, uid, cid = update.message.text, update.effective_user.id, update.effective_chat.id
    u = db["users"].get(str(uid))

    if msg == ".명령어":
        help_txt = "📜 <b>명령어 리스트</b>\n━━━━━━━━━━━━━━\n<b>.가입 .내정보 .출석 .채광 .판매 .상점 .수리 .바카라 .플/뱅/타이 [금액] .송금 .랭킹 .공지 .문의</b>"
        return await update.message.reply_text(help_txt, parse_mode='HTML')

    if msg == ".가입":
        if u: return await update.message.reply_text("이미 가입되어 있습니다.")
        now = datetime.now()
        db["users"][str(uid)] = {"name": update.effective_user.first_name, "money": 100000, "inv": {}, "last_check": "", "durability": 100, "max_durability": 100, "pickaxe_name": "Onyx", "join_date": now.strftime("%Y-%m-%d")}
        save_db(); return await update.message.reply_text("✅ 가입 완료! 10만 G 지급.")

    if not u: return await update.message.reply_text("가입이 필요합니다. (.가입)")

    if msg == ".내정보":
        return await update.message.reply_text(f"👤 <b>내 정보</b>\n아이디: <code>{uid}</code>\n잔액: {u['money']:,} G\n내구도: {u['durability']}/{u['max_durability']}", parse_mode='HTML')

    if msg == ".출석":
        today = datetime.now().strftime("%Y-%m-%d")
        if u.get("last_check") == today: return await update.message.reply_text("❌ 오늘 이미 받음")
        u["money"] += 50000; u["last_check"] = today; save_db()
        return await update.message.reply_text("✅ 출석 5만 G 지급!")

    if msg == ".채광":
        now = time.time(); last = mine_cooldowns.get(str(uid), 0)
        if now - last < 40: return await update.message.reply_text(f"⏳ {int(40-(now-last))}초 남음")
        if u["durability"] <= 0: return await update.message.reply_text("❌ 내구도 부족")
        mine_cooldowns[str(uid)] = now; u["durability"] -= 1
        tier = random.choices(list(MINERALS.keys()), weights=[1, 5, 14, 30, 50])[0]
        m_name = random.choice(list(MINERALS[tier].keys())); u["inv"][m_name] = u["inv"].get(m_name, 0) + 1
        save_db(); return await update.message.reply_text(f"⛏ <b>채광 성공!</b>\n💎 {m_name}\n🔋 내구도: {u['durability']}", parse_mode='HTML')

    if msg == ".판매":
        btns = [[InlineKeyboardButton(f"{i}티어 판매", callback_data=f"sell_{i}")] for i in range(1, 6)]
        btns.append([InlineKeyboardButton("전체 판매", callback_data="sell_all")])
        return await update.message.reply_text("💰 판매 선택:", reply_markup=InlineKeyboardMarkup(btns))

    if msg.startswith((".플", ".뱅", ".타이")):
        if cid in room_betting_status: return
        try:
            amt = int(msg.split()[1])
            if u["money"] < amt: return await update.message.reply_text("❌ 잔액 부족")
            u["money"] -= amt; save_db(); room_betting_status[cid] = True
            await update.message.reply_text(f"✅ {amt:,} G 베팅 완료 (30초 뒤 마감)")
            await asyncio.sleep(30); res = db["next_result"]
            win = (msg.startswith(".플") and res["name"]=="플레이어") or (msg.startswith(".뱅") and res["name"]=="뱅커") or (msg.startswith(".타이") and res["name"]=="타이")
            rate = 8.0 if res["name"]=="타이" else 1.95 if res["name"]=="뱅커" else 2.0
            w_amt = int(amt * rate) if win else 0
            if win: u["money"] += w_amt
            await play_card_animation(context, cid, res, u['name'], w_amt, win)
            db["history"].append(res['sym']); db["game_count"] += 1; db["next_result"] = get_baccarat_result()
            save_db(); del room_betting_status[cid]
        except: 
            if cid in room_betting_status: del room_betting_status[cid]

    if msg.startswith(".송금"):
        try:
            _, tid, amt = msg.split(); amt = int(amt)
            if u["money"] >= amt and str(tid) in db["users"]:
                u["money"] -= amt; db["users"][str(tid)]["money"] += amt; save_db()
                return await update.message.reply_text("✅ 송금 완료!")
        except: pass

    if msg == ".공지":
        return await update.message.reply_text(f"📢 <a href='{NOTICE_CHANNEL}'>공지 채널 바로가기</a>", parse_mode='HTML')

    if msg == ".문의":
        return await update.message.reply_text(f"💬 <a href='{SUPPORT_CHANNEL}'>상담 채널 바로가기</a>", parse_mode='HTML')

# ================= [4] 콜백 핸들러 =================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); u = db["users"].get(uid)
    if not u: return await query.answer()
    await query.answer()
    if query.data.startswith("sell_"):
        gain = 0; target = query.data.replace("sell_", "")
        if target == "all":
            for t in MINERALS.values():
                for m, p in t.items(): gain += p * u["inv"].get(m, 0); u["inv"][m] = 0
        else:
            for m, p in MINERALS[f"{target}티어"].items(): gain += p * u["inv"].get(m, 0); u["inv"][m] = 0
        u["money"] += gain; save_db()
        await query.edit_message_text(f"💰 정산 완료: +{gain:,} G")

# ================= [5] 실행 =================
if __name__ == "__main__":
    keep_alive()
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), main_handler))
    app_bot.add_handler(CallbackQueryHandler(callback_handler))
    app_bot.run_polling()
