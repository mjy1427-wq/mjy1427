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
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web); t.daemon = True; t.start()

# ================= 🔐 [1] 설정 및 데이터베이스 =================
BOT_TOKEN = "8484299407:AAE6HoOeutOiDxFjewWVZaMy21MPNa3KAXo"
ADMIN_ID = 7476630349 
BASE_URL = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/"
DB_FILE = "casino_data.json"

db = {"users": {}, "vault": 500000000000, "history": [], "game_count": 1, "next_result": None}
mine_cooldowns = {}
room_betting_status = {}

CARD_VALUES = {1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 10: "10", 11: "11", 12: "12", 13: "13"}
SUITS = ["h", "d", "c", "s"]

SHOP_ITEMS = {
    "Onyx": {"price": 1000000, "durability": 100},
    "Sapphire": {"price": 5000000, "durability": 300},
    "Topaz": {"price": 15000000, "durability": 500},
    "Emerald": {"price": 50000000, "durability": 1000},
    "Ruby": {"price": 250000000, "durability": 5000},
    "Opal": {"price": 1000000000, "durability": 10000},
    "Diamond": {"price": 2000000000, "durability": 25000}
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

# ================= 🛠 [2] 바카라 엔진 및 로직 =================
def get_baccarat_result():
    p_cards = [{'val': random.randint(1, 13), 'suit': random.choice(SUITS)} for _ in range(2)]
    b_cards = [{'val': random.randint(1, 13), 'suit': random.choice(SUITS)} for _ in range(2)]
    p_score = sum([c['val'] if c['val'] < 10 else 0 for c in p_cards]) % 10
    b_score = sum([c['val'] if c['val'] < 10 else 0 for c in b_cards]) % 10
    if p_score <= 5:
        nc = {'val': random.randint(1, 13), 'suit': random.choice(SUITS)}; p_cards.append(nc)
        p_score = (p_score + (nc['val'] if nc['val'] < 10 else 0)) % 10
    if b_score <= 5:
        nc = {'val': random.randint(1, 13), 'suit': random.choice(SUITS)}; b_cards.append(nc)
        b_score = (b_score + (nc['val'] if nc['val'] < 10 else 0)) % 10
    res_name = "타이" if p_score == b_score else "플레이어" if p_score > b_score else "뱅커"
    sym = "🟢" if p_score == b_score else "🔴" if p_score > b_score else "🔵"
    return {"name": res_name, "sym": sym, "p_cards": p_cards, "b_cards": b_cards}

if not db.get("next_result"): db["next_result"] = get_baccarat_result()

async def play_baccarat_animation(context, chat_id, p_cards, b_cards, res_msg):
    await asyncio.sleep(2)
    for c in p_cards[:2]: await context.bot.send_photo(chat_id=chat_id, photo=f"{BASE_URL}{CARD_VALUES[c['val']]}_{c['suit']}.png")
    await asyncio.sleep(1.5)
    for c in b_cards[:2]: await context.bot.send_photo(chat_id=chat_id, photo=f"{BASE_URL}{CARD_VALUES[c['val']]}_{c['suit']}.png")
    if len(p_cards) > 2:
        await asyncio.sleep(1); c = p_cards[2]
        await context.bot.send_photo(chat_id=chat_id, photo=f"{BASE_URL}{CARD_VALUES[c['val']]}_{c['suit']}.png", caption="👤 플레이어 추가 카드")
    if len(b_cards) > 2:
        await asyncio.sleep(1); c = b_cards[2]
        await context.bot.send_photo(chat_id=chat_id, photo=f"{BASE_URL}{CARD_VALUES[c['val']]}_{c['suit']}.png", caption="🏦 뱅커 추가 카드")
    await asyncio.sleep(1)
    await context.bot.send_photo(chat_id=chat_id, photo=BASE_URL+"dealer.jpg")
    await context.bot.send_photo(chat_id=chat_id, photo=BASE_URL+"gcoin_logo.png", caption=res_msg, parse_mode='HTML')

def history_to_roadmap(history):
    recent = history[-45:]; grid = [["⬜" for _ in range(10)] for _ in range(5)]
    for i, res in enumerate(recent):
        if i // 5 < 10: grid[i % 5][i // 5] = res
    txt = "📊 <b>바카라 로드맵</b>\n"
    for r in grid: txt += "".join(r) + "\n"
    return txt

# ================= 🛠 [3] 메인 핸들러 =================
async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    msg, uid, cid = update.message.text, update.effective_user.id, update.effective_chat.id
    u = db["users"].get(str(uid))

    # [명령어] 세로 나열
    if msg == ".명령어":
        help_txt = (
            "📜 <b>G-COIN 전체 명령어</b>\n"
            "━━━━━━━━━━━━━━\n"
            ".가입 ➖ 계정 생성\n"
            ".내정보 ➖ 상태 확인\n"
            ".출석 ➖ 5만 G 지급\n"
            ".채광 ➖ 광물 채굴\n"
            ".판매 ➖ 광물 정산\n"
            ".상점 ➖ 장비 구매\n"
            ".수리 ➖ 내구 충전\n"
            ".바카라 ➖ 전적 확인\n"
            ".플/뱅/타이 [금액] ➖ 베팅\n"
            ".송금 [ID] [금액] ➖ 선물\n"
            ".랭킹 ➖ 자산 순위\n"
            "━━━━━━━━━━━━━━"
        )
        return await update.message.reply_text(help_txt, parse_mode='HTML')

    if msg == ".가입":
        if u: return await update.message.reply_text("이미 가입됨.")
        db["users"][str(uid)] = {"name": update.effective_user.first_name, "money": 100000, "inv": {}, "last_check": "", "durability": 100, "max_durability": 100, "pickaxe_name": "Onyx"}
        save_db(); return await update.message.reply_text("✅ 가입 완료")

    if not u and msg.startswith("."): return await update.message.reply_text("가입 필요 (.가입)")

    if msg == ".내정보":
        return await update.message.reply_text(f"👤 <b>내 정보</b>\n\n이름: {u['name']}\n아이디: <code>{uid}</code>\n잔액: {u['money']:,} G\n곡괭이: {u['pickaxe_name']}\n🔋 내구도: {u['durability']}/{u['max_durability']}", parse_mode='HTML')

    if msg == ".채광":
        now = time.time()
        if now - mine_cooldowns.get(str(uid), 0) < 40: return await update.message.reply_text("⏳ 40초 대기")
        if u["durability"] <= 0: return await update.message.reply_text("❌ 수리 필요")
        mine_cooldowns[str(uid)] = now; u["durability"] -= 1
        tier = random.choices(list(MINERALS.keys()), weights=[1, 5, 14, 30, 50])[0]
        m_name = random.choice(list(MINERALS[tier].keys())); m_price = MINERALS[tier][m_name]
        u["inv"][m_name] = u["inv"].get(m_name, 0) + 1
        res = (f"⛏ <b>채광 성공!</b>\n💎 광물: {m_name} ({m_price:,} G)\n━━━━━━━━━━━━━━\n⚒ 곡괭이: {u['pickaxe_name']}\n🔋 내구도: {u['durability']} / {u['max_durability']}")
        save_db(); return await update.message.reply_text(res, parse_mode='HTML')

    if msg == ".바카라":
        return await update.message.reply_photo(photo=BASE_URL+"grid.png.JPG", caption=history_to_roadmap(db["history"]), parse_mode='HTML')

    if msg.startswith((".플", ".뱅", ".타이")):
        if cid in room_betting_status: return 
        try:
            amt = int(msg.split()[1])
            if u["money"] < amt: return await update.message.reply_text("❌ 잔액 부족")
            
            # [실시간] 유저 잔액 즉시 차감
            u["money"] -= amt
            save_db()
            
            room_betting_status[cid] = True
            await update.message.reply_text(f"✅ <b>{db['game_count']}회차 베팅완료!</b>\n💵 베팅금: {amt:,} G (차감완료)\n⏳ 30초 후 마감.", parse_mode='HTML')
            
            res = db["next_result"]
            await asyncio.sleep(30)
            await update.message.reply_text(f"🚫 <b>{db['game_count']}회차 베팅 마감!</b>", parse_mode='HTML')
            
            win = (msg.startswith(".플") and res["name"]=="플레이어") or (msg.startswith(".뱅") and res["name"]=="뱅커") or (msg.startswith(".타이") and res["name"]=="타이")
            rate = 8.0 if res["name"]=="타이" else 1.95 if res["name"]=="뱅커" else 2.0
            
            res_msg = f"🏆 <b>{db['game_count']}회차 결과</b>\n━━━━━━━━━━━━━━\n승리: {res['sym']} {res['name']}\n"
            if win:
                win_amt = int(amt * rate)
                db["vault"] -= (win_amt - amt) # 당첨금 금고 전송 (아무도 모르게)
                u["money"] += win_amt
                res_msg += f"✅ 적중 유저: <code>{uid}</code>\n💰 당첨금: +{win_amt:,} G"
            else:
                db["vault"] += amt # 낙첨금 금고 전송 (아무도 모르게)
                res_msg += f"💀 낙첨 유저: <code>{uid}</code>\n💸 낙첨금: -{amt:,} G"

            await play_baccarat_animation(context, cid, res["p_cards"], res["b_cards"], res_msg)
            
            db["history"].append(res['sym']); db["game_count"] += 1
            if db["game_count"] > 45: db["game_count"] = 1; db["history"] = []
            
            # 다음 결과 예고
            db["next_result"] = get_baccarat_result()
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"📢 <b>{db['game_count']}회차 예고:</b> {db['next_result']['sym']} {db['next_result']['name']}")
            
            save_db(); del room_betting_status[cid]
        except: 
            if cid in room_betting_status: del room_betting_status[cid]
            await update.message.reply_text("❌ 오류 발생")

# ================= 🖱 [4] 콜백 및 실행 =================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; u = db["users"].get(str(query.from_user.id))
    await query.answer()
    if not u or not query.data.startswith("sell_"): return
    target = query.data.split("_")[1]; gain = 0
    if target == "all":
        for mins in MINERALS.values():
            for m, p in mins.items(): gain += (p * u["inv"].get(m, 0)); u["inv"][m] = 0
    else:
        for m, p in MINERALS[f"{target}티어"].items(): gain += (p * u["inv"].get(m, 0)); u["inv"][m] = 0
    u["money"] += gain; save_db()
    await query.edit_message_text(f"💰 정산 완료: +{gain:,} G")

def main():
    keep_alive()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), main_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()

if __name__ == "__main__": main()
