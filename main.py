import logging
import time
import random
import os
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler

# --- [1] Flask 서버 유지 설정 ---
app = Flask('')

@app.route('/')
def home():
    return "G-Coin Bot is Online!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- [2] 데이터 및 설정 ---
user_data = {}
ORES = {
    "T1": {"name": "👑 전설의 핵", "price": 5000000, "chance": 1},
    "T2": {"name": "💎 다이아몬드", "price": 1000000, "chance": 5},
    "T3": {"name": "🥇 금광석", "price": 100000, "chance": 15},
    "T4": {"name": "🥈 은광석", "price": 50000, "chance": 30},
    "T5": {"name": "🪨 일반석", "price": 10000, "chance": 49}
}

def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            'money': 1000000,
            'durability': 100,
            'inventory': {k: 0 for k in ORES}
        }
    return user_data[user_id]

# --- [3] 메시지 처리 핸들러 ---
def handle_message(update, context):
    user_id = update.message.from_user.username
    if not user_id:
        update.message.reply_text("❌ 텔레그램 아이디(@username)가 설정되어 있어야 합니다.")
        return

    user = get_user(user_id)
    text = update.message.text

    # 명령어 안내
    if text == "!명령어":
        msg = (
            "━━━━━━━━━━━━━━\n"
            "💰 **G-COIN BOT 명령어**\n"
            "━━━━━━━━━━━━━━\n"
            "⛏ `!채광` - 광석 캐기 (내구도 -5)\n"
            "💰 `!내정보` - 잔액 및 보유 자산\n"
            "🛒 `!상점` - 곡괭이 수리 및 아이템\n"
            "🃏 `!플 [금액]` - 바카라 플레이어 승\n"
            "🃏 `!뱅 [금액]` - 바카라 뱅커 승\n"
            "🃏 `!타이 [금액]` - 바카라 타이 승\n"
            "━━━━━━━━━━━━━━"
        )
        update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    # 내 정보
    elif text == "!내정보":
        msg = (
            f"👤 **사용자**: @{user_id}\n"
            f"💵 **보유 잔액**: {user['money']:,} G\n"
            f"🛠 **곡괭이 내구도**: {user['durability']}%"
        )
        update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    # 채광 기능
    elif text == "!채광":
        if user['durability'] <= 0:
            update.message.reply_text("🪓 곡괭이가 부서졌습니다! !상점에서 수리하세요.")
            return
        
        user['durability'] -= 5
        rand = random.random() * 100
        current = 0
        selected_ore = "T5"
        
        for k, v in ORES.items():
            current += v['chance']
            if rand <= current:
                selected_ore = k
                break
        
        user['inventory'][selected_ore] += 1
        user['money'] += ORES[selected_ore]['price']
        
        update.message.reply_text(
            f"⛏ **채광 성공!**\n"
            f"💎 획득: {ORES[selected_ore]['name']}\n"
            f"💰 판매가: {ORES[selected_ore]['price']:,} G 획득!\n"
            f"📉 내구도: {user['durability']}% 남음"
        )
            # 바카라 기능 (플레이어, 뱅커, 타이)
    elif any(text.startswith(x) for x in ["!플", "!뱅", "!타이"]):
        try:
            split_text = text.split()
            if len(split_text) < 2:
                return update.message.reply_text("❌ 사용법: !플 [금액]")
            
            bet_amount = int(split_text[1])
            if bet_amount <= 0 or bet_amount > user['money']:
                return update.message.reply_text("❌ 잔액이 부족하거나 잘못된 금액입니다.")

            # 카드 뽑기 (1~9)
            p_card = random.randint(1, 9)
            b_card = random.randint(1, 9)
            
            if p_card > b_card:
                winner = "플레이어"
            elif b_card > p_card:
                winner = "뱅커"
            else:
                winner = "타이"

            # 승패 확인
            is_win = False
            multiplier = 2
            if text.startswith("!플") and winner == "플레이어":
                is_win = True
            elif text.startswith("!뱅") and winner == "뱅커":
                is_win = True
            elif text.startswith("!타이") and winner == "타이":
                is_win = True
                multiplier = 8

            if is_win:
                user['money'] += (bet_amount * (multiplier - 1))
                update.message.reply_text(f"🎲 **결과: [{p_card} vs {b_card}] {winner} 승!**\n✅ 축하합니다! {bet_amount * multiplier:,} G를 획득했습니다!")
            else:
                user['money'] -= bet_amount
                update.message.reply_text(f"🎲 **결과: [{p_card} vs {b_card}] {winner} 승!**\n❌ 아쉽네요. {bet_amount:,} G를 잃었습니다.")
        except ValueError:
            update.message.reply_text("❌ 금액은 숫자로 입력해주세요.")

    # 상점 기능
    elif text == "!상점":
        keyboard = [[InlineKeyboardButton("🔧 곡괭이 전체 수리 (100,000 G)", callback_data='repair')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("🛒 **G-COIN 상점**\n수리하시겠습니까?", reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

# --- [4] 콜백 핸들러 (버튼 처리) ---
def handle_callback(update, context):
    query = update.callback_query
    user_id = query.from_user.username
    user = get_user(user_id)

    if query.data == 'repair':
        if user['money'] >= 100000:
            user['money'] -= 100000
            user['durability'] = 100
            query.answer("수리 완료!")
            query.edit_message_text(f"✅ 수리가 완료되었습니다! (현재 잔액: {user['money']:,} G)")
        else:
            query.answer("잔액 부족!", show_alert=True)

# --- [5] 메인 실행부 ---
if __name__ == '__main__':
    keep_alive()  # Flask 서버 시작
    
    TOKEN = "8771125252:AAFbKHLcDM2KhLR3MIp6ZGOnFQQWlIQUIlc"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # 핸들러 등록
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(handle_callback))

    print("Bot is running...")
    updater.start_polling()
    updater.idle()
