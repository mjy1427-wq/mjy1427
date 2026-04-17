import random, json, asyncio, os, time
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
# 주의: Conflict 에러 발생 시 @BotFather에서 토큰을 재발급받아 아래에 넣으세요.
BOT_TOKEN = "8484299407:AAGtzWZEhKmIdQmWoD1HiS3_h1grl2Asyog" 
ADMIN_ID = 7476630349 
BASE_URL = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/"
DB_FILE = "casino_data.json"

db = {"users": {}, "vault": 700000000000, "history": [], "game_count": 1, "next_result": None, "active_rooms": []}
mine_cooldowns = {}; room_betting_status = {}

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
def hand_value(hand): return sum(card_value(c) for c in hand) % 10
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
        p_third_n = deck.pop(); p_nums.append(p_third_n); p_cards.append({'val': p_third_n, 'suit': random.choice(suits)})
    if banker_draw(b_nums, p_third_n):
        b_n = deck.pop(); b_nums.append(b_n); b_cards.append({'val': b_n, 'suit': random.choice(suits)})
    p_s, b_s = hand_value(p_nums), hand_value(b_nums)
    res_name = "타이" if p_s == b_s else "플레이어" if p_s > b_s else "뱅커"
    sym = "🟢" if p_s == b_s else "🔴" if p_s > b_s else "🔵"
    return {"name": res_name, "sym": sym, "p_cards": p_cards, "b_cards": b_cards, "p_score": p_s, "b_score": b_s}

if not db.get("next_result"): db["next_result"] = get_baccarat_result()

async def play_card_animation(context, cid, res, user_name, win_amt, is_win):
    suit_map = {"h": "hearts", "d": "diamonds", "c": "clubs", "s": "spades"}
    for i in range(2):
        await context.bot.send_photo(cid, f"{BASE_URL}{res['p_cards'][i]['val']}_of_{suit_map[res['p_cards'][i]['suit']]}.png")
        await context.bot.send_photo(cid, f"{BASE_URL}{res['b_cards'][i]['val']}_of_{suit_map[res['b_cards'][i]['suit']]}.png")
        await asyncio.sleep(0.5)
    banner = "player_win.png" if res['name'] == "플레이어" else "banker_win.png" if res['name'] == "뱅커" else "tie_win.png"
    result_txt = f"<b>{res['sym']} {res['name']} 승 !</b>\n🏆 @{user_name} 적중: {win_amt:,} G"
    await context.bot.send_photo(cid, f"{BASE_URL}{banner}", caption=result_txt, parse_mode='HTML')

# ================= [3] 메인 핸들러 =================
async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # --- [상담 버튼 클릭 처리] ---
    if update.callback_query:
        query = update.callback_query
        uid = query.from_user.id
        if query.data == "start_inquiry":
            await query.answer()
            if str(uid) in db["users"]:
                db["users"][str(uid)]["status"] = "inquiry"; save_db()
                await context.bot.send_message(uid, "💬 <b>1:1 고객센터</b>\n\n문의 내용을 입력해주시면 담당자가 답변드립니다.", parse_mode='HTML')
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
                    return await update.message.reply_text(f"지급 완료 target: {tid} 금액: {amt:,} G")
            except: pass
        if msg == ".현황":
            return await update.message.reply_text(f"방: {len(db['active_rooms'])} / 유저: {len(db['users'])}")

    # --- [유저 명령어 (스타일 창 완전 패치)] ---
    if msg == ".명령어":
        kb = [
            [InlineKeyboardButton("📢 공지", url="https://t.me/your_link"), InlineKeyboardButton("💬 상담", callback_data="start_inquiry")]
        ]
        cmd_txt = (
            "📜 <b>명령어 안내</b>\n"
            "━━━━━━━━━━━━━━\n"
            "▫️ <b>기본:</b> .가입 .출석 .내정보 .송금 .랭킹\n"
            "▫️ <b>채광:</b> .채광 .인벤\n"
            "▫️ <b>게임:</b> .바카라 .플/뱅/타이 [금액]\n"
            "━━━━━━━━━━━━━━\n"
            "유저 문의는 .내정보 -> 상담 버튼 이용"
        )
        return await update.message.reply_text(cmd_txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')

    if msg == ".가입":
        if u: return await update.message.reply_text("❌ 이미 가입된 계정입니다.")
        db["users"][str(uid)] = {"name": update.effective_user.first_name, "money": 100000, "inv": {}, "last_check": "", "durability": 100, "max_durability": 100, "pickaxe_name": "Onyx", "status": "normal"}
        save_db(); return await update.message.reply_text("✅ 가입 완료! 10만 G 지급되었습니다.", parse_mode='HTML')

    if not u: return # 가입 전 명령어 무시

    if msg == ".출석":
        today = datetime.now().strftime("%Y-%m-%d")
        if u.get("last_check") == today: return await update.message.reply_text("❌ 오늘은 이미 출석 완료했습니다.")
        u["money"] += 50000; u["last_check"] = today; save_db()
        return await update.message.reply_text("✅ 출석 완료! 5만 G 지급되었습니다.", parse_mode='HTML')

    if msg == ".내정보":
        kb = [
            [InlineKeyboardButton("📢 공지", url="https://t.me/your_link"), InlineKeyboardButton("💬 상담", callback_data="start_inquiry")]
        ]
        info_txt = (
            f"👤 <b>내 정보</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"👤 <b>이름:</b> {u['name']}\n"
            f"아이디: <code>{uid}</code>\n"
            f"💰 <b>잔액:</b> {u['money']:,} G\n"
            f"🔧 <b>내구도:</b> {u['durability']}/{u['max_durability']}\n"
            f"━━━━━━━━━━━━━━"
        )
        return await update.message.reply_text(info_txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')

    if msg == ".채광":
        now = time.time()
        if uid in mine_cooldowns and now - mine_cooldowns[uid] < 5:
            return await update.message.reply_text("⏱ 쿨타임 (5초)")
        if u["durability"] <= 0: return await update.message.reply_text("❌ 내구도 부족! 수리 필요")
        
        # 1티어 1%, 5티어 49% 등 확률 세팅 (V11.5와 동일)
        tier = random.choices(["1티어","2티어","3티어","4티어","5티어"], [1,5,15,30,49])[0]
        m_name = random.choice(list(MINERALS[tier].keys()))
        m_price = MINERALS[tier][m_name]
        
        u["inv"][m_name] = u["inv"].get(m_name, 0) + 1
        u["durability"] -= 1; mine_cooldowns[uid] = now; save_db()
        
        # [채광 결과 스타일 패치]
        mine_msg = (
            f"⛏ <b>채광 완료!</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"💎 <b>획득:</b> {m_name}\n"
            f"💰 <b>가치:</b> {m_price:,Interpretation} G\n"
            f"🔧 <b>내구도:</b> {u['durability']}/{u['max_durability']}\n"
            f"━━━━━━━━━━━━━━"
        )
        return await update.message.reply_text(mine_msg, parse_mode='HTML')

    if msg == ".인벤":
        if not u["inv"]: return await update.message.reply_text("🎒 가방이 비어있습니다.")
        # [인벤토리 스타일 패치]
        inv_txt = "🎒 <b>내 인벤토리</b>\n━━━━━━━━━━━━━━\n"
        # 티어별 정렬 누락 해결 (V11.3 로직 통합)
        for tier, minerals in MINERALS.items():
            inv_txt += f"<b>[{tier}]</b>\n"
            has_item = False
            for m_name, price in minerals.items():
                count = u["inv"].get(m_name, 0)
                if count > 0:
                    inv_txt += f"▫️ {m_name}: {count}개\n"
                    has_item = True
            if not has_item: inv_txt += "보유 광물 없음\n"
            inv_txt += "━━━━━━━━━━━━━━\n"
        return await update.message.reply_text(inv_txt, parse_mode='HTML')

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
            if u["money"] < amt: return await update.message.reply_text("❌ 잔액 부족")
            u["money"] -= amt; room_betting_status[cid] = True; save_db()
            c_game = db["game_count"]
            await update.message.reply_text(f"✅ <b>{c_game}회차 배팅 완료</b> 금액: {amt:,} G", parse_mode='HTML')
            await asyncio.sleep(30); await update.message.reply_text(f"🚫 <b>{c_game}회차 마감</b>", parse_mode='HTML')
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
    # drop_pending_updates: 봇이 꺼진 동안 쌓인 명령어 무시 (켜기 전 에러 방지 핵심)
    app_bot.run_polling(drop_pending_updates=True)
