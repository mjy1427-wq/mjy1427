import logging, time, random, os, datetime
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler

# --- [서버 및 관리자 설정] ---
app = Flask(''); ADMIN_ID = "EJ1427" 
@app.route('/')
def home(): return "G-COIN BOT Online"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
def keep_alive(): Thread(target=run).start()

# --- [데이터베이스 및 설정] ---
user_data = {} 
baccarat_history = [] 
IMG_BASE = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/cards/"

# [광물 및 가격 데이터] - !인벤토리와 !판매에 사용됨
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

# [곡괭이 데이터] - !상점에 반영됨 (사진 4, 5, 6번 기준)
PICKS = {
    "Wood": {"p": 1000000, "d": 100}, "Stone": {"p": 5000000, "d": 300},
    "Iron": {"p": 15000000, "d": 500}, "Gold": {"p": 50000000, "d": 1000},
    "Diamond": {"p": 250000000, "d": 5000}, "Netherite": {"p": 1000000000, "d": 10000}
}

# [카드 덱 설정]
SUITS = ["♠️", "♥️", "♦️", "♣️"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
DECK = [{"rank": r, "suit": s, "value": min(i+1, 10) if r not in ["10", "J", "Q", "K"] else 0, "name": f"{r}{s}"} for s in SUITS for i, r in enumerate(RANKS)]

def get_user(uid): return user_data.get(uid)
def draw_card(deck):
    card = random.choice(deck); deck.remove(card)
    return card, deck

# --- [메인 메시지 핸들러] ---
def handle_message(update, context):
    uid = update.message.from_user.username
    if not uid: return
    text = update.message.text

    # 1. 가입 처리
    if text == "!가입":
        if uid in user_data: return update.message.reply_text("이미 가입된 계정입니다.")
        user_data[uid] = {
            'money': 100000, 'pick': 'Wood', 'dur': 100, 'max_dur': 100,
            'inv': {k: 0 for k in ORES}, 'last_mine': 0
        }
        return update.message.reply_text("🎊 가입이 완료되었습니다! !명령어로 시작하세요.")

    user = get_user(uid)
    if not user: return

    # 2. !인벤 (광물 이름 + 개수 + 가격 완벽 반영)
    if text == "!인벤":
        inv_msg = "🎒 **아이템 가방 정보**\n━━━━━━━━━━━━━━\n"
        found = False
        for k, v in ORES.items():
            qty = user['inv'].get(k, 0)
            if qty > 0:
                inv_msg += f"📦 {v['n']}\n   └ 수량: {qty}개 (개당 {v['p']:,} G)\n"
                found = True
        if not found: return update.message.reply_text("🎒 가방이 비어있습니다. !채광을 먼저 하세요!")
        return update.message.reply_text(inv_msg, parse_mode=ParseMode.MARKDOWN)

    # 3. !판매 (사진 1번 레이아웃: 1~4티어 한 줄 / 5티어+전체판매 한 줄)
    elif text == "!판매":
        kb = [
            [InlineKeyboardButton("1티어", callback_data="s_1"), InlineKeyboardButton("2티어", callback_data="s_2"),
             InlineKeyboardButton("3티어", callback_data="s_3"), InlineKeyboardButton("4티어", callback_data="s_4")],
            [InlineKeyboardButton("5티어", callback_data="s_5"), InlineKeyboardButton("전체판매", callback_data="s_all")]
        ]
        return update.message.reply_text("💰 **판매할 등급을 선택하세요.**", reply_markup=InlineKeyboardMarkup(kb))

    # 4. !상점 (사진 4, 5, 6번 문구 및 정보 반영)
    elif text == "!상점":
        shop_msg = (
            "⛏ **곡괭이 상점**\n━━━━━━━━━━━━━━\n\n"
            "**Wood** — 1,000,000 G (내구도 100)\n"
            "**Stone** — 5,000,000 G (내구도 300)\n"
            "**Iron** — 15,000,000 G (내구도 500)\n"
            "**Gold** — 50,000,000 G (내구도 1,000)\n"
            "**Diamond** — 250,000,000 G (내구도 5,000)\n"
            "**Netherite** — 1,000,000,000 G (내구도 10,000)\n\n"
            "구매를 원하는 곡괭이를 아래에서 선택하세요!"
        )
        kb = [[InlineKeyboardButton(f"{pk} 구매", callback_data=f"buy_{pk}")] for pk in PICKS]
        return update.message.reply_text(shop_msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)

    # 5. !채광 (40초 쿨타임)
    elif text == "!채광":
        now = time.time()
        if now - user.get('last_mine', 0) < 40:
            rem = int(40 - (now - user['last_mine']))
            return update.message.reply_text(f"⏱ **{rem}초** 뒤에 다시 채광할 수 있습니다.")
        if user['dur'] <= 0: return update.message.reply_text("🪓 곡괭이가 부서졌습니다! 상점에서 새로 구입하세요.")
        user['dur'] -= 1; user['last_mine'] = now
        res = random.choices(list(ORES.keys()), weights=[v['c'] for v in ORES.values()])[0]
        user['inv'][res] += 1
        return update.message.reply_text(f"⛏ **{ORES[res]['n']}**을(를) 캤습니다!\n🔧 남은 내구도: {user['dur']}/{user['max_dur']}")

    # 6. 바카라 배팅 (!플, !뱅, !타이)
    elif any(text.startswith(x) for x in ["!플 ", "!뱅 ", "!타이 "]):
        try:
            bet = "P" if "!플" in text else ("B" if "!뱅" in text else "T")
            amt = int(text.split()[1])
            if amt > user['money'] or amt <= 0: return update.message.reply_text("보유 코인이 부족합니다.")
            
            deck = list(DECK); p1, deck = draw_card(deck); p2, deck = draw_card(deck)
            b1, deck = draw_card(deck); b2, deck = draw_card(deck)
            pv, bv = (p1['value']+p2['value'])%10, (b1['value']+b2['value'])%10

            update.message.reply_photo(photo=f"{IMG_BASE}p_open.png", caption=f"🃏 플레이어: {pv}점")
            time.sleep(1.5)
            update.message.reply_photo(photo=f"{IMG_BASE}b_open.png", caption=f"🃏 뱅커: {bv}점")
            
            win = "P" if pv > bv else ("B" if bv > pv else "T")
            baccarat_history.append(win); user['money'] -= amt
            if bet == win:
                rate = 8 if win == "T" else 2
                user['money'] += (amt * rate); r_msg = f"✅ 승리! +{amt*rate:,} G"
            else: r_msg = f"❌ 패배.. -{amt:,} G"
            return update.message.reply_text(f"🎰 결과: {pv} vs {bv}\n{r_msg}")
        except: return

    # 7. !명령어 (모든 명령어 활성화)
    elif text == "!명령어":
        help_txt = (
            "📜 **G-COIN BOT 명령어**\n━━━━━━━━━━━━━━\n"
            "🔹 가입 / 내정보 / 인벤 / 랭킹\n"
            "🔹 채광(40초) / 판매 / 상점\n"
            "🔹 바카라(그림장) / !플 !뱅 !타이 [금액]"
        )
        return update.message.reply_text(help_txt, parse_mode=ParseMode.MARKDOWN)

    # 8. 관리자 지급 (익명성 보장)
    elif text.startswith("!지급") and uid == ADMIN_ID:
        try:
            p = text.split(); tid = p[1].replace("@", ""); a = int(p[2])
            if tid in user_data:
                user_data[tid]['money'] += a
                try: context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
                except: pass
                return context.bot.send_message(chat_id=update.effective_chat.id, text=f"🎁 **시스템에서 G-COIN이 지급되었습니다.**\n대상: @{tid}\n금액: {a:,} G")
        except: pass

    # 9. 내정보 및 랭킹
    elif text == "!내정보":
        return update.message.reply_text(f"👤 @{uid}\n💵 잔액: {user['money']:,} G\n⛏ 곡괭이: {user['pick']} ({user['dur']}/{user['max_dur']})")
    
    elif text == "!랭킹":
        top = sorted(user_data.items(), key=lambda x: x[1]['money'], reverse=True)[:10]
        rank_msg = "🏆 **코인 보유 랭킹**\n"
        for i, (n, d) in enumerate(top, 1): rank_msg += f"{i}위. @{n} : {d['money']:,} G\n"
        return update.message.reply_text(rank_msg)

# --- [콜백 쿼리 핸들러] ---
def handle_callback(update, context):
    q = update.callback_query; uid = q.from_user.username; user = get_user(uid)
    if not user: return
    
    if q.data.startswith("buy_"): # 구매 처리
        pk = q.data.split("_")[1]; info = PICKS[pk]
        if user['money'] >= info['p']:
            user['money'] -= info['p']; user['pick'] = pk; user['dur'] = info['d']; user['max_dur'] = info['d']
            q.edit_message_text(f"✅ **{pk} 곡괭이** 구매 완료! 즐거운 채광 되세요.")
        else: q.answer("코인이 부족합니다!", show_alert=True)
        
    elif q.data.startswith("s_"): # 판매 처리
        earn = 0
        if q.data == "s_all":
            for k in ORES: earn += user['inv'][k] * ORES[k]['p']; user['inv'][k] = 0
        else:
            t = int(q.data.split("_")[1])
            for k, v in ORES.items():
                if v['t'] == t: earn += user['inv'][k] * v['p']; user['inv'][k] = 0
        user['money'] += earn
        q.edit_message_text(f"💰 **판매 정산 완료**\n총 {earn:,} G가 입금되었습니다.")
    q.answer()

if __name__ == '__main__':
    keep_alive()
    TOKEN = "8771125252:AAFbKHLcDM2KhLR3MIp6ZGOnFQQWlIQUIlc"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(handle_callback))
    updater.start_polling(); updater.idle()
