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
BOT_TOKEN = "8484299407:AAGGpWvsN6gyWDbp0vv2QoSAUSyuvAwDjmQ"
ADMIN_ID = 7476630349 
NOTICE_CHANNEL = "https://t.me/GCOIN7777"
CS_LINK = "https://t.me/GCOINZ_BOT" 

# 깃허브 데이터 경로 (수정 금지)
BASE_URL = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/"
DB_FILE = "casino_data.json"

db = {"users": {}, "vault": 500000000000, "history": [], "active_rooms": [], "game_count": 1}
mine_cooldowns = {}
pending_replies = {}
room_betting_status = {}

# 카드 매칭용 데이터
CARD_VALUES = {1: "ace", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 10: "10", 11: "jack", 12: "queen", 13: "king"}
SUITS = ["spades", "hearts", "diamonds", "clubs"]

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

# ================= 🛠 [2] 보조 함수 =================
async def send_baccarat_animation(context, chat_id, p_cards, b_cards, res_msg):
    """카드를 순서대로 보여주는 애니메이션 효과"""
    # 1. 딜러 이미지
    await context.bot.send_photo(chat_id=chat_id, photo=BASE_URL+"dealer.jpg", caption="🃏 <b>딜러가 카드를 배분합니다...</b>", parse_mode='HTML')
    await asyncio.sleep(1.5)

    # 2. 플레이어 카드 배분
    for i, card in enumerate(p_cards, 1):
        url = f"{BASE_URL}{CARD_VALUES[card['val']]}_of_{card['suit']}.png"
        await context.bot.send_photo(chat_id=chat_id, photo=url, caption=f"👤 플레이어 {i}번째 카드")
        await asyncio.sleep(0.7)

    # 3. 뱅커 카드 배분
    for i, card in enumerate(b_cards, 1):
        url = f"{BASE_URL}{CARD_VALUES[card['val']]}_of_{card['suit']}.png"
        await context.bot.send_photo(chat_id=chat_id, photo=url, caption=f"🏦 뱅커 {i}번째 카드")
        await asyncio.sleep(0.7)

    # 4. 최종 결과 메시지 전송
    await context.bot.send_message(chat_id=chat_id, text=res_msg, parse_mode='HTML')

# ================= 🛠 [3] 격자 연출 함수 (V6.9 추가) =================
def generate_grid_roadmap(history):
    """최근 50회차 전적을 주신 이미지의 6x9 격자 패턴으로 시각화"""
    recent_history = history[-50:]
    grid = [["⬜" for _ in range(9)] for _ in range(6)]
    
    for i, result in enumerate(recent_history):
        row = i % 6
        col = i // 6
        if col < 9:
            grid[row][col] = result

    roadmap_text = "📊 <b>최근 전적 (6x9 격자)</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    for row in grid:
        roadmap_text += "".join(row) + "\n"
    
    return roadmap_text

# ================= 🛠 [4] 메인 핸들러 =================
async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    msg, uid, cid = update.message.text, update.effective_user.id, update.effective_chat.id
    u = db["users"].get(str(uid))

    if str(cid) not in db["active_rooms"]: db["active_rooms"].append(str(cid))

    # [명령어 처리 로직]
    if msg == ".가입":
        if u: return await update.message.reply_text("이미 가입된 계정입니다.")
        db["users"][str(uid)] = {"name": update.effective_user.first_name, "money": 100000, "inv": {}, "last_check": "", "durability": 100, "max_durability": 100, "pickaxe_name": "Onyx", "join_date": datetime.now().strftime("%Y-%m-%d")}
        await update.message.reply_text("✅ <b>가입 완료!</b> 초기 자금 100,000 G 지급.", parse_mode='HTML')

    elif msg == ".출석":
        today = datetime.now().strftime("%Y-%m-%d")
        if u["last_check"] == today: return await update.message.reply_text("오늘 이미 출석하셨습니다.")
        u["money"] += 50000; u["last_check"] = today
        await update.message.reply_text("✅ <b>출석 완료!</b> 50,000 G 지급.", parse_mode='HTML')

    elif msg == ".인벤":
        inv_text = "🎒 <b>보유 광물 목록</b>\n\n"
        has_item = False
        for tier in MINERALS.values():
            for name, price in tier.items():
                count = u["inv"].get(name, 0); 
                if count > 0: inv_text += f"📦 {name} | {count}개 ({price:,}G)\n"; has_item = True
        await update.message.reply_text(inv_text if has_item else "가방이 비어 있습니다.", parse_mode='HTML')

    elif msg == ".채광":
        now_ts = time.time()
        if now_ts - mine_cooldowns.get(str(uid), 0) < 40:
            return await update.message.reply_text(f"⏳ <b>채광 대기 중</b>", parse_mode='HTML')
        if u["durability"] <= 0: return await update.message.reply_text("❌ 내구도 부족! .수리가 필요합니다.")
        
        mine_cooldowns[str(uid)] = now_ts; u["durability"] -= 1
        tier = random.choices(list(MINERALS.keys()), weights=[1, 5, 14, 30, 50])[0]
        m_name = random.choice(list(MINERALS[tier].keys())); m_price = MINERALS[tier][m_name]
        u["inv"][m_name] = u["inv"].get(m_name, 0) + 1
        await update.message.reply_text(f"⛏ <b>채광 완료!</b>\n💎 <b>광물:</b> {m_name}\n🔋 <b>내구도:</b> {u['durability']}/{u['max_durability']}", parse_mode='HTML')

    elif msg == ".판매":
        kb = [[InlineKeyboardButton("💎 1티어", callback_data="sell_1"), InlineKeyboardButton("✨ 2티어", callback_data="sell_2")],
              [InlineKeyboardButton("💰 전체 판매", callback_data="sell_all")]]
        await update.message.reply_text("💰 <b>판매하실 티어를 선택하세요.</b>", reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')

    elif msg.startswith(".송금"):
        try:
            parts = msg.split()
            target_id = str(update.message.reply_to_message.from_user.id) if update.message.reply_to_message else parts[1]
            amount = int(parts[-1])
            if u["money"] < amount or target_id == str(uid): raise Exception()
            fee = int(amount * 0.08); net = amount - fee
            u["money"] -= amount; db["users"][target_id]["money"] += net; db["vault"] += fee
            await update.message.reply_text(f"✅ <b>송금 완료</b>\n실입금액: {net:,} G", parse_mode='HTML')
        except: await update.message.reply_text("❌ <b>송금 실패</b> (잔액 부족 또는 형식 오류)", parse_mode='HTML')

    elif msg == ".상점":
        kb = [[InlineKeyboardButton(f"{n} 구매", callback_data=f"buy_{n}")] for n in SHOP_ITEMS.keys()]
        await update.message.reply_text("⚒ <b>장비 상점</b>", reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')

    # [.바카라] 전적판 격자 연출 (주신 이미지 패턴 적용)
    elif msg == ".바카라":
        roadmap_text = generate_grid_roadmap(db["history"])
        try:
            # 주신 grid.png.JPG를 배경으로, 메시지 내부에 격자 텍스트 출력
            await update.message.reply_photo(photo=BASE_URL+"grid.png.JPG", caption=roadmap_text, parse_mode='HTML')
        except:
            # 이미지 전송 실패 시 텍스트 격자만이라도 출력
            await update.message.reply_text(roadmap_text, parse_mode='HTML')

    # [바카라 베팅 결과 기호 수정🔴🔵🟢]
    elif msg.startswith((".플", ".뱅", ".타이")):
        if cid in room_betting_status: return 
        try:
            amt = int(msg.split()[1])
            if u["money"] < amt: return await update.message.reply_text("❌ 잔액 부족", parse_mode='HTML')
            
            room_betting_status[cid] = True
            await update.message.reply_text(f"🎲 <b>{db['game_count']}회차 베팅 시작!</b>\n30초 후 마감됩니다.", parse_mode='HTML')
            
            # 카드 생성
            p_cards = [{"val": random.randint(1, 13), "suit": random.choice(SUITS)} for _ in range(2)]
            b_cards = [{"val": random.randint(1, 13), "suit": random.choice(SUITS)} for _ in range(2)]
            
            p_score = sum([c['val'] if c['val'] < 10 else 0 for c in p_cards]) % 10
            b_score = sum([c['val'] if c['val'] < 10 else 0 for c in b_cards]) % 10
            
            # 3구 보충
            if p_score <= 5: 
                new_c = {"val": random.randint(1, 13), "suit": random.choice(SUITS)}
                p_cards.append(new_c); p_score = (p_score + (new_c['val'] if new_c['val'] < 10 else 0)) % 10

            res_name = "타이 승" if p_score == b_score else "플레이어 승" if p_score > b_score else "뱅커 승"
            sym = "🟢" if p_score == b_score else "🔴" if p_score > b_score else "🔵" # 결과 기호 변경

            if uid == ADMIN_ID: await context.bot.send_message(chat_id=ADMIN_ID, text=f"📢 <b>예고:</b> {sym} {res_name}")

            await asyncio.sleep(30)
            await update.message.reply_text(f"🚫 <b>{db['game_count']}회차 베팅 마감!</b>", parse_mode='HTML')
            await asyncio.sleep(3)
            await update.message.reply_text(f"🎊 <b>{db['game_count']}회차 결과 발표!!</b>", parse_mode='HTML')
            await asyncio.sleep(2)
            
            u["money"] -= amt 
            is_win = (msg.startswith(".플") and "플레이어" in res_name) or (msg.startswith(".뱅") and "뱅커" in res_name) or (msg.startswith(".타이") and "타이" in res_name)
            res_msg = f"🃏 <b>{db['game_count']}회차 게임 결과</b>\n🏆 <b>결과: {sym} {res_name}</b>\n"
            
            if is_win:
                rate = 8.0 if "타이" in res_name else 1.95 if "뱅커" in res_name else 2.0
                win_amt = int(amt * rate); u["money"] += win_amt; res_msg += f"✅ +{win_amt:,} G"
            else: res_msg += f"💀 -{amt:,} G"

            await send_baccarat_animation(context, cid, p_cards, b_cards, res_msg)
            db["history"].append(sym); db["game_count"] += 1; del room_betting_status[cid]
        except: 
            if cid in room_betting_status: del room_betting_status[cid]
            await update.message.reply_text("❌ 베팅 형식 오류", parse_mode='HTML')

    elif msg == ".랭킹":
        top = sorted(db["users"].items(), key=lambda x: x[1]['money'], reverse=True)[:10]
        txt = "🏆 <b>G코인 랭킹</b>\n\n"
        for i, (id, d) in enumerate(top, 1): txt += f"{i}위. {d['name']} | {d['money']:,} G\n"
        await update.message.reply_text(txt, parse_mode='HTML')

    elif msg == ".명령어":
        await update.message.reply_text("📜 .가입 .출석 .인벤 .채광 .판매 .상점 .송금 .바카라 .플 .뱅 .타이 .랭킹", parse_mode='HTML')

    save_db()

# ================= 🖱 [5] 콜백 핸들러 =================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); u = db["users"].get(uid); data = query.data
    await query.answer()
    
    if data.startswith("sell_"):
        gain = 0; t_label = "전체 판매" if "all" in data else "티어 판매"
        for mins in MINERALS.values():
            for m, p in mins.items():
                if "all" in data or data.split("_")[1] in str(m):
                    c = u["inv"].get(m, 0); gain += (p * c); u["inv"][m] = 0
        if gain > 0: u["money"] += gain; await query.edit_message_text(f"💰 <b>{t_label} 완료</b>\n정산: {gain:,} G", parse_mode='HTML')
        else: await query.edit_message_text("❌ 판매할 광물이 없습니다.")
            
    elif data.startswith("buy_"):
        n = data.split("_")[1]; i = SHOP_ITEMS[n]
        if u["money"] >= i["price"]:
            u["money"] -= i["price"]; u["pickaxe_name"] = n; u["durability"] = i["durability"]; u["max_durability"] = i["durability"]
            await query.edit_message_text(f"✅ <b>{n}</b> 구매 완료!")
        else: await query.edit_message_text(f"❌ 잔액 부족 (가격: {i['price']:,} G)")
    
    save_db()

def main():
    keep_alive()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), main_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()

if __name__ == "__main__": main()
