import logging, time, random, os, json, re
from flask import Flask
from threading import Thread
from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler

# --- [1. 서버 설정 & Render 포트 해결] ---
app = Flask('')
@app.route('/')
def home(): return "G-COIN BOT Online"

def run():
    # Render는 환경 변수 PORT(기본 10000)를 사용해야 에러가 나지 않습니다.
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive(): Thread(target=run).start()

# --- [2. 설정 및 데이터 소스] ---
TOKEN = "8771125252:AAFbKHLcDM2KhLR3MIp6ZGOnFQQWlIQUIlc"
ADMIN_ID = "EJ1427"
DATA_FILE = "data.json"

# 스크린샷과 같은 이미지를 위한 기본 경로 (사용자님 GitHub 경로에 맞춰 수정 가능)
IMG_BASE = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/cards/"

user_data = {}
baccarat_history = []
current_round = 0

ORES = {
    "diam1": {"n":"다이아몬드", "p":3000000, "t":1, "e":"💎"},
    "ori": {"n":"오리하르콘", "p":2500000, "t":1, "e":"🔱"},
    "ruby": {"n":"루비", "p":500000, "t":2, "e":"🍎"},
    "gold": {"n":"금광석", "p":100000, "t":4, "e":"🥇"},
    "stone": {"n":"일반돌", "p":5000, "t":5, "e":"🪨"}
}

# 카드 덱 설정
SUITS = ["S", "H", "D", "C"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
DECK_ORIGIN = [{"rank": r, "value": min(i+1, 10) if r not in ["10", "J", "Q", "K"] else 0} for s in SUITS for i, r in enumerate(RANKS)]

# --- [3. 데이터 관리 함수] ---
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"users": user_data, "history": baccarat_history, "round": current_round}, f, ensure_ascii=False)

def load_data():
    global user_data, baccarat_history, current_round
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                user_data, baccarat_history, current_round = data.get("users", {}), data.get("history", []), data.get("round", 0)
        except: pass

def draw_card(deck):
    card = random.choice(deck); deck.remove(card); return card, deck

# --- [4. 판매 버튼 콜백] ---
def button_callback(update, context):
    query = update.callback_query
    uid = query.from_user.username
    if uid not in user_data: return
    user, data = user_data[uid], query.data
    total_gain = 0
    if data == "sell_all":
        for k in ORES: total_gain += user['inv'].get(k, 0) * ORES[k]['p']; user['inv'][k] = 0
    elif data.startswith("sell_tier_"):
        t = int(data.split("_")[2])
        for k, v in ORES.items():
            if v['t'] == t: total_gain += user['inv'].get(k, 0) * v['p']; user['inv'][k] = 0
    
    if total_gain == 0: return query.answer("판매할 광물이 없습니다!", show_alert=True)
    user['money'] += total_gain
    save_data()
    query.edit_message_text(f"💰 판매 완료! **+{total_gain:,} G**\n💵 현재 잔액: {user['money']:,} G", parse_mode=ParseMode.MARKDOWN)

# --- [5. 메인 핸들러] ---
def handle_message(update, context):
    global current_round, baccarat_history
    if not update.message or not update.message.text: return
    uid = update.message.from_user.username
    if not uid: return
    text = update.message.text.strip()

    if text == "!가입":
        if uid in user_data: return update.message.reply_text("이미 가입된 계정입니다.")
        user_data[uid] = {'money': 100000, 'inv': {k: 0 for k in ORES}, 'last_mine': 0, 'dur': 100, 'mine_count': 0}
        save_data(); return update.message.reply_text("🎊 가입 완료! 10만 G 지급.")

    if uid not in user_data: return
    user = user_data[uid]

    # [바카라 - 스크린샷 고퀄리티 연출 모드]
    bet_match = re.match(r"^!(플|뱅|타이)\s*([0-9,]+)", text)
    if bet_match:
        cmd, amt_val = bet_match.group(1), int(bet_match.group(2).replace(",", ""))
        if amt_val > user['money']: return update.message.reply_text("❌ 잔액이 부족합니다.")

        current_round += 1
        bet_type = "P" if cmd == "플" else ("B" if cmd == "뱅" else "T")
        
        # 카드 드로우
        temp_deck = list(DECK_ORIGIN)
        p1, temp_deck = draw_card(temp_deck); p2, temp_deck = draw_card(temp_deck)
        b1, temp_deck = draw_card(temp_deck); b2, temp_deck = draw_card(temp_deck)
        pv, bv = (p1['value'] + p2['value']) % 10, (b1['value'] + b2['value']) % 10

        # 연출 시작
        update.message.reply_text(f"✨ **{current_round}회차 결과 발표 !**", parse_mode=ParseMode.MARKDOWN)
        time.sleep(0.5)

        # 1. 플레이어 카드 공개
        update.message.reply_photo(photo=f"{IMG_BASE}p_open.png", caption="**플레이어 카드 공개!**", parse_mode=ParseMode.MARKDOWN)
        time.sleep(0.7)

        # 2. 뱅커 카드 공개
        update.message.reply_photo(photo=f"{IMG_BASE}b_open.png", caption="**뱅커 카드 공개!**", parse_mode=ParseMode.MARKDOWN)
        time.sleep(0.7)

        # 3. 결과 판정 및 배너 송출
        result = "P" if pv > bv else ("B" if bv > pv else "T")
        res_name = "플레이어" if result == "P" else ("뱅커" if result == "B" else "타이")
        res_img = "p" if result == "P" else ("b" if result == "B" else "t")

        update.message.reply_photo(
            photo=f"{IMG_BASE}banner_{res_img}.png", 
            caption=f"플레이어 : {pv}\n뱅커 : {bv}\n\n**{res_name} 승 !**", 
            parse_mode=ParseMode.MARKDOWN
        )
        
        # 4. 적중자 발표
        user['money'] -= amt_val
        if bet_type == result:
            rate = 2.0 if result == "P" else (1.85 if result == "B" else 6.0)
            win_amt = int(amt_val * rate)
            user['money'] += win_amt
            update.message.reply_text(f"🏆 **적중자**\n- @{uid} +{win_amt:,}코인", parse_mode=ParseMode.MARKDOWN)
        else:
            update.message.reply_text("📉 이번 회차는 적중하지 못했습니다.")

        baccarat_history.append(result)
        if len(baccarat_history) > 45: baccarat_history.pop(0)

        # 5. 그림장 송출 (이모지 격자 방식)
        COLS = 15; grid = [["⚪" for _ in range(COLS)] for _ in range(3)]
        for i, res in enumerate(baccarat_history[-45:]):
            grid[i//COLS][i%COLS] = "🔴" if res == "P" else ("🔵" if res == "B" else "🟢")
        grid_text = "\n".join(["".join(r) for r in grid])
        update.message.reply_text(f"`{grid_text}`\n\n**바카라 그림장**", parse_mode=ParseMode.MARKDOWN)

        if current_round >= 50: current_round = 0; baccarat_history = []
        save_data(); return

    # [그 외 광산 명령어]
    elif text == "!채광":
        # (중략: 요청하신 형식대로 획득/가치/내구도/횟수 출력 로직 포함)
        now = time.time()
        if now - user.get('last_mine', 0) < 40: return update.message.reply_text("⏱ 쿨타임 중...")
        user['last_mine'] = now; res_key = random.choice(list(ORES.keys()))
        user['inv'][res_key] += 1; user['dur'] -= 1; user['mine_count'] = user.get('mine_count', 0) + 1
        save_data()
        return update.message.reply_text(f"⛏ **채광 완료 !**\n획득: {ORES[res_key]['e']} {ORES[res_key]['n']}\n가치: {ORES[res_key]['p']:,}\n내구도: {user['dur']}/100\n채광횟수: {user['mine_count']}회", parse_mode=ParseMode.MARKDOWN)

    elif text == "!인벤":
        msg = "🎒 **아이템 가방**\n"
        for k, v in ORES.items():
            cnt = user['inv'].get(k, 0)
            if cnt > 0: msg += f"{v['e']} {v['n']}: x{cnt} [ {v['p']*cnt:,} G ]\n"
        return update.message.reply_text(msg if "x" in msg else "가방이 비었습니다.", parse_mode=ParseMode.MARKDOWN)

    elif text == "!판매":
        kb = [[InlineKeyboardButton(f"{i}티어", callback_data=f"sell_tier_{i}") for i in range(1, 4)],
              [InlineKeyboardButton(f"{i}티어", callback_data=f"sell_tier_{i}") for i in range(4, 6)],
              [InlineKeyboardButton("전체판매", callback_data="sell_all")]]
        return update.message.reply_text("💰 **판매할 등급을 선택하세요.**", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)

# --- [6. 실행] ---
if __name__ == '__main__':
    load_data(); keep_alive()
    updater = Updater(TOKEN, use_context=True)
    updater.dispatcher.add_handler(MessageHandler(Filters.text, handle_message))
    updater.dispatcher.add_handler(CallbackQueryHandler(button_callback))
    updater.start_polling(); updater.idle()
