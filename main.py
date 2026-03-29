import logging, time, random, os, json, re
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler

# --- [1. 서버 유지 및 포트 설정 (Render 전용)] ---
app = Flask('')
@app.route('/')
def home(): return "G-COIN BOT Online"

def run():
    # Render는 기본적으로 10000번 포트 혹은 환경 변수 PORT를 사용합니다.
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- [2. 설정 및 데이터베이스] ---
TOKEN = "8771125252:AAFbKHLcDM2KhLR3MIp6ZGOnFQQWlIQUIlc"
ADMIN_ID = "EJ1427"
DATA_FILE = "data.json"
IMG_BASE = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/cards/"

user_data = {}
baccarat_history = []
current_round = 0

# 광물 정보
ORES = {
    "diam1": {"n":"다이아몬드", "p":3000000, "t":1, "c":1.0, "e":"💎"},
    "ori": {"n":"오리하르콘", "p":2500000, "t":1, "c":2.0, "e":"🔱"},
    "ruby": {"n":"루비", "p":500000, "t":2, "c":5.0, "e":"🍎"},
    "plat": {"n":"백금광석", "p":450000, "t":2, "c":7.0, "e":"⚪"},
    "sapph": {"n":"사파이어", "p":400000, "t":3, "c":15.0, "e":"🌌"},
    "emera": {"n":"에메랄드", "p":250000, "t":3, "c":20.0, "e":"🧪"},
    "gold": {"n":"금광석", "p":100000, "t":4, "c":25.0, "e":"🥇"},
    "silv": {"n":"은광석", "p":50000, "t":4, "c":25.0, "e":"🥈"},
    "coal": {"n":"석탄", "p":10000, "t":5, "c":35.0, "e":"🌑"},
    "stone": {"n":"일반돌", "p":5000, "t":5, "c":35.0, "e":"🪨"}
}

# 바카라 카드 덱 구성
SUITS = ["S", "H", "D", "C"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
DECK_ORIGIN = [{"rank": r, "value": min(i+1, 10) if r not in ["10", "J", "Q", "K"] else 0} for s in SUITS for i, r in enumerate(RANKS)]

# --- [3. 핵심 기능 함수] ---
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"users": user_data, "history": baccarat_history, "round": current_round}, f, ensure_ascii=False)

def load_data():
    global user_data, baccarat_history, current_round
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                user_data = data.get("users", {})
                baccarat_history = data.get("history", [])
                current_round = data.get("round", 0)
        except: pass

def draw_card(deck):
    card = random.choice(deck); deck.remove(card); return card, deck

# --- [4. 메시지 핸들러] ---
def handle_message(update, context):
    global current_round, baccarat_history
    if not update.message or not update.message.text: return
    uid = update.message.from_user.username
    if not uid: return
    text = update.message.text.strip()

    # 가입
    if text == "!가입":
        if uid in user_data: return update.message.reply_text("이미 가입된 계정입니다.")
        user_data[uid] = {'money': 100000, 'inv': {k: 0 for k in ORES}, 'last_mine': 0}
        save_data()
        return update.message.reply_text("🎊 가입 완료! 10만 G가 지급되었습니다.")

    if uid not in user_data: return

    user = user_data[uid]

    # [바카라 배팅 - 무제한 & 대형 이미지 연출]
    bet_match = re.match(r"^!(플|뱅|타이)\s*([0-9,]+)", text)
    if bet_match:
        cmd = bet_match.group(1)
        amt = int(bet_match.group(2).replace(",", ""))
        
        if amt < 0: return
        if amt > user['money']: return update.message.reply_text(f"❌ 잔액 부족 (현재: {user['money']:,} G)")

        bet_type = "P" if cmd == "플" else ("B" if cmd == "뱅" else "T")
        current_round += 1
        
        deck = list(DECK_ORIGIN)
        p1, deck = draw_card(deck); p2, deck = draw_card(deck)
        b1, deck = draw_card(deck); b2, deck = draw_card(deck)
        pv, bv = (p1['value'] + p2['value']) % 10, (b1['value'] + b2['value']) % 10

        # 카드 대형 이미지 연출
        update.message.reply_photo(photo=f"{IMG_BASE}p_open.png", caption=f"🃏 [ {current_round}/45 회차 ]\n플레이어 점수: {pv}")
        time.sleep(0.6)
        update.message.reply_photo(photo=f"{IMG_BASE}b_open.png", caption=f"뱅커 점수: {bv}")
        
        result = "P" if pv > bv else ("B" if bv > pv else "T")
        user['money'] -= amt

        if bet_type == result:
            rate = 2.0 if result == "P" else (1.85 if result == "B" else 6.0)
            win = int(amt * rate); user['money'] += win
            msg = f"✅ 승리! +{win:,} G"
        else:
            msg = f"❌ 패배.. -{amt:,} G"
        
        baccarat_history.append(result)
        if len(baccarat_history) > 45: baccarat_history.pop(0)
        
        save_data()
        return update.message.reply_text(f"🎰 결과: {pv} vs {bv}\n{msg}\n💵 잔액: {user['money']:,} G")

    # 기타 명령어 (채광, 인벤, 판매 등)
    if text == "!채광":
        now = time.time()
        if now - user['last_mine'] < 40: return update.message.reply_text("⏱ 채광 대기 중...")
        user['last_mine'] = now
        res_key = random.choices(list(ORES.keys()), weights=[v.get('c', 10) for v in ORES.values()])[0]
        user['inv'][res_key] += 1
        save_data()
        return update.message.reply_text(f"⛏ {ORES[res_key]['e']} {ORES[res_key]['n']} 획득!")

    elif text == "!인벤":
        msg = "🎒 가방\n"
        for k, v in ORES.items():
            if user['inv'][k] > 0: msg += f"{v['e']} {v['n']}: {user['inv'][k]}개\n"
        return update.message.reply_text(msg if "개" in msg else "🎒 가방이 비어있습니다.")

    elif text == "!판매":
        total = sum(user['inv'][k] * ORES[k]['p'] for k in ORES)
        if total == 0: return update.message.reply_text("판매할 광물이 없습니다.")
        user['money'] += total
        for k in ORES: user['inv'][k] = 0
        save_data()
        return update.message.reply_text(f"💰 전체 판매 완료: +{total:,} G")

    elif text == "!내정보":
        return update.message.reply_text(f"👤 @{uid}\n💵 자산: {user['money']:,} G")

    elif text == "!바카라":
        return update.message.reply_text(f"📊 최근 기록: {baccarat_history[-15:]}")

# --- [5. 실행] ---
if __name__ == '__main__':
    load_data()
    keep_alive() # Render 포트 문제를 해결한 서버 실행
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    updater.start_polling()
    updater.idle()
