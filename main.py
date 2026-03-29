import logging, time, random, os, datetime
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler

# --- [1. 서버 및 관리자 설정] ---
app = Flask(''); ADMIN_ID = "EJ1427" 
@app.route('/')
def home(): return "G-COIN BOT Online"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
def keep_alive(): Thread(target=run).start()

# --- [2. 데이터베이스 및 카드 설정] ---
user_data = {} 
baccarat_history = [] 
current_round = 0 
IMG_BASE = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/cards/"

# 광물 확률 및 가격 설정
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

PICKS = {
    "Wood": {"p": 1000000, "d": 100}, "Stone": {"p": 5000000, "d": 300},
    "Iron": {"p": 15000000, "d": 500}, "Gold": {"p": 50000000, "d": 1000},
    "Diamond": {"p": 250000000, "d": 5000}, "Netherite": {"p": 1000000000, "d": 10000}
}

SUITS = ["♠️", "♥️", "♦️", "♣️"]; RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
DECK_ORIGIN = [{"rank": r, "suit": s, "value": min(i+1, 10) if r not in ["10", "J", "Q", "K"] else 0} for s in SUITS for i, r in enumerate(RANKS)]

def get_user(uid): return user_data.get(uid)
def draw_card(deck):
    card = random.choice(deck); deck.remove(card); return card, deck

# --- [3. 메인 핸들러] ---
def handle_message(update, context):
    global current_round, baccarat_history
    if not update.message or not update.message.text: return
    uid = update.message.from_user.username
    if not uid: return
    text = update.message.text.strip()

    # 가입
    if text == "!가입":
        if uid in user_data: return update.message.reply_text("이미 가입된 계정입니다.")
        user_data[uid] = {'money': 100000, 'pick': 'Wood', 'dur': 100, 'max_dur': 100, 'inv': {k: 0 for k in ORES}, 'last_mine': 0}
        return update.message.reply_text("🎊 가입 완료! 10만 G가 지급되었습니다.")

    user = get_user(uid)
    if not user: return

    # [바카라 배팅 로직 - 금액 무제한 및 명령어 최적화]
    target_cmd = None
    if text.startswith("!플"): target_cmd = "!플"; bet_type = "P"
    elif text.startswith("!뱅"): target_cmd = "!뱅"; bet_type = "B"
    elif text.startswith("!타이"): target_cmd = "!타이"; bet_type = "T"

    if target_cmd:
        try:
            # 명령어 뒤에 붙은 모든 숫자를 추출 (공백, 괄호 등 제거)
            amt_text = "".join(filter(str.isdigit, text.replace(target_cmd, "")))
            if not amt_text: return update.message.reply_text(f"💰 배팅 금액을 입력해 주세요!\n사용법: {target_cmd} 100")
            
            amt = int(amt_text)
            if amt < 0: return update.message.reply_text("❌ 잘못된 금액입니다.")
            if amt > user['money']: return update.message.reply_text(f"❌ 잔액이 부족합니다! (현재: {user['money']:,} G)")

            current_round += 1
            temp_deck = list(DECK_ORIGIN)
            p1, temp_deck = draw_card(temp_deck); p2, temp_deck = draw_card(temp_deck)
            b1, temp_deck = draw_card(temp_deck); b2, temp_deck = draw_card(temp_deck)
            pv, bv = (p1['value']+p2['value'])%10, (b1['value']+b2['value'])%10

            # 카드 대형 연출
            update.message.reply_photo(photo=f"{IMG_BASE}p_open.png", caption=f"🃏 [ {current_round}/45 회차 ]\n플레이어 카드 공개: {pv}점")
            time.sleep(0.6)
            update.message.reply_photo(photo=f"{IMG_BASE}b_open.png", caption=f"🃏 뱅커 카드 공개: {bv}점")
            
            result = "P" if pv > bv else ("B" if bv > pv else "T")
            baccarat_history.append(result); user['money'] -= amt

            # 배당: 플 2.0 / 뱅 1.85 / 타이 6.0
            if bet_type == result:
                rate = 2.0 if result == "P" else (1.85 if result == "B" else 6.0)
                prize = int(amt * rate); user['money'] += prize
                res_txt = f"✅ 승리! {rate}배 당첨: +{prize:,} G"
            else: res_txt = f"❌ 패배.. -{amt:,} G"
            
            update.message.reply_text(f"🎰 결과: {pv} vs {bv}\n{res_txt}\n💵 잔액: {user['money']:,} G")

            if current_round >= 45:
                current_round = 0; baccarat_history = []
                update.message.reply_text("⚠️ 45회차 종료! 그림장과 회차를 리셋합니다. (새 판 시작)")
            return 
        except Exception: return

    # [일반 명령어들]
    if text == "!채광":
        now = time.time()
        if now - user['last_mine'] < 40: return update.message.reply_text(f"⏱ {int(40-(now-user['last_mine']))}초 후 가능")
        if user['dur'] <= 0: return update.message.reply_text("🪓 곡괭이 파손!")
        user['dur'] -= 1; user['last_mine'] = now
        res_key = random.choices(list(ORES.keys()), weights=[v['c'] for v in ORES.values()])[0]
        o = ORES[res_key]; user['inv'][res_key] += 1
        return update.message.reply_text(f"⛏ {o['e']} {o['t']}티어 {o['n']} 획득!\n🔧 내구도: {user['dur']}/{user['max_dur']}")

    elif text == "!바카라":
        if not baccarat_history: return update.message.reply_text("기록이 없습니다.")
        COLS = 15; grid = [["⬜" for _ in range(COLS)] for _ in range(3)]
        for i, res in enumerate(baccarat_history):
            if i < 45: grid[i//COLS][i%COLS] = "🔴" if res == "P" else ("🔵" if res == "B" else "🟢")
        return update.message.reply_text(f"📊 **그림장 ({current_round}/45)**\n`" + "\n".join(["".join(r) for r in grid]) + "`", parse_mode=ParseMode.MARKDOWN)

    elif text == "!내정보": return update.message.reply_text(f"👤 @{uid}\n💵 자산: {user['money']:,} G\n⛏ {user['pick']} ({user['dur']}/{user['max_dur']})")
    elif text == "!인벤":
        inv_msg = "🎒 **가방**\n"; found = False
        for k, v in ORES.items():
            if user['inv'][k] > 0: inv_msg += f"{v['e']} {v['n']}: {user['inv'][k]}개\n"; found = True
        return update.message.reply_text(inv_msg if found else "🎒 비어있음")
    elif text == "!판매":
        kb = [[InlineKeyboardButton(f"{i}티어", callback_data=f"s_{i}") for i in range(1, 5)], [InlineKeyboardButton("5티어", callback_data="s_5"), InlineKeyboardButton("전체판매", callback_data="s_all")]]
        return update.message.reply_text("💰 판매 등급 선택", reply_markup=InlineKeyboardMarkup(kb))
    elif text == "!상점":
        shop_msg = "⛏ **상점**\n"; [shop_msg := shop_msg + f"• {k}: {v['p']:,} G\n" for k, v in PICKS.items()]
        kb = [[InlineKeyboardButton(f"구매 {k}", callback_data=f"buy_{k}")] for k in PICKS]
        return update.message.reply_text(shop_msg, reply_markup=InlineKeyboardMarkup(kb))
    elif text == "!랭킹":
        rankers = sorted(user_data.items(), key=lambda x: x[1]['money'], reverse=True)[:10]
        rank_msg = "🏆 **자산 순위**\n"
        for i, (name, data) in enumerate(rankers, 1): rank_msg += f"{i}위. @{name}: {data['money']:,} G\n"
        return update.message.reply_text(rank_msg, parse_mode=ParseMode.MARKDOWN)
    elif text == "!명령어": return update.message.reply_text("📜 가입/내정보/인벤/채광/판매/상점/바카라/랭킹\n배팅: !플 !뱅 !타이 [금액]")

def handle_callback(update, context):
    q = update.callback_query; uid = q.from_user.username; user = get_user(uid)
    if not user: return
    if q.data.startswith("buy_"):
        pk = q.data.split("_")[1]; info = PICKS[pk]
        if user['money'] >= info['p']:
            user['money'] -= info['p']; user['pick'] = pk; user['dur'] = info['d']; user['max_dur'] = info['d']
            q.edit_message_text(f"✅ {pk} 장착!")
        else: q.answer("돈 부족!", show_alert=True)
    elif q.data.startswith("s_"):
        gain = 0
        if q.data == "s_all":
            for k in ORES: gain += user['inv'][k] * ORES[k]['p']; user['inv'][k] = 0
        else:
            t = int(q.data.split("_")[1]); [gain := gain + user['inv'][k] * v['p'] for k, v in ORES.items() if v['t'] == t]; [user['inv'].update({k: 0}) for k, v in ORES.items() if v['t'] == t]
        user['money'] += gain; q.edit_message_text(f"💰 판매 완료: +{gain:,} G")
    q.answer()

if __name__ == '__main__':
    keep_alive()
    TOKEN = "8771125252:AAFbKHLcDM2KhLR3MIp6ZGOnFQQWlIQUIlc"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    dp.add_handler(CallbackQueryHandler(handle_callback))
    updater.start_polling(); updater.idle()
