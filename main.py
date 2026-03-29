
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

# 52장 포커 덱 설정
SUITS = ["♠", "♥", "◆", "♣"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
DECK = [{"rank": r, "suit": s, "value": min(i+1, 10) if r not in ["10", "J", "Q", "K"] else 0} for s in SUITS for i, r in enumerate(RANKS)]

# 광석 데이터 (티어별 분류)
ORES = {
    "diam1":  {"n":"💎 1티어 다이아몬드", "p":3000000, "t":1, "c":1.0},
    "ori":    {"n":"🔱 오리하르콘",      "p":2500000, "t":1, "c":2.0},
    "ruby":   {"n":"🍎 루비",            "p":500000,  "t":2, "c":5.0},
    "plat":   {"n":"⚪ 백금광석",        "p":450000,  "t":2, "c":7.0},
    "sapph":  {"n":"🌌 사파이어",        "p":400000,  "t":3, "c":10.0},
    "emera":  {"n":"🧪 에메랄드",        "p":250000,  "t":3, "c":15.0},
    "gold":   {"n":"🥇 금광석",          "p":100000,  "t":4, "c":15.0},
    "silv":   {"n":"🥈 은광석",          "p":50000,   "t":4, "c":15.0},
    "coal":   {"n":"🌑 석탄",            "p":10000,   "t":5, "c":15.0},
    "stone":  {"n":"🪨 일반돌",          "p":5000,    "t":5, "c":15.0}
}

# 곡괭이 데이터 (상점 통합 리스트)
PICKS = {
    "Wood": {"p": 1000000, "d": 100},
    "Stone": {"p": 5000000, "d": 300},
    "Iron": {"p": 15000000, "d": 500},
    "Gold": {"p": 50000000, "d": 1000},
    "Diamond": {"p": 250000000, "d": 5000},
    "Netherite": {"p": 1000000000, "d": 10000}
}

def get_user(uid): return user_data.get(uid)
def draw_card(deck):
    card = random.choice(deck)
    deck.remove(card)
    return card, deck
def format_card(card): return f"{card['rank']}{card['suit']}"

# --- [메인 핸들러] ---
def handle_message(update, context):
    uid = update.message.from_user.username
    if not uid: return
    text = update.message.text
    user = get_user(uid)

    if text == "!가입":
        if uid in user_data: return update.message.reply_text("이미 가입된 계정입니다.")
        reg_date = datetime.datetime.now().strftime("%Y-%m-%d")
        user_data[uid] = {
            'money': 100000, 'pick': 'Wood', 'dur': 100, 'max_dur': 100,
            'inv': {k: 0 for k in ORES}, 'reg_date': reg_date, 'last_check': ""
        }
        update.message.reply_text(f"🎊 등록완료! 10만원과 Wood 곡괭이 지급.")
        return

    if not user: return

    # [채광 시스템]
    if text == "!채광":
        if user['dur'] <= 0: return update.message.reply_text("🪓 내구도가 다 되었습니다! 상점에서 새로 구매하세요.")
        user['dur'] -= 1
        rand = random.random() * 100; curr = 0; sel = "stone"
        for k, v in ORES.items():
            curr += v['c']
            if rand <= curr: sel = k; break
        user['inv'][sel] += 1
        msg = (f"⛏ **채광 완료!**\n\n⛏ 곡괭이: {user['pick']}\n💎 획득: {ORES[sel]['n']}\n"
               f"💰 가치: {ORES[sel]['p']:,} G\n🔧 내구도: {user['dur']}/{user['max_dur']}")
        update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    # [판매 시스템 - 티어별 버튼]
    elif text == "!판매":
        kb = [
            [InlineKeyboardButton("1티어", callback_data="s_1"), InlineKeyboardButton("2티어", callback_data="s_2"),
             InlineKeyboardButton("3티어", callback_data="s_3"), InlineKeyboardButton("4티어", callback_data="s_4")],
            [InlineKeyboardButton("5티어", callback_data="s_5"), InlineKeyboardButton("전체판매", callback_data="s_all")]
        ]
        update.message.reply_text("💰 **판매할 등급을 선택하세요.**", reply_markup=InlineKeyboardMarkup(kb))

    # [상점 시스템 - 통합 리스트]
    elif text == "!상점":
        shop_msg = "⛏ **곡괭이 상점**\n───────────────────\n\n"
        kb = []
        for pk, info in PICKS.items():
            shop_msg += f"📦 **{pk}**\n💰 가격: {info['p']:,} G\n🔧 내구도: {info['d']:,}\n───────────────────\n"
            kb.append([InlineKeyboardButton(f"{pk} 구매", callback_data=f"buy_{pk}")])
        update.message.reply_text(shop_msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)

    # [바카라 게임 - 포커 덱 연출]
    elif any(text.startswith(x) for x in ["!플 ", "!뱅 ", "!타이 "]):
        try:
            bet_type = "P" if "!플" in text else ("B" if "!뱅" in text else "T")
            amt = int(text.split()[1])
            if amt > user['money'] or amt <= 0: return update.message.reply_text("잔액이 부족합니다!")
            
            m = update.message.reply_text(f"🎲 배팅 완료! 결과를 기다려주세요...")
            deck = list(DECK); p1, deck = draw_card(deck); p2, deck = draw_card(deck)
            b1, deck = draw_card(deck); b2, deck = draw_card(deck)
            p_val, b_val = (p1['value']+p2['value'])%10, (b1['value']+b2['value'])%10

            time.sleep(2); context.bot.edit_message_text(f"🃏 플레이어 오픈: [{format_card(p1)}][{format_card(p2)}] (합 {p_val})", chat_id=update.effective_chat.id, message_id=m.message_id)
            time.sleep(2); context.bot.edit_message_text(f"🃏 플레이어: {p_val}\n🃏 뱅커 오픈: [{format_card(b1)}][{format_card(b2)}] (합 {b_val})", chat_id=update.effective_chat.id, message_id=m.message_id)
            
            # 추가 카드 룰 (간략화)
            if p_val <= 5: 
                time.sleep(1.5); p3, deck = draw_card(deck); p_val = (p_val+p3['value'])%10
                context.bot.edit_message_text(f"🃏 플레이어 추가 카드: [{format_card(p3)}]\n🃏 최종: {p_val} vs {b_val}", chat_id=update.effective_chat.id, message_id=m.message_id)
            
            result = "P" if p_val > b_val else ("B" if b_val > p_val else "T")
            baccarat_history.append(result)
            if len(baccarat_history) > 120: baccarat_history.pop(0)

            user['money'] -= amt
            if bet_type == result:
                mult = 8 if result == "T" else 2
                user['money'] += (amt * mult)
                res_t = f"✅ 승리! +{amt*mult:,} G"
            else: res_t = f"❌ 패배.. -{amt:,} G"
            
            time.sleep(1.5)
            update.message.reply_text(f"🎰 **결과: {p_val} vs {b_val}**\n{res_t}")
        except: update.message.reply_text("사용법: ![플/뱅/타이] [금액]")

    # [바카라 그림장 - 첫 칸부터 꽉 채우기 최적화]
    elif text == "!바카라":
        COLS, ROWS = 20, 6
        grid = [["⬜" for _ in range(COLS)] for _ in range(ROWS)]
        for i, res in enumerate(baccarat_history):
            r, c = i // COLS, i % COLS
            if r < ROWS: grid[r][c] = "🔵" if res == "B" else ("🔴" if res == "P" else "🟢")
        
        display = "📊 **실시간 바카라 그림장**\n`"
        for row in grid: display += "".join(row) + "\n"
        display += "`"
        update.message.reply_text(display, parse_mode=ParseMode.MARKDOWN)

# --- [콜백 핸들러 (버튼 클릭 처리)] ---
def handle_callback(update, context):
    q = update.callback_query; uid = q.from_user.username; user = get_user(uid)
    if not user: return
    
    if q.data.startswith("s_"): # 판매
        gain = 0
        if q.data == "s_all":
            for k in ORES: gain += user['inv'][k] * ORES[k]['p']; user['inv'][k] = 0
        else:
            tier = int(q.data.split("_")[1])
            for k, v in ORES.items():
                if v['t'] == tier: gain += user['inv'][k] * v['p']; user['inv'][k] = 0
        user['money'] += gain
        q.edit_message_text(f"💰 판매 완료! +{gain:,} G")
        
    elif q.data.startswith("buy_"): # 구매
        pk = q.data.split("_")[1]; info = PICKS[pk]
        if user['money'] >= info['p']:
            user['money'] -= info['p']; user['pick'] = pk
            user['dur'] = info['d']; user['max_dur'] = info['d']
            q.edit_message_text(f"✅ {pk} 곡괭이 장착 완료!")
        else: q.answer("잔액이 부족합니다!", show_alert=True)
    q.answer()

if __name__ == '__main__':
    keep_alive()
    TOKEN = "8771125252:AAFbKHLcDM2KhLR3MIp6ZGOnFQQWlIQUIlc"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(handle_callback))
    updater.start_polling(); updater.idle()
