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

# ================= [1] 데이터베이스 및 설정 =================
BOT_TOKEN = "8484299407:AAEcDMZ70R3Z2ADw6xzamOrkJyP8AyZ2h2w" 
ADMIN_ID = 7476630349 
BASE_URL = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/"
DB_FILE = "casino_data.json"

db = {
    "users": {}, 
    "vault": 700000000000, 
    "history": [], 
    "game_count": 1, 
    "next_result": None,
    "active_rooms": [] 
}

mine_cooldowns = {}
room_betting_status = {}

# 광물 리스트 (오리하르콘 포함)
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

# ================= [2] 정석 바카라 엔진 (52장 셔플 덱) =================
def card_value(card):
    if card in ['J', 'Q', 'K', '10']: return 0
    if card == 'A': return 1
    return int(card)

def hand_value(hand):
    return sum(card_value(c) for c in hand) % 10

def create_deck():
    deck = ['A','2','3','4','5','6','7','8','9','10','J','Q','K'] * 4
    random.shuffle(deck)
    return deck

def banker_draw(b_hand, p_third=None):
    b_s = hand_value(b_hand)
    if p_third is None: return b_s <= 5
    pt = card_value(p_third)
    if b_s <= 2: return True
    elif b_s == 3: return pt != 8
    elif b_s == 4: return 2 <= pt <= 7
    elif b_s == 5: return 4 <= pt <= 7
    elif b_s == 6: return 6 <= pt <= 7
    return False

def get_baccarat_result():
    suits = ["h", "d", "c", "s"]
    deck = create_deck()
    p_nums, b_nums = [deck.pop(), deck.pop()], [deck.pop(), deck.pop()]
    p_cards = [{'val': n, 'suit': random.choice(suits)} for n in p_nums]
    b_cards = [{'val': n, 'suit': random.choice(suits)} for n in b_nums]
    p_third_n = None
    if hand_value(p_nums) <= 5:
        p_third_n = deck.pop()
        p_nums.append(p_third_n); p_cards.append({'val': p_third_n, 'suit': random.choice(suits)})
    if banker_draw(b_nums, p_third_n):
        b_n = deck.pop()
        b_nums.append(b_n); b_cards.append({'val': b_n, 'suit': random.choice(suits)})
    p_s, b_s = hand_value(p_nums), hand_value(b_nums)
    res_name = "타이" if p_s == b_s else "플레이어" if p_s > b_s else "뱅커"
    sym = "🟢" if p_s == b_s else "🔴" if p_s > b_s else "🔵"
    return {"name": res_name, "sym": sym, "p_cards": p_cards, "b_cards": b_cards, "p_score": p_s, "b_score": b_s}

if not db.get("next_result"): db["next_result"] = get_baccarat_result()

async def play_card_animation(context, cid, res, user_name, win_amt, is_win):
    suit_map = {"h": "hearts", "d": "diamonds", "c": "clubs", "s": "spades"}
    for i in range(2):
        await context.bot.send_photo(cid, f"{BASE_URL}{res['p_cards'][i]['val']}_of_{suit_map[res['p_cards'][i]['suit']]}.png", caption=f"👤 플레이어 카드 {i+1}")
        await context.bot.send_photo(cid, f"{BASE_URL}{res['b_cards'][i]['val']}_of_{suit_map[res['b_cards'][i]['suit']]}.png", caption=f"🏦 뱅커 카드 {i+1}")
        await asyncio.sleep(0.7)
    if len(res['p_cards']) > 2:
        await context.bot.send_photo(cid, f"{BASE_URL}{res['p_cards'][2]['val']}_of_{suit_map[res['p_cards'][2]['suit']]}.png", caption="👤 플레이어 추가 카드")
        await asyncio.sleep(0.5)
    if len(res['b_cards']) > 2:
        await context.bot.send_photo(cid, f"{BASE_URL}{res['b_cards'][2]['val']}_of_{suit_map[res['b_cards'][2]['suit']]}.png", caption="🏦 뱅커 추가 카드")
        await asyncio.sleep(0.5)
    banner = "player_win.png" if res['name'] == "플레이어" else "banker_win.png" if res['name'] == "뱅커" else "tie_win.png"
    result_txt = f"<b>{res['sym']} {res['name']} 승 !</b>\n(P:{res['p_score']} vs B:{res['b_score']})\n\n🏆 적중자: @{user_name} {'+' + str(f'{win_amt:,}') if is_win else '-'} G"
    await context.bot.send_photo(cid, f"{BASE_URL}{banner}", caption=result_txt, parse_mode='HTML')

# ================= [3] 메인 핸들러 (명령어 인식 강화) =================
async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # --- [상담 버튼 클릭 처리] ---
    if update.callback_query:
        query = update.callback_query
        uid = query.from_user.id
        if query.data == "start_inquiry":
            await query.answer()
            if str(uid) in db["users"]:
                db["users"][str(uid)]["status"] = "inquiry"; save_db()
                await context.bot.send_message(uid, "💬 <b>1:1 고객센터</b>\n\n문의 내용을 입력해주시면 담당자가 답변드립니다.")
            return

    if not update.message or not update.message.text: return
    msg = update.message.text.strip()
    uid, cid = update.effective_user.id, update.effective_chat.id
    u = db["users"].get(str(uid))

    if cid not in db["active_rooms"]:
        db["active_rooms"].append(cid); save_db()

    # --- [익명 상담 메시지 전달] ---
    if u and u.get("status") == "inquiry" and not msg.startswith("."):
        await context.bot.send_message(ADMIN_ID, f"📩 <b>[문의 도착]</b>\nID: <code>{uid}</code>\n내용: {msg}", parse_mode='HTML')
        await update.message.reply_text("✅ 문의가 접수되었습니다.")
        u["status"] = "normal"; save_db(); return

    # --- [관리자 전용] ---
    if str(uid) == str(ADMIN_ID):
        if msg.startswith("/답장"):
            try:
                parts = msg.split(); tid = parts[1]; content = " ".join(parts[2:])
                await context.bot.send_message(tid, f"🤖 <b>[G-COIN 고객센터 답변]</b>\n\n{content}", parse_mode='HTML')
                return await update.message.reply_text(f"✅ {tid}님께 전송 완료")
            except: pass
        if msg.startswith(".지급"):
            try:
                _, tid, amt = msg.split(); amt = int(amt)
                if str(tid) in db["users"]:
                    db["users"][str(tid)]["money"] += amt; db["vault"] -= amt; save_db()
                    return await update.message.reply_text(f"지급 완료: {amt:,} G")
            except: pass
        if msg == ".현황":
            return await update.message.reply_text(f"방: {len(db['active_rooms'])} / 유저: {len(db['users'])}")

    # --- [유저 명령어 (풀 버전)] ---
    if msg == ".명령어":
        return await update.message.reply_text("📜 .가입 .출석 .내정보 .채광 .인벤 .상점 .송금 .바카라 .랭킹 .플/뱅/타이 [금액]", parse_mode='HTML')

    if msg == ".가입":
        if u: return await update.message.reply_text("이미 가입됨")
        db["users"][str(uid)] = {"name": update.effective_user.first_name, "money": 100000, "inv": {}, "last_check": "", "durability": 100, "max_durability": 100, "pickaxe_name": "Onyx", "status": "normal"}
        save_db(); return await update.message.reply_text("✅ 가입 완료! 10만 G 지급")

    if not u: return

    if msg == ".출석":
        today = datetime.now().strftime("%Y-%m-%d")
        if u.get("last_check") == today: return await update.message.reply_text("❌ 금일 완료")
        u["money"] += 50000; u["last_check"] = today; save_db()
        return await update.message.reply_text("✅ 5만 G 지급")

    if msg == ".내정보":
        kb = [[InlineKeyboardButton("📢 공지", url="https://t.me/your_channel"), InlineKeyboardButton("💬 상담", callback_data="start_inquiry")]]
        return await update.message.reply_text(f"👤 <b>{u['name']}</b>\nID: <code>{uid}</code>\n잔액: {u['money']:,} G\n내구도: {u['durability']}/{u['max_durability']}", reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')

    if msg == ".채광":
        now = time.time()
        if uid in mine_cooldowns and now - mine_cooldowns[uid] < 5:
            return await update.message.reply_text("⏱ 쿨타임 (5초)")
        if u["durability"] <= 0: return await update.message.reply_text("🪓 수리 필요")
        tier = random.choices(["1티어","2티어","3티어","4티어","5티어"], [1,5,15,30,49])[0]
        m_name = random.choice(list(MINERALS[tier].keys()))
        u["inv"][m_name] = u["inv"].get(m_name, 0) + 1
        u["durability"] -= 1; mine_cooldowns[uid] = now; save_db()
        return await update.message.reply_text(f"⛏ <b>{m_name}</b> 채굴 성공!")

    if msg == ".인벤":
        txt = "🎒 <b>내 가방</b>\n"
        for k, v in u["inv"].items(): txt += f"▫️ {k}: {v}개\n"
        return await update.message.reply_text(txt if u["inv"] else "가방이 비었습니다.", parse_mode='HTML')

    if msg == ".바카라":
        history = db["history"][-50:]
        grid = [["⬜" for _ in range(10)] for _ in range(5)]
        for i, sym in enumerate(history): grid[i % 5][i // 5] = sym
        roadmap = "📊 <b>실시간 로드맵</b>\n━━━━━━━━━━━━━━\n"
        for row in grid: roadmap += "".join(row) + "\n"
        roadmap += "━━━━━━━━━━━━━━\n(🔴:플 🔵:뱅 🟢:타이)"
        return await update.message.reply_text(roadmap, parse_mode='HTML')

    if msg.startswith((".플", ".뱅", ".타이")):
        if cid in room_betting_status: return
        try:
            amt = int(msg.split()[1])
            if u["money"] < amt: return await update.message.reply_text("잔액 부족")
            u["money"] -= amt; room_betting_status[cid] = True; save_db()
            c_game = db["game_count"]
            await update.message.reply_text(f"✅ {c_game}회차 베팅 완료")
            await asyncio.sleep(30); await update.message.reply_text(f"🚫 마감")
            await asyncio.sleep(5)
            res = db["next_result"]
            win = (msg.startswith(".플") and res["name"]=="플레이어") or (msg.startswith(".뱅") and res["name"]=="뱅커") or (msg.startswith(".타이") and res["name"]=="타이")
            w_amt = int(amt * (8.0 if res["name"]=="타이" else 1.95 if res["name"]=="뱅커" else 2.0)) if win else 0
            if win: u["money"] += w_amt
            else: db["vault"] += amt
            await play_card_animation(context, cid, res, u['name'], w_amt, win)
            db["history"].append(res['sym']); db["game_count"] += 1; db["next_result"] = get_baccarat_result()
            save_db(); del room_betting_status[cid]
        except: 
            if cid in room_betting_status: del room_betting_status[cid]

# ================= [4] 실행부 (충돌 완전 방지) =================
if __name__ == "__main__":
    keep_alive()
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CallbackQueryHandler(main_handler))
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), main_handler))
    # drop_pending_updates: 봇이 꺼진 동안 유저가 보낸 메시지를 무시하고 시작함 (충돌 방지 핵심)
    app_bot.run_polling(drop_pending_updates=True)
