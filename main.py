

import logging, time, random, os, datetime
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler

# --- [서버 유지 설정] ---
app = Flask(''); ADMIN_ID = "EJ1427"
@app.route('/')
def home(): return "G-COIN BOT Online"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
def keep_alive(): Thread(target=run).start()

# --- [데이터베이스 및 설정] ---
user_data = {} 
baccarat_history = [] 

# 카드 이미지 베이스 URL (GitHub 등에 올린 이미지 경로)
# 예: p_open.png (플레이어 카드 이미지), b_open.png (뱅커 카드 이미지)
IMG_BASE = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/cards/"

# 52장 포커 덱 설정
SUITS = ["S", "H", "D", "C"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
DECK = [{"rank": r, "suit": s, "value": min(i+1, 10) if r not in ["10", "J", "Q", "K"] else 0, "name": f"{r}{s}"} for s in SUITS for i, r in enumerate(RANKS)]

ORES = {
    "diam1": {"n":"💎 1티어 다이아몬드", "p":3000000, "t":1, "c":1.0},
    "ori": {"n":"🔱 오리하르콘", "p":2500000, "t":1, "c":2.0},
    "ruby": {"n":"🍎 루비", "p":500000, "t":2, "c":5.0},
    "plat": {"n":"⚪ 백금광석", "p":450000, "t":2, "c":7.0},
    "sapph": {"n":"🌌 사파이어", "p":400000, "t":3, "c":10.0},
    "emera": {"n":"🧪 에메랄드", "p":250000, "t":3, "c":15.0},
    "gold": {"n":"🥇 금광석", "p":100000, "t":4, "c":15.0},
    "silv": {"n":"🥈 은광석", "p":50000, "t":4, "c":15.0},
    "coal": {"n":"🌑 석탄", "p":10000, "t":5, "c":15.0},
    "stone": {"n":"🪨 일반돌", "p":5000, "t":5, "c":15.0}
}
PICKS = {
    "Wood": {"p": 1000000, "d": 100}, "Stone": {"p": 5000000, "d": 300},
    "Iron": {"p": 15000000, "d": 500}, "Gold": {"p": 50000000, "d": 1000},
    "Diamond": {"p": 250000000, "d": 5000}, "Netherite": {"p": 1000000000, "d": 10000}
}

def get_user(uid): return user_data.get(uid)
def draw_card(deck):
    card = random.choice(deck); deck.remove(card)
    return card, deck

# --- [메인 핸들러] ---
def handle_message(update, context):
    uid = update.message.from_user.username
    if not uid: return
    text = update.message.text
    
    if text == "!가입":
        if uid in user_data: return update.message.reply_text("이미 가입된 계정입니다.")
        user_data[uid] = {
            'money': 100000, 'pick': 'Wood', 'dur': 100, 'max_dur': 100,
            'inv': {k: 0 for k in ORES}, 'reg_date': datetime.datetime.now().strftime("%Y-%m-%d"), 
            'last_check': "", 'last_mine': 0
        }
        return update.message.reply_text("🎊 가입 완료! !명령어를 입력해 확인하세요.")

    user = get_user(uid)
    if not user: return

    # [1] !랭킹 시스템
    if text == "!랭킹":
        sorted_users = sorted(user_data.items(), key=lambda x: x[1]['money'], reverse=True)
        rank_msg = "🏆 **G-COIN 보유량 랭킹 (TOP 10)**\n\n"
        for i, (username, data) in enumerate(sorted_users[:10], 1):
            medal = "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else f"{i}위"))
            rank_msg += f"{medal} @{username} : {data['money']:,} G\n"
        update.message.reply_text(rank_msg, parse_mode=ParseMode.MARKDOWN)

    # [2] !명령어 도움말
    elif text == "!명령어":
        msg = ("📜 **명령어 리스트**\n"
               "🔹 가입 / 내정보 / 인벤 / 랭킹\n"
               "🔹 채광(40초쿨) / 판매 / 상점 / 출석\n"
               "🔹 플,뱅,타이 [금액] / 바카라(그림장)")
        update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    # [3] !채광 (40초 쿨타임 적용)
    elif text == "!채광":
        now = time.time()
        if now - user.get('last_mine', 0) < 40:
            remain = int(40 - (now - user['last_mine']))
            return update.message.reply_text(f"⏱ **{remain}초** 후에 다시 채광 가능합니다.")
        if user['dur'] <= 0: return update.message.reply_text("🪓 곡괭이 파손! 상점에서 새로 구매하세요.")
        user['dur'] -= 1; user['last_mine'] = now
        sel = random.choices(list(ORES.keys()), weights=[v['c'] for v in ORES.values()])[0]
        user['inv'][sel] += 1
        update.message.reply_text(f"⛏ **{ORES[sel]['n']}** 획득!\n🔧 내구도: {user['dur']}/{user['max_dur']}")

    # [4] !바카라 게임 (카드 이미지 연출)
    elif any(text.startswith(x) for x in ["!플 ", "!뱅 ", "!타이 "]):
        try:
            bet_type = "P" if "!플" in text else ("B" if "!뱅" in text else "T")
            amt = int(text.split()[1])
            if amt > user['money'] or amt <= 0: return update.message.reply_text("잔액 부족!")
            
            deck = list(DECK); p1, deck = draw_card(deck); p2, deck = draw_card(deck)
            b1, deck = draw_card(deck); b2, deck = draw_card(deck)
            p_val, b_val = (p1['value']+p2['value'])%10, (b1['value']+b2['value'])%10

            # 카드 이미지 순차 전송
            update.message.reply_photo(photo=f"{IMG_BASE}p_open.png", caption=f"🃏 **플레이어 카드 공개**\n합 {p_val}")
            time.sleep(2)
            update.message.reply_photo(photo=f"{IMG_BASE}b_open.png", caption=f"🃏 **뱅커 카드 공개**\n합 {b_val}")
            
            result = "P" if p_val > b_val else ("B" if b_val > p_val else "T")
            baccarat_history.append(result)
            if len(baccarat_history) > 120: baccarat_history.pop(0)

            user['money'] -= amt
            if bet_type == result:
                mult = 8 if result == "T" else 2
                user['money'] += (amt * mult)
                res_t = f"✅ 승리! +{amt*mult:,} G"
            else: res_t = f"❌ 패배.. -{amt:,} G"
            update.message.reply_text(f"🎰 **결과: {p_val} vs {b_val}**\n{res_t}")
        except: pass

    # [5] 기타 명령어
    elif text == "!바카라":
        COLS, ROWS = 20, 6
        grid = [["⬜" for _ in range(COLS)] for _ in range(ROWS)]
        for i, res in enumerate(baccarat_history):
            r, c = i // COLS, i % COLS
            if r < ROWS: grid[r][c] = "🔵" if res == "B" else ("🔴" if res == "P" else "🟢")
        update.message.reply_text("📊 **그림장**\n`" + "\n".join(["".join(r) for r in grid]) + "`", parse_mode=ParseMode.MARKDOWN)

    elif text == "!상점":
        shop_msg = "⛏ **곡괭이 상점**\n───────────────────\n"
        kb = [[InlineKeyboardButton(f"{pk} 구매 ({info['p']:,}G)", callback_data=f"buy_{pk}")] for pk, info in PICKS.items()]
        update.message.reply_text(shop_msg, reply_markup=InlineKeyboardMarkup(kb))

    elif text == "!판매":
        kb = [[InlineKeyboardButton(f"{i}티어", callback_data=f"s_{i}") for i in range(1, 4)],
              [InlineKeyboardButton(f"{i}티어", callback_data=f"s_{i}") for i in range(4, 6)],
              [InlineKeyboardButton("전체판매", callback_data="s_all")]]
        update.message.reply_text("💰 판매할 등급을 선택하세요.", reply_markup=InlineKeyboardMarkup(kb))

    elif text == "!내정보":
        update.message.reply_text(f"👤 **@{uid}**\n💵 잔액: {user['money']:,} G\n⛏ 곡괭이: {user['pick']} ({user['dur']}/{user['max_dur']})")

    elif text.startswith("!지급") and uid == ADMIN_ID:
        try:
            _, t_id, t_amt = text.split(); t_id = t_id.replace("@","")
            user_data[t_id]['money'] += int(t_amt)
            update.message.reply_text(f"✅ @{t_id} 지급 완료!")
        except: pass

# --- [콜백 핸들러] ---
def handle_callback(update, context):
    q = update.callback_query; uid = q.from_user.username; user = get_user(uid)
    if not user: return

    if q.data.startswith("buy_"):
        pk = q.data.split("_")[1]; info = PICKS[pk]
        if user['money'] >= info['p']:
            user['money'] -= info['p']; user['pick'] = pk; user['dur'] = info['d']; user['max_dur'] = info['d']
            q.edit_message_text(f"✅ {pk} 장착 완료!")
        else: q.answer("돈이 부족합니다!", show_alert=True)

    elif q.data.startswith("s_"):
        gain = 0
        if q.data == "s_all":
            for k in ORES: gain += user['inv'][k] * ORES[k]['p']; user['inv'][k] = 0
        else:
            t = int(q.data.split("_")[1])
            for k, v in ORES.items():
                if v['t'] == t: gain += user['inv'][k] * v['p']; user['inv'][k] = 0
        user['money'] += gain; q.edit_message_text(f"💰 판매 완료: +{gain:,} G")
    q.answer()

if __name__ == '__main__':
    keep_alive()
    TOKEN = "8771125252:AAFbKHLcDM2KhLR3MIp6ZGOnFQQWlIQUIlc"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(handle_callback))
    updater.start_polling(); updater.idle()
