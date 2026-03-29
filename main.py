import logging, time, random, os, json, re
from flask import Flask
from threading import Thread
from telegram import ParseMode
from telegram.ext import Updater, MessageHandler, Filters

# --- [1. 서버 유지 및 포트 설정] ---
app = Flask('')
@app.route('/')
def home(): return "G-COIN BOT Online"

def run():
    # Render의 포트 문제를 해결하기 위한 환경변수 설정
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive(): 
    t = Thread(target=run)
    t.start()

# --- [2. 설정 및 데이터 소스] ---
TOKEN = "8771125252:AAFbKHLcDM2KhLR3MIp6ZGOnFQQWlIQUIlc"
ADMIN_ID = "EJ1427"
DATA_FILE = "data.json"

# 이미지 경로 설정 (GitHub 주소 확인 필요)
IMG_BASE = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/cards/"
BANNER_URL = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/cards/banner_"

user_data = {}
baccarat_history = []
current_round = 0

# 광물 정보 (가격 및 아이콘)
ORES = {
    "diam1": {"n":"다이아몬드", "p":3000000, "e":"💎"},
    "ori": {"n":"오리하르콘", "p":2500000, "e":"🔱"},
    "ruby": {"n":"루비", "p":500000, "e":"🍎"},
    "gold": {"n":"금광석", "p":100000, "e":"🥇"},
    "stone": {"n":"일반돌", "p":5000, "e":"🪨"}
}

# 바카라 카드 덱
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
                user_data = data.get("users", {})
                baccarat_history = data.get("history", [])
                current_round = data.get("round", 0)
        except: pass

def draw_card(deck):
    card = random.choice(deck); deck.remove(card); return card, deck

# --- [4. 메인 메시지 핸들러] ---
def handle_message(update, context):
    global current_round, baccarat_history
    if not update.message or not update.message.text: return
    uid = update.message.from_user.username
    if not uid: return
    text = update.message.text.strip()

    # [가입]
    if text == "!가입":
        if uid in user_data: return update.message.reply_text("이미 가입된 계정입니다.")
        user_data[uid] = {'money': 100000, 'inv': {k: 0 for k in ORES}, 'last_mine': 0}
        save_data()
        return update.message.reply_text("🎊 가입 완료! 10만 G가 지급되었습니다.")

    if uid not in user_data: return
    user = user_data[uid]

    # [바카라 배팅 - 요청하신 고퀄리티 연출]
    bet_match = re.match(r"^!(플|뱅|타이)\s*([0-9,]+)", text)
    if bet_match:
        cmd, amt_val = bet_match.group(1), int(bet_match.group(2).replace(",", ""))
        if amt_val > user['money'] or amt_val < 0: 
            return update.message.reply_text(f"❌ 잔액 부족 (현재: {user['money']:,} G)")

        current_round += 1
        bet_type = "P" if cmd == "플" else ("B" if cmd == "뱅" else "T")
        
        # 카드 계산
        temp_deck = list(DECK_ORIGIN)
        p1, temp_deck = draw_card(temp_deck); p2, temp_deck = draw_card(temp_deck)
        b1, temp_deck = draw_card(temp_deck); b2, temp_deck = draw_card(temp_deck)
        pv, bv = (p1['value'] + p2['value']) % 10, (b1['value'] + b2['value']) % 10

        # 연출 1: 결과 발표 알림
        update.message.reply_text(f"✨ **{current_round}회차 결과 발표 !**", parse_mode=ParseMode.MARKDOWN)
        time.sleep(0.5)

        # 연출 2: 플레이어 카드 공개
        update.message.reply_photo(photo=f"{IMG_BASE}p_open.png", caption="**플레이어 카드 공개!**", parse_mode=ParseMode.MARKDOWN)
        time.sleep(0.7)

        # 연출 3: 뱅커 카드 공개
        update.message.reply_photo(photo=f"{IMG_BASE}b_open.png", caption="**뱅커 카드 공개!**", parse_mode=ParseMode.MARKDOWN)
        time.sleep(0.7)

        # 결과 계산
        result = "P" if pv > bv else ("B" if bv > pv else "T")
        res_name = "플레이어" if result == "P" else ("뱅커" if result == "B" else "타이")
        res_img = "p" if result == "P" else ("b" if result == "B" else "t")

        # 연출 4: 승리 배너 및 점수
        update.message.reply_photo(
            photo=f"{BANNER_URL}{res_img}.png", 
            caption=f"플레이어 : {pv}\n뱅커 : {bv}\n\n**{res_name} 승 !**", 
            parse_mode=ParseMode.MARKDOWN
        )
        
        # 연출 5: 적중자 명단
        user['money'] -= amt_val
        if bet_type == result:
            rate = 2.0 if result == "P" else (1.85 if result == "B" else 6.0)
            win_amt = int(amt_val * rate)
            user['money'] += win_amt
            update.message.reply_text(f"🏆 **적중자**\n- @{uid} +{win_amt:,}코인", parse_mode=ParseMode.MARKDOWN)
        else:
            update.message.reply_text("📉 아쉽게도 적중하지 못했습니다.")

        baccarat_history.append(result)
        if len(baccarat_history) > 45: baccarat_history.pop(0)

        # 연출 6: 그림장 출력
        COLS = 15; grid = [["⚪" for _ in range(COLS)] for _ in range(3)]
        for i, res in enumerate(baccarat_history[-45:]):
            grid[i//COLS][i%COLS] = "🔴" if res == "P" else ("🔵" if res == "B" else "🟢")
        
        grid_text = "\n".join(["".join(r) for r in grid])
        update.message.reply_text(f"`{grid_text}`\n\n**바카라 그림장**", parse_mode=ParseMode.MARKDOWN)

        if current_round >= 50: 
            current_round = 0
            baccarat_history = []
            update.message.reply_text("🔄 50회차가 종료되어 회차와 그림장을 리셋합니다.")
        
        save_data(); return

    # [그 외 모든 명령어들]
    if text == "!채광":
        now = time.time()
        if now - user.get('last_mine', 0) < 40:
            return update.message.reply_text(f"⏱ {int(40-(now-user['last_mine']))}초 후 다시 가능!")
        user['last_mine'] = now
        res = random.choice(list(ORES.keys()))
        user['inv'][res] += 1
        save_data()
        return update.message.reply_text(f"⛏ {ORES[res]['e']} {ORES[res]['n']}을(를) 캤습니다!")

    elif text == "!인벤":
        msg = "🎒 **아이템 가방**\n"
        has_item = False
        for k, v in ORES.items():
            if user['inv'].get(k, 0) > 0:
                msg += f"{v['e']} {v['n']}: {user['inv'][k]}개\n"
                has_item = True
        return update.message.reply_text(msg if has_item else "🎒 가방이 텅 비어있습니다.")

    elif text == "!판매":
        total = sum(user['inv'].get(k, 0) * ORES[k]['p'] for k in ORES)
        if total == 0: return update.message.reply_text("판매할 광물이 없습니다.")
        user['money'] += total
        for k in ORES: user['inv'][k] = 0
        save_data()
        return update.message.reply_text(f"💰 모든 광물을 판매하여 {total:,} G를 벌었습니다!")

    elif text == "!내정보":
        return update.message.reply_text(f"👤 **사용자**: @{uid}\n💵 **보유 자산**: {user['money']:,} G")

    elif text == "!랭킹":
        rank = sorted(user_data.items(), key=lambda x: x[1]['money'], reverse=True)[:10]
        msg = "🏆 **자산가 순위**\n"
        for i, (name, data) in enumerate(rank, 1):
            msg += f"{i}위. @{name}: {data['money']:,} G\n"
        return update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    elif text == "!명령어":
        return update.message.reply_text(
            "📜 **명령어 목록**\n"
            "• !가입 / !내정보 / !랭킹\n"
            "• !채광 / !인벤 / !판매\n"
            "• !플 [금액] / !뱅 [금액] / !타이 [금액]"
        )

# --- [5. 봇 실행] ---
if __name__ == '__main__':
    load_data()
    keep_alive() # 포트 문제 해결 서버 시작
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    
    print("Bot is running...")
    updater.start_polling()
    updater.idle()
