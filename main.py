import logging
import json
import os
import random
from datetime import datetime
from threading import Thread
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# --- [1. Render 포트 감지용 웹서버] ---
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "봉신연의 서버 가동 중"

def run():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- [2. 설정] ---
ADMIN_HANDLE = "EJ1427"
TOKEN = "여기에_너_새토큰_넣어라"  # ⚠️ 절대 깃허브에 그대로 올리지 마
OFFICIAL_CHANNEL_URL = "https://t.me/your_channel"

DATA_FILE = "user_data.json"
ROOMS_FILE = "active_rooms.json"

users = {}
active_rooms = set()

# 🔥 전역 변수 (여기서만 선언)
hot_time_coin = False
hot_time_prob = False

# --- 데이터 ---
def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)
    with open(ROOMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(active_rooms), f)

def load_data():
    global users, active_rooms
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                users = json.load(f)
        except:
            users = {}

    if os.path.exists(ROOMS_FILE):
        try:
            with open(ROOMS_FILE, 'r', encoding='utf-8') as f:
                active_rooms = set(json.load(f))
        except:
            active_rooms = set()

# --- 메시지 처리 ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global hot_time_coin, hot_time_prob

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    uid = str(update.effective_user.id)
    active_rooms.add(update.effective_chat.id)

    if text == ".가입":
        if uid in users:
            await update.message.reply_text("이미 등록됨")
            return

        users[uid] = {
            "name": update.effective_user.first_name,
            "coin": 100000,
            "items": {"태을기문령": 20},
        }
        save_data()
        await update.message.reply_text("가입 완료")

    elif text == ".메뉴":
        if uid not in users:
            return

        keyboard = [
            [InlineKeyboardButton("⚔️ 사냥", callback_data="hunt")],
            [InlineKeyboardButton("📢 채널", url=OFFICIAL_CHANNEL_URL)]
        ]
        await update.message.reply_text("메뉴", reply_markup=InlineKeyboardMarkup(keyboard))

    elif text == ".관리자모드":
        if str(update.effective_user.username) != ADMIN_HANDLE:
            return

        s_c = "ON" if hot_time_coin else "OFF"
        s_p = "ON" if hot_time_prob else "OFF"

        keyboard = [[
            InlineKeyboardButton(f"코인 {s_c}", callback_data="t_c"),
            InlineKeyboardButton(f"확률 {s_p}", callback_data="t_p")
        ]]
        await update.message.reply_text("관리자", reply_markup=InlineKeyboardMarkup(keyboard))

# --- 콜백 ---
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global hot_time_coin, hot_time_prob

    query = update.callback_query
    await query.answer()

    uid = str(query.from_user.id)
    user = users.get(uid)

    if not user:
        return

    if query.data == "hunt":
        if user["items"]["태을기문령"] <= 0:
            await query.edit_message_text("아이템 부족")
            return

        user["items"]["태을기문령"] -= 1

        success_rate = 30 + (5 if hot_time_prob else 0)
        success = random.randint(1, 100) <= success_rate

        gain = 50000 * (2 if hot_time_coin else 1) if success else 0
        user["coin"] += gain

        save_data()

        await query.edit_message_text(
            f"{'성공 +' + str(gain) if success else '실패'}"
        )

    elif query.data == "t_c":
        hot_time_coin = not hot_time_coin

    elif query.data == "t_p":
        hot_time_prob = not hot_time_prob

# --- 메인 ---
def main():
    load_data()
    keep_alive()  # 🔥 먼저 서버 켜기

    app = Application.builder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(callback_handler))

    print("서버 실행중")
    app.run_polling()

if __name__ == "__main__":
    main()
