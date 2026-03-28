
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
baccarat_history = [] # 바카라 결과 저장 (최대 270개: 45칸 * 6줄)

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
    if uid not in user_data: return None
    return user_data[uid]

def handle_message(update, context):
    uid = update.message.from_user.username
    if not uid: return
    text = update.message.text
    user = get_user(uid)

    # --- [1] 가입 기능 ---
    if text == "!가입":
        if uid in user_data: return update.message.reply_text("이미 가입된 계정입니다.")
        reg_date = datetime.datetime.now().strftime("%Y-%m-%d")
        user_data[uid] = {
            'money': 100000, 'pick': 'Wood', 'dur': 100, 'max_dur': 100,
            'inv': {k: 0 for k in ORES}, 'reg_date': reg_date, 'last_check': ""
        }
        update.message.reply_text(f"🎊 등록완료! 10만원과 기본 곡괭이가 지급되었습니다.\n(가입일자: {reg_date})")
        return

    if not user: return # 가입 안 한 유저 무시

    # --- [2] 기본 명령어 ---
    if text == "!명령어":
        msg = ("📜 **전체 명령어**\n"
               "!가입, !내정보, !출석, !채광, !판매, !상점\n"
               "!송금 [아이디] [금액]\n"
               "!플/!뱅/!타이 [금액], !바카라")
        update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    elif text == "!출석":
        today = datetime.datetime.now().strftime("%Y%m%d")
        if user['last_check'] == today: return update.message.reply_text("이미 오늘 출석체크를 하셨습니다.")
        user['money'] += 50000; user['last_check'] = today
        update.message.reply_text("✅ 출석체크 완료! 5만원이 지급되었습니다.")

    elif text == "!내정보":
        update.message.reply_text(f"👤 **@{uid}**\n💵 잔액: {user['money']:,} G\n⛏ 곡괭이: {user['pick']} ({user['dur']}/{user['max_dur']})\n📅 가입일: {user['reg_date']}")

    # --- [3] 송금 기능 ---
    elif text.startswith("!송금"):
        try:
            p = text.split(); target = p[1].replace("@", ""); amt = int(p[2])
            if amt <= 0 or user['money'] < amt: return update.message.reply_text("잔액이 부족하거나 잘못된 금액입니다.")
            if target not in user_data: return update.message.reply_text("대상을 찾을 수 없습니다.")
            user['money'] -= amt; user_data[target]['money'] += amt
            update.message.reply_text(f"✅ @{target}님에게 {amt:,} G를 송금했습니다.")
        except: update.message.reply_text("❌ 사용법: !송금 [아이디] [금액]")

    # --- [4] 채광 기능 (내구도 1 소모) ---
    elif text == "!채광":
        if user['dur'] <= 0: return update.message.reply_text("🪓 곡괭이 내구도가 없습니다! 상점을 이용하세요.")
        user['dur'] -= 1
        rand = random.random() * 100; curr = 0; sel = "stone"
        for k, v in ORES.items():
            curr += v['c']
            if rand <= curr: sel = k; break
        user['inv'][sel] += 1
        update.message.reply_text(f"⛏ **{ORES[sel]['n']}** 획득!\n🔧 내구도: {user['dur']}/{user['max_dur']}")

    # --- [5] 바카라 게임 로직 ---
    elif any(text.startswith(x) for x in ["!플 ", "!뱅 ", "!타이 "]):
        try:
            bet_type = "P" if "!플" in text else ("B" if "!뱅" in text else "T")
            amt = int(text.split()[1])
            if amt > user['money'] or amt <= 0: return update.message.reply_text("금액 부족!")
            
            msg = update.message.reply_text(f"🎲 배팅 완료! 15초 후 마감됩니다.")
            time.sleep(12); context.bot.edit_message_text("⚠️ 배팅 마감 3초 전!", chat_id=update.effective_chat.id, message_id=msg.message_id)
            time.sleep(3); context.bot.edit_message_text("🚫 배팅 마감! 결과를 계산합니다...", chat_id=update.effective_chat.id, message_id=msg.message_id)
            time.sleep(3)

            p_val, b_val = random.randint(0, 9), random.randint(0, 9)
            result = "P" if p_val > b_val else ("B" if b_val > p_val else "T")
            baccarat_history.append(result)
            if len(baccarat_history) > 270: baccarat_history.pop(0)

            win_map = {"P": "플레이어🔴", "B": "뱅커🔵", "T": "타이🟢"}
            is_win = (bet_type == result)
            if is_win:
                mult = 8 if result == "T" else 2
                user['money'] += (amt * (mult-1))
                final_msg = f"🎰 결과: {win_map[result]} [{p_val} vs {b_val}]\n✅ 축하합니다! {amt*mult:,} G 획득!"
            else:
                user['money'] -= amt
                final_msg = f"🎰 결과: {win_map[result]} [{p_val} vs {b_val}]\n❌ 아쉽습니다.. {amt:,} G 손실."
            update.message.reply_text(final_msg)
        except: update.message.reply_text("❌ 사용법: ![플/뱅/타이] [금액]")

    elif text == "!바카라":
        # 그림장 구현 (가로 45칸, 세로 6줄)
        board = [["⬜" for _ in range(45)] for _ in range(6)]
        for i, res in enumerate(baccarat_history):
            col, row = divmod(i, 6)
            if col < 45:
                char = "🔴" if res == "P" else ("🔵" if res == "B" else " / ")
                # 연속 타이 처리 (간략화: 타이 발생 시 슬러시 표시)
                board[row][col] = char
        
        display = "📊 **바카라 최근 결과 (그림장)**\n"
        for r in range(6):
            display += "".join(board[r]) + "\n"
        update.message.reply_text(f"`{display}`", parse_mode=ParseMode.MARKDOWN)

    # --- [6] 상점 및 기타 ---
    elif text == "!상점":
        msg = "⛏ **곡괭이 상점**\n" + "\n".join([f"{k}: {v['p']:,} G" for k, v in PICKS.items()])
        kb = [[InlineKeyboardButton(f"{k} 구매", callback_data=f"buy_{k}")] for k in PICKS.keys()]
        update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))

    elif text == "!판매":
        kb = [[InlineKeyboardButton("💰 전체 판매", callback_data="s_all")]]
        update.message.reply_text("보유한 모든 광물을 판매하시겠습니까?", reply_markup=InlineKeyboardMarkup(kb))

# --- [콜백 및 실행부 생략 - 이전 구조와 동일하게 유지] ---
def handle_callback(update, context):
    q = update.callback_query; uid = q.from_user.username; user = get_user(uid)
    if not user: return
    if q.data.startswith("buy_"):
        pk = q.data.split("_")[1]; info = PICKS[pk]
        if user['money'] >= info['p']:
            user['money'] -= info['p']; user['pick'] = pk
            user['dur'] = info['d']; user['max_dur'] = info['d']
            q.edit_message_text(f"✅ {pk} 구매 완료!")
        else: q.answer("잔액 부족!", show_alert=True)
    elif q.data == "s_all":
        gain = sum(user['inv'][k] * ORES[k]['p'] for k in ORES)
        for k in ORES: user['inv'][k] = 0
        user['money'] += gain; q.edit_message_text(f"✅ 판매 완료! +{gain:,} G")
    q.answer()

if __name__ == '__main__':
    keep_alive()
    TOKEN = "8771125252:AAFbKHLcDM2KhLR3MIp6ZGOnFQQWlIQUIlc"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(handle_callback))
    updater.start_polling(); updater.idle()
