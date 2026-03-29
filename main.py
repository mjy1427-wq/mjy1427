import logging, time, random, os, json, re
from flask import Flask
from threading import Thread, Lock
from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler

# 로그 설정 (Render 로그창에서 에러 확인 가능)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask('')
@app.route('/')
def home(): return "G-COIN BOT ONLINE"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
def keep_alive(): Thread(target=run, daemon=True).start()

TOKEN = "8771125252:AAFbKHLcDM2KhLR3MIp6ZGOnFQQWlIQUIlc"
ADMIN_ID = "EJ1427"
DATA_FILE = "data.json"
IMG_BASE = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/cards/"

user_data, baccarat_history, current_round = {}, [], 0
betting_pool, is_betting_active, game_lock = {}, False, Lock()

# 곡괭이 및 광물 13종 데이터 (생략 없이 전체 포함)
PICKS = {
    "Wood": {"p": 1000000, "d": 100}, "Stone": {"p": 5000000, "d": 300},
    "Iron": {"p": 15000000, "d": 500}, "Gold": {"p": 50000000, "d": 1000},
    "Diamond": {"p": 250000000, "d": 5000}, "Netherite": {"p": 1000000000, "d": 10000}
}
ORES = {
    "nether": {"n":"네더라이트", "p":10000000, "t":1, "e":"🌑", "w":1},
    "diam1": {"n":"다이아몬드", "p":3000000, "t":1, "e":"💎", "w":2},
    "ori": {"n":"오리하르콘", "p":2500000, "t":1, "e":"🔱", "w":3},
    "emeral": {"n":"에메랄드", "p":1500000, "t":2, "e":"🍏", "w":5},
    "ruby": {"n":"루비", "p":500000, "t":2, "e":"🍎", "w":7},
    "saphi": {"n":"사파이어", "p":400000, "t":2, "e":"🔷", "w":8},
    "gold": {"n":"금광석", "p":100000, "t":3, "e":"🥇", "w":12},
    "plat": {"n":"백금", "p":80000, "t":3, "e":"🏐", "w":15},
    "silver": {"n":"은광석", "p":50000, "t":4, "e":"🥈", "w":20},
    "copper": {"n":"구리", "p":30000, "t":4, "e":"🥉", "w":25},
    "iron": {"n":"철광석", "p":20000, "t":4, "e":"⛓", "w":30},
    "coal": {"n":"석탄", "p":10000, "t":5, "e":"🔌", "w":50},
    "stone": {"n":"일반돌", "p":5000, "t":5, "e":"🪨", "w":100}
}

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

# --- [바카라 엔진] ---
def start_baccarat(update, context):
    global is_betting_active, current_round, betting_pool, baccarat_history
    with game_lock:
        if is_betting_active: return
        is_betting_active = True
    
    cid = update.effective_chat.id
    context.bot.send_message(cid, "🎰 **배팅 시작! (20초 후 마감)**\n`!플 / !뱅 / !타이 [금액]`", parse_mode=ParseMode.MARKDOWN)
    time.sleep(20)
    
    context.bot.send_message(cid, "🚫 **배팅 마감! 결과를 계산 중입니다...**")
    time.sleep(4)
    
    current_round += 1
    pv, bv = random.randint(0, 9), random.randint(0, 9)
    context.bot.send_message(cid, f"✨ **{current_round}회차 결과 발표 !**")
    
    # 카드 이미지 연출
    time.sleep(0.5)
    context.bot.send_photo(cid, photo=f"{IMG_BASE}p_open.png", caption="**플레이어 초기 카드 공개!**")
    time.sleep(0.5)
    context.bot.send_photo(cid, photo=f"{IMG_BASE}b_open.png", caption="**뱅커 초기 카드 공개!**")
    
    # 추가 카드 룰 (간소화하여 확실히 작동하게 함)
    if pv <= 5:
        pv = (pv + random.randint(0, 9)) % 10
        time.sleep(0.7)
        context.bot.send_photo(cid, photo=f"{IMG_BASE}p_add.png", caption="🃏 플레이어 **추가 카드 오픈!**")
    if bv <= 5:
        bv = (bv + random.randint(0, 9)) % 10
        time.sleep(0.7)
        context.bot.send_photo(cid, photo=f"{IMG_BASE}b_add.png", caption="🃏 뱅커 **추가 카드 오픈!**")

    res = "P" if pv > bv else ("B" if bv > pv else "T")
    time.sleep(1)
    context.bot.send_photo(cid, photo=f"{IMG_BASE}banner_{res.lower()}.png", caption=f"플레이어: {pv} / 뱅커: {bv}\n\n**{res} 승리!**")
    
    # 정산 로직
    for u, (bt, amt) in betting_pool.items():
        if bt == res:
            rate = 2.0 if res == "P" else (1.85 if res == "B" else 6.0)
            user_data[u]['money'] += int(amt * rate)
    
    baccarat_history.append(res)
    if len(baccarat_history) > 45: baccarat_history.pop(0)
    grid = [["⚪" for _ in range(15)] for _ in range(3)]
    for i, r in enumerate(baccarat_history): grid[i//15][i%15] = "🔴" if r=="P" else "🔵" if r=="B" else "🟢"
    grid_txt = "\n".join(["".join(row) for row in grid])
    context.bot.send_message(cid, f"`{grid_txt}`\n**바카라 그림장**", parse_mode=ParseMode.MARKDOWN)

    betting_pool.clear(); is_betting_active = False; save_data()

# --- [메인 핸들러] ---
def handle_message(update, context):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    
    # 명령어는 무조건 "!"로 시작
    if not text.startswith("!"): return
    
    uid = update.message.from_user.username
    if not uid: return
    
    # 명령어 분리
    parts = text[1:].split()
    cmd = parts[0]

    # [1] 가입
    if cmd == "가입":
        if uid in user_data: return update.message.reply_text("이미 가입되어 있습니다.")
        user_data[uid] = {'money': 100000, 'pick': 'Wood', 'dur': 100, 'inv': {k: 0 for k in ORES}, 'last_mine': 0}
        save_data(); return update.message.reply_text("🎊 가입 완료! 10만 G가 지급되었습니다.")

    if uid not in user_data: return
    user = user_data[uid]

    # [2] 관리자 권한 (EJ1427)
    if uid == ADMIN_ID:
        if cmd == "돈지급":
            try:
                target = parts[1].replace("@", "")
                amt = int(parts[2])
                user_data[target]['money'] += amt
                save_data(); return update.message.reply_text(f"💰 @{target}님께 {amt:,}G 지급 완료!")
            except: pass
        if cmd == "초기화":
            try:
                target = parts[1].replace("@", "")
                if target in user_data: del user_data[target]
                save_data(); return update.message.reply_text(f"🧹 @{target} 데이터 초기화 완료!")
            except: pass

    # [3] 게임/상점 명령어
    if cmd == "상점":
        txt = "⛏ **곡괭이 상점**\n──────────────\n"
        for k, v in PICKS.items(): txt += f"**{k}** — {v['p']:,} 코인\n내구도: {v['d']:,}\n\n"
        btns = [[InlineKeyboardButton(f"💰 {k} 구매", callback_data=f"buy_{k}")] for k in PICKS.keys()]
        return update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(btns), parse_mode=ParseMode.MARKDOWN)

    if cmd == "명령어":
        return update.message.reply_text("📜 **명령어 목록**\n!가입 / !채광 / !상점 / !인벤 / !판매 / !내정보\n**바카라**: !플 금액 / !뱅 금액 / !타이 금액", parse_mode=ParseMode.MARKDOWN)

    if cmd == "채광":
        keys, w = list(ORES.keys()), [v['w'] for v in ORES.values()]
        res = random.choices(keys, weights=w, k=1)[0]
        user['inv'][res] += 1; save_data()
        return update.message.reply_text(f"⛏ **채광 성공!**\n{ORES[res]['e']} {ORES[res]['n']} 획득!")

    # [4] 바카라 배팅 인식 (이 부분이 핵심!)
    if cmd in ["플", "뱅", "타이"]:
        try:
            bt = "P" if cmd == "플" else "B" if cmd == "뱅" else "T"
            amt = int(parts[1].replace(",", ""))
            if user['money'] < amt: return update.message.reply_text("❌ 자산이 부족합니다!")
            user['money'] -= amt; betting_pool[uid] = (bt, amt)
            update.message.reply_text(f"✅ {amt:,}G 배팅 완료! (대상: {cmd})")
            if not is_betting_active: Thread(target=start_baccarat, args=(update, context)).start()
        except:
            update.message.reply_text("⚠️ 형식이 틀렸습니다! 예: `!플 10000`")

def button_callback(update, context):
    query = update.callback_query; uid = query.from_user.username
    if uid not in user_data: return
    if query.data.startswith("buy_"):
        pk = query.data.split("_")[1]
        if user_data[uid]['money'] < PICKS[pk]['p']: return query.answer("❌ 코인 부족!", show_alert=True)
        user_data[uid]['money'] -= PICKS[pk]['p']
        user_data[uid]['pick'], user_data[uid]['dur'] = pk, PICKS[pk]['d']
        save_data(); query.answer(f"✅ {pk} 구매 완료!", show_alert=True)

if __name__ == '__main__':
    load_data(); keep_alive()
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    # 단톡방(Filters.group)에서도 메시지를 확실히 읽도록 설정
    dp.add_handler(MessageHandler(Filters.text | Filters.group, handle_message))
    dp.add_handler(CallbackQueryHandler(button_callback))
    updater.start_polling()
    updater.idle()
