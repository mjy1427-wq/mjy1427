import logging, time, random, os, datetime
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler

# --- [1. 서버 유지 및 관리자 설정] ---
app = Flask(''); ADMIN_ID = "EJ1427" 
@app.route('/')
def home(): return "G-COIN BOT Online"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
def keep_alive(): Thread(target=run).start()

# --- [2. 데이터베이스 및 설정] ---
user_data = {} 
baccarat_history = [] 
IMG_BASE = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/cards/"

# [광물 데이터] - 요청하신 4, 5티어 확률 대폭 상향 반영
ORES = {
    "diam1": {"n":"다이아몬드", "p":3000000, "t":1, "c":1.0, "e":"💎"},
    "ori": {"n":"오리하르콘", "p":2500000, "t":1, "c":2.0, "e":"🔱"},
    "ruby": {"n":"루비", "p":500000, "t":2, "c":5.0, "e":"🍎"},
    "plat": {"n":"백금광석", "p":450000, "t":2, "c":7.0, "e":"⚪"},
    "sapph": {"n":"사파이어", "p":400000, "t":3, "c":15.0, "e":"🌌"},
    "emera": {"n":"에메랄드", "p":250000, "t":3, "c":20.0, "e":"🧪"},
    "gold": {"n":"금광석", "p":100000, "t":4, "c":25.0, "e":"🥇"},   # 4티어 (합 50)
    "silv": {"n":"은광석", "p":50000, "t":4, "c":25.0, "e":"🥈"},    # 4티어 (합 50)
    "coal": {"n":"석탄", "p":10000, "t":5, "c":35.0, "e":"🌑"},    # 5티어 (합 70)
    "stone": {"n":"일반돌", "p":5000, "t":5, "c":35.0, "e":"🪨"}     # 5티어 (합 70)
}

PICKS = {
    "Wood": {"p": 1000000, "d": 100}, "Stone": {"p": 5000000, "d": 300},
    "Iron": {"p": 15000000, "d": 500}, "Gold": {"p": 50000000, "d": 1000},
    "Diamond": {"p": 250000000, "d": 5000}, "Netherite": {"p": 1000000000, "d": 10000}
}

# [카드 덱 설정]
SUITS = ["♠️", "♥️", "♦️", "♣️"]; RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
DECK = [{"rank": r, "suit": s, "value": min(i+1, 10) if r not in ["10", "J", "Q", "K"] else 0} for s in SUITS for i, r in enumerate(RANKS)]

def get_user(uid): return user_data.get(uid)
def draw_card(deck):
    card = random.choice(deck); deck.remove(card)
    return card, deck

# --- [3. 메인 핸들러] ---
def handle_message(update, context):
    uid = update.message.from_user.username
    if not uid: return
    text = update.message.text

    if text == "!가입":
        if uid in user_data: return update.message.reply_text("이미 가입된 계정입니다.")
        user_data[uid] = {'money': 100000, 'pick': 'Wood', 'dur': 100, 'max_dur': 100, 'inv': {k: 0 for k in ORES}, 'last_mine': 0}
        return update.message.reply_text("🎊 가입 완료! !명령어를 입력하세요.")

    user = get_user(uid)
    if not user: return

    # [채광] 장식 제거 + 티어/가격 표시
    if text == "!채광":
        now = time.time()
        if now - user['last_mine'] < 40:
            return update.message.reply_text(f"⏱ {int(40-(now-user['last_mine']))}초 후 가능")
        if user['dur'] <= 0: return update.message.reply_text("🪓 곡괭이가 파손되었습니다!")
        user['dur'] -= 1; user['last_mine'] = now
        res_key = random.choices(list(ORES.keys()), weights=[v['c'] for v in ORES.values()])[0]
        o = ORES[res_key]; user['inv'][res_key] += 1
        mine_msg = (f"⛏ {o['e']} {o['t']}티어 {o['n']}을(를) 캤습니다!\n💰 가치: {o['p']:,} G\n🔧 남은 내구도: {user['dur']}/{user['max_dur']}")
        return update.message.reply_text(mine_msg)

    # [바카라 배팅] !플, !뱅, !타이 완벽 복구
    elif any(text.startswith(x) for x in ["!플 ", "!뱅 ", "!타이 "]):
        try:
            parts = text.split(); bet_type = "P" if "!플" in parts[0] else ("B" if "!뱅" in parts[0] else "T")
            amt = int(parts[1])
            if amt > user['money'] or amt <= 0: return update.message.reply_text("코인이 부족합니다.")
            temp_deck = list(DECK); p1, temp_deck = draw_card(temp_deck); p2, temp_deck = draw_card(temp_deck)
            b1, temp_deck = draw_card(temp_deck); b2, temp_deck = draw_card(temp_deck)
            pv, bv = (p1['value']+p2['value'])%10, (b1['value']+b2['value'])%10
            update.message.reply_photo(photo=f"{IMG_BASE}p_open.png", caption=f"🃏 플레이어: {pv}점")
            time.sleep(1.2)
            update.message.reply_photo(photo=f"{IMG_BASE}b_open.png", caption=f"🃏 뱅커: {bv}점")
            result = "P" if pv > bv else ("B" if bv > pv else "T")
            baccarat_history.append(result); user['money'] -= amt
            if bet_type == result:
                rate = 8 if result == "T" else 2
                user['money'] += (amt * rate); res_txt = f"✅ 승리! +{amt*rate:,} G"
            else: res_txt = f"❌ 패배.. -{amt:,} G"
            return update.message.reply_text(f"🎰 결과: {pv} vs {bv}\n{res_txt}")
        except: return

    # [판매] 레이아웃 (1~4티어 / 5티어+전체판매)
    elif text == "!판매":
        kb = [[InlineKeyboardButton(f"{i}티어", callback_data=f"s_{i}") for i in range(1, 5)],
              [InlineKeyboardButton("5티어", callback_data="s_5"), InlineKeyboardButton("전체판매", callback_data="s_all")]]
        return update.message.reply_text("💰 판매할 등급을 선택하세요.", reply_markup=InlineKeyboardMarkup(kb))

    # [상점] 곡괭이 정보 표시
    elif text == "!상점":
        shop_msg = "⛏ **곡괭이 상점**\n━━━━━━━━━━━━━━\n"
        for k, v in PICKS.items(): shop_msg += f"• **{k}**: {v['p']:,} G (내구도 {v['d']})\n"
        kb = [[InlineKeyboardButton(f"{k} 구매", callback_data=f"buy_{k}")] for k in PICKS]
        return update.message.reply_text(shop_msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)

    # [인벤] 개수 + 가격 표시
    elif text == "!인벤":
        inv_msg = "🎒 **가방 내용물**\n"
        found = False
        for k, v in ORES.items():
            if user['inv'][k] > 0:
                inv_msg += f"{v['e']} {v['n']}: {user['inv'][k]}개 (개당 {v['p']:,} G)\n"
                found = True
        return update.message.reply_text(inv_msg if found else "🎒 가방이 비어있습니다.")

    elif text == "!명령어":
        return update.message.reply_text("📜 가입 / 내정보 / 인벤 / 랭킹\n🔹 채광 / 판매 / 상점 / 바카라\n🔹 !플 !뱅 !타이 [금액]")

    elif text == "!내정보":
        return update.message.reply_text(f"👤 @{uid}\n💵 잔액: {user['money']:,} G\n⛏ {user['pick']} ({user['dur']}/{user['max_dur']})")

    elif text == "!바카라":
        COLS = 20; grid = [["⬜" for _ in range(COLS)] for _ in range(6)]
        for i, res in enumerate(baccarat_history[-120:]):
            grid[i//COLS][i%COLS] = "🔵" if res == "B" else ("🔴" if res == "P" else "🟢")
        return update.message.reply_text("📊 **그림장**\n`" + "\n".join(["".join(r) for r in grid]) + "`", parse_mode=ParseMode.MARKDOWN)

# --- [4. 콜백 핸들러] ---
def handle_callback(update, context):
    q = update.callback_query; uid = q.from_user.username; user = get_user(uid)
    if not user: return
    if q.data.startswith("buy_"):
        pk = q.data.split("_")[1]; info = PICKS[pk]
        if user['money'] >= info['p']:
            user['money'] -= info['p']; user['pick'] = pk; user['dur'] = info['d']; user['max_dur'] = info['d']
            q.edit_message_text(f"✅ {pk} 장착 완료!")
        else: q.answer("돈 부족!", show_alert=True)
    elif q.data.startswith("s_"):
        gain = 0
        if q.data == "s_all":
            for k in ORES: gain += user['inv'][k] * ORES[k]['p']; user['inv'][k] = 0
        else:
            t = int(q.data.split("_")[1])
            for k, v in ORES.items():
                if v['t'] == t: gain += user['inv'][k] * v['p']; user['inv'][k] = 0
        user['money'] += gain
        q.edit_message_text(f"💰 판매 완료: +{gain:,} G")
    q.answer()

if __name__ == '__main__':
    keep_alive()
    TOKEN = "8771125252:AAFbKHLcDM2KhLR3MIp6ZGOnFQQWlIQUIlc"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(handle_callback))
    updater.start_polling(); updater.idle()
