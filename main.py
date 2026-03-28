import logging, time, random, os, datetime
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler

app = Flask(''); ADMIN_ID = "EJ1427"
@app.route('/')
def home(): return "G-COIN BOT Online"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
def keep_alive(): Thread(target=run).start()

user_data = {}
baccarat_history = [] 

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

PICKS = {
    "Wood": {"p": 1000000, "d": 100},
    "Stone": {"p": 5000000, "d": 300},
    "Netherite": {"p": 1000000000, "d": 10000}
}

def get_user(uid):
    return user_data.get(uid)

def get_card(): return random.randint(1, 9)

def handle_message(update, context):
    uid = update.message.from_user.username
    if not uid: return
    text = update.message.text
    user = get_user(uid)

    # --- [1] 가입 및 명령어 안내 ---
    if text == "!가입":
        if uid in user_data: return update.message.reply_text("이미 가입된 계정입니다.")
        reg_date = datetime.datetime.now().strftime("%Y-%m-%d")
        user_data[uid] = {
            'money': 100000, 'pick': 'Wood', 'dur': 100, 'max_dur': 100,
            'inv': {k: 0 for k in ORES}, 'reg_date': reg_date, 'last_check': ""
        }
        update.message.reply_text(f"🎊 등록완료! 10만원과 기본 곡괭이 지급.\n(가입일자: {reg_date})")
        return

    # 가입하지 않은 유저는 아래 명령어를 인식하지 않도록 수정했습니다.
    if not user: return 

    if text == "!명령어":
        msg = ("📜 **전체 명령어**\n"
               "!가입, !내정보, !인벤, !출석, !채광, !판매, !상점\n"
               "!송금 [아이디] [금액]\n"
               "!플/!뱅/!타이 [금액], !바카라")
        update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    elif text == "!인벤":
        inv_msg = f"🎒 **@{uid}님의 인벤토리**\n\n"
        has_item = False
        for k, v in ORES.items():
            count = user['inv'][k]
            if count > 0:
                inv_msg += f"{v['n']} x{count}개 (개당 {v['p']:,} G)\n"
                has_item = True
        if not has_item: inv_msg += "비어 있음"
        update.message.reply_text(inv_msg, parse_mode=ParseMode.MARKDOWN)

    elif text == "!채광":
        if user['dur'] <= 0: return update.message.reply_text("🪓 내구도 부족!")
        user['dur'] -= 1
        rand = random.random() * 100; curr = 0; sel = "stone"
        for k, v in ORES.items():
            curr += v['c']; 
            if rand <= curr: sel = k; break
        user['inv'][sel] += 1
        msg = (f"⛏ **채광 완료!**\n\n⛏ 착용중인 곡괭이: {user['pick']}\n"
               f"💎 획득: {ORES[sel]['n']}\n💰 가치: {ORES[sel]['p']:,} 코인\n🔧 내구도: {user['dur']}/{user['max_dur']}")
        update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    # --- [2] 바카라 카드 연출 (결과 발표 시 이미지 전송 추가) ---
    elif any(text.startswith(x) for x in ["!플 ", "!뱅 ", "!타이 "]):
        try:
            bet_type = "P" if "!플" in text else ("B" if "!뱅" in text else "T")
            amt = int(text.split()[1])
            if amt > user['money'] or amt <= 0: return update.message.reply_text("금액 부족!")
            
            m = update.message.reply_text(f"🎲 배팅 완료! 15초 후 마감됩니다.")
            time.sleep(12); context.bot.edit_message_text("⚠️ 배팅 마감 3초 전!", chat_id=update.effective_chat.id, message_id=m.message_id)
            time.sleep(3); context.bot.edit_message_text("🚫 배팅 마감! 결과를 계산합니다...", chat_id=update.effective_chat.id, message_id=m.message_id)
            
            p_val, b_val = random.randint(0, 9), random.randint(0, 9)
            result = "P" if p_val > b_val else ("B" if b_val > p_val else "T")
            baccarat_history.append(result)
            if len(baccarat_history) > 270: baccarat_history.pop(0)

            # --- [수정된 카드 연출 - 이미지 전송] ---
            # 플레이어 카드 공개
            update.message.reply_photo(photo="https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/cards/player_open.png", caption=f"🃏 플레이어 카드 공개: 합 {p_val}")
            time.sleep(3)
            # 뱅커 카드 공개
            update.message.reply_photo(photo="https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/cards/banker_open.png", caption=f"🃏 뱅커 카드 공개: 합 {b_val}")
            
            # --- [합산 결과 및 정산] ---
            time.sleep(2)
            win_map = {"P": "플레이어🔴", "B": "뱅커🔵", "T": "타이🟢"}
            if bet_type == result:
                mult = 8 if result == "T" else 2
                user['money'] += (amt * (mult-1))
                res_text = f"✅ 축하합니다! {win_map[result]} 승리! +{amt*mult:,} G"
            else:
                user['money'] -= amt
                res_text = f"❌ 아쉽습니다.. {win_map[result]} 승리. -{amt:,} G"
            
            update.message.reply_text(f"🎰 **최종 결과: {p_val} vs {b_val}**\n{res_text}")
        except: update.message.reply_text("사용법: ![플/뱅/타이] [금액]")

    # --- [3] 바카라 그림장 수정 (가로 나열 방식) ---
    elif text == "!바카라":
        # 세 번째 이미지 스타일로 격자 무늬 구현
        board = [["⬜" for _ in range(6)] for _ in range(45)]
        for i, res in enumerate(baccarat_history):
            col, row = divmod(i, 45) # 가로로 나열하도록 수정
            if row < 6:
                board[col][row] = "🔵" if res == "B" else ("🔴" if res == "P" else " / ")
        
        display = "📊 **바카라 실시간 그림장**\n`"
        for r in range(6):
            display += "".join([board[c][r] for c in range(45)]) + "\n"
        display += "`"
        update.message.reply_text(display, parse_mode=ParseMode.MARKDOWN)

    # --- [4] 기타 기능 ---
    elif text == "!출석":
        today = datetime.datetime.now().strftime("%Y%m%d")
        if user['last_check'] == today: return update.message.reply_text("이미 출석하셨습니다.")
        user['money'] += 50000; user['last_check'] = today
        update.message.reply_text("✅ 5만원 지급 완료!")

    elif text == "!내정보":
        update.message.reply_text(f"👤 **@{uid}**\n💵 잔액: {user['money']:,} G\n⛏ 곡괭이: {user['pick']} ({user['dur']}/{user['max_dur']})")

    elif text.startswith("!송금"):
        try:
            p = text.split(); target = p[1].replace("@", ""); amt = int(p[2])
            if target in user_data and user['money'] >= amt:
                user['money'] -= amt; user_data[target]['money'] += amt
                update.message.reply_text(f"✅ @{target}에게 {amt:,} G 송금 완료.")
        except: pass

    elif text.startswith("!지급") and uid == ADMIN_ID:
        try:
            p = text.split(); target = p[1].replace("@",""); amt = int(p[2])
            user_data[target]['money'] += amt
            update.message.reply_text(f"✅ {target}에게 {amt:,} G 지급!")
        except: pass

def handle_callback(update, context):
    q = update.callback_query; uid = q.from_user.username; user = get_user(uid)
    if not user: return
    if q.data == "s_all":
        gain = sum(user['inv'][k] * ORES[k]['p'] for k in ORES)
        for k in ORES: user['inv'][k] = 0
        user['money'] += gain; q.edit_message_text(f"✅ 전체 판매 완료! +{gain:,} G")
    q.answer()

if __name__ == '__main__':
    keep_alive()
    TOKEN = "8771125252:AAFbKHLcDM2KhLR3MIp6ZGOnFQQWlIQUIlc"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(handle_callback))
    updater.start_polling(); updater.idle()
