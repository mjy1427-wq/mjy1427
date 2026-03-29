import logging, time, random, os, json, re
from flask import Flask
from threading import Thread, Lock
from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler

# --- [1. 서버 및 데이터 설정] ---
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

# 곡괭이 데이터
PICKS = {
    "Wood": {"p": 1000000, "d": 100}, "Stone": {"p": 5000000, "d": 300},
    "Iron": {"p": 15000000, "d": 500}, "Gold": {"p": 50000000, "d": 1000},
    "Diamond": {"p": 250000000, "d": 5000}, "Netherite": {"p": 1000000000, "d": 10000}
}

# 광물 13종 데이터 (티어/가격/아이콘/확률 가중치)
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
                user_data, baccarat_history, current_round = data.get("users", {}), data.get("history", []), data.get("round", 0)
        except: pass

# --- [2. 바카라 엔진 (타이머/연출/추가카드)] ---
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
    p_val, b_val = random.randint(0, 9), random.randint(0, 9)
    context.bot.send_message(cid, f"✨ **{current_round}회차 결과 발표 !**")
    time.sleep(0.5)
    context.bot.send_photo(cid, photo=f"{IMG_BASE}p_open.png", caption="**플레이어 초기 카드 공개!**")
    time.sleep(0.5)
    context.bot.send_photo(cid, photo=f"{IMG_BASE}b_open.png", caption="**뱅커 초기 카드 공개!**")
    time.sleep(1)

    # 5점 이하 추가 카드 룰
    if p_val <= 5:
        p_val = (p_val + random.randint(0, 9)) % 10
        context.bot.send_photo(cid, photo=f"{IMG_BASE}p_add.png", caption="🃏 플레이어 5점 이하 **추가 카드 오픈!**")
        time.sleep(0.7)
    if b_val <= 5:
        b_val = (b_val + random.randint(0, 9)) % 10
        context.bot.send_photo(cid, photo=f"{IMG_BASE}b_add.png", caption="🃏 뱅커 5점 이하 **추가 카드 오픈!**")
        time.sleep(0.7)

    result = "P" if p_val > b_val else ("B" if b_val > p_val else "T")
    context.bot.send_photo(cid, photo=f"{IMG_BASE}banner_{result.lower()}.png", 
                           caption=f"플레이어: {p_val} / 뱅커: {b_val}\n\n**{'플레이어' if result=='P' else '뱅커' if result=='B' else '타이'} 승 !**")
    
    # 정산 및 그림장 (생략 없이 모두 포함)
    for uid, (bt, amt) in betting_pool.items():
        if bt == result:
            rate = 2.0 if result == "P" else (1.85 if result == "B" else 6.0)
            user_data[uid]['money'] += int(amt * rate)
    
    baccarat_history.append(result)
    if len(baccarat_history) > 45: baccarat_history.pop(0)
    grid = [["⚪" for _ in range(15)] for _ in range(3)]
    for i, r in enumerate(baccarat_history): grid[i//15][i%15] = "🔴" if r=="P" else "🔵" if r=="B" else "🟢"
    grid_txt = "\n".join(["".join(row) for row in grid])
    context.bot.send_message(cid, f"`{grid_txt}`\n**바카라 그림장**", parse_mode=ParseMode.MARKDOWN)

    betting_pool.clear(); is_betting_active = False; save_data()

# --- [3. 메시지 핸들러 (명령어 통합)] ---
def handle_message(update, context):
    uid = update.message.from_user.username
    if not uid or not update.message.text: return
    text = update.message.text.strip()

    # [관리자 EJ1427 전용]
    if uid == ADMIN_ID:
        if text.startswith("!돈지급"):
            try:
                _, target, amt = text.split(); target = target.replace("@", "")
                user_data[target]['money'] += int(amt)
                save_data(); return update.message.reply_text(f"💰 @{target}님께 {int(amt):,}G 지급 완료!")
            except: pass
        if text.startswith("!초기화"):
            try:
                target = text.split()[1].replace("@", "")
                if target in user_data: del user_data[target]
                save_data(); return update.message.reply_text(f"🧹 @{target} 초기화 완료!")
            except: pass

    # [일반 명령어]
    if text == "!가입":
        if uid in user_data: return update.message.reply_text("이미 가입된 상태입니다.")
        user_data[uid] = {'money': 100000, 'pick': 'Wood', 'dur': 100, 'inv': {k: 0 for k in ORES}, 'last_mine': 0}
        save_data(); return update.message.reply_text("🎊 가입 완료! 10만 G 지급.")

    if uid not in user_data: return
    user = user_data[uid]

    if text == "!상점":
        shop_txt = "⛏ **곡괭이 상점**\n──────────────\n"
        for k, v in PICKS.items(): shop_txt += f"**{k}** — {v['p']:,} 코인\n내구도: {v['d']:,}\n\n"
        btns = [[InlineKeyboardButton(f"💰 {k} 구매", callback_data=f"buy_{k}")] for k in PICKS.keys()]
        return update.message.reply_text(shop_txt, reply_markup=InlineKeyboardMarkup(btns), parse_mode=ParseMode.MARKDOWN)

    elif text == "!명령어":
        return update.message.reply_text("📜 **명령어 목록**\n가입/내정보/랭킹/채광/인벤/판매/**상점**\n!플 !뱅 !타이 [금액]", parse_mode=ParseMode.MARKDOWN)

    elif text == "!채광":
        # 가중치 기반 채광 로직
        res_list = list(ORES.keys())
        weights = [v['w'] for v in ORES.values()]
        res_key = random.choices(res_list, weights=weights, k=1)[0]
        user['inv'][res_key] += 1
        save_data(); return update.message.reply_text(f"⛏ **채광 완료!**\n획득: {ORES[res_key]['e']} {ORES[res_key]['n']}")

    # 바카라 배팅
    m = re.match(r"^!(플|뱅|타이)\s*([0-9,]+)", text)
    if m:
        bt, a = ("P" if m.group(1)=="플" else "B" if m.group(1)=="뱅" else "T"), int(m.group(2).replace(",",""))
        if user['money'] < a: return update.message.reply_text("❌ 자산 부족!")
        user['money'] -= a; betting_pool[uid] = (bt, a)
        update.message.reply_text(f"✅ {a:,}G 배팅 완료!")
        if not is_betting_active: Thread(target=start_baccarat, args=(update, context)).start()

# --- [4. 콜백 및 실행] ---
def button_callback(update, context):
    query = update.callback_query; uid = query.from_user.username
    if uid not in user_data: return
    if query.data.startswith("buy_"):
        pk = query.data.split("_")[1]
        if user_data[uid]['money'] < PICKS[pk]['p']: return query.answer("❌ 코인 부족!", show_alert=True)
        user_data[uid]['money'] -= PICKS[pk]['p']; user_data[uid]['pick'] = pk; user_data[uid]['dur'] = PICKS[pk]['d']
        save_data(); query.answer(f"✅ {pk} 구매 완료!", show_alert=True)

if __name__ == '__main__':
    load_data(); keep_alive()
    updater = Updater(TOKEN, use_context=True)
    updater.dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), handle_message))
    updater.dispatcher.add_handler(CallbackQueryHandler(button_callback))
    updater.start_polling()
    updater.idle()
