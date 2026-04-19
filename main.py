import logging
import json
import os
import random
from datetime import datetime
from threading import Thread
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# --- [1. Render Free 티어 24시간 가동을 위한 웹서버] ---
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "서버 상태: 정상 가동 중 (24/7)"

def run():
    app_flask.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- [2. 게임 설정 및 고정 데이터] ---
ADMIN_HANDLE = "EJ1427"
TOKEN = "8484299407:AAEFUmF3brlAfWMN3Cn1NFT1oTjB3EByIzw"
OFFICIAL_CHANNEL_URL = "https://t.me/your_channel" # 관리자 채널 주소

DATA_FILE = "user_data.json"
ROOMS_FILE = "active_rooms.json"

users = {}
active_rooms = set()
hot_time_coin = False
hot_time_prob = False

def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)
    with open(ROOMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(active_rooms), f)

def load_data():
    global users, active_rooms
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
    if os.path.exists(ROOMS_FILE):
        with open(ROOMS_FILE, 'r', encoding='utf-8') as f:
            active_rooms = set(json.load(f))

# --- [3. 마침표(.) 명령어 처리 엔진] ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    text = update.message.text.strip()
    uid = str(update.effective_user.id)
    active_rooms.add(update.effective_chat.id)

    # .가입 명령어
    if text == ".가입":
        if uid in users:
            await update.message.reply_text("이미 수행자로 등록되어 있습니다. `.메뉴`를 입력하세요.")
            return
        users[uid] = {
            "name": update.effective_user.first_name,
            "coin": 100000,
            "items": {"태을기문령": 20, "진화석": 0, "영혼의조각": 0, "하급영양제": 0, "상급영양제": 0},
            "pets": [{"name": "아기청룡", "lv": 1, "exp": 0, "grade": "C", "awakened": False}],
            "main_pet_idx": 0,
            "equipped_amulet": "태을기문령",
            "last_attendance": ""
        }
        save_data()
        await update.message.reply_text("⛩️ **수행자 등록 완료**\n💰 초기 자산: 100,000 G\n📜 보급 부적: 20장", parse_mode="Markdown")

    # .메뉴 명령어
    elif text == ".메뉴":
        if uid not in users:
            await update.message.reply_text("`.가입`을 먼저 진행해주세요.")
            return
        keyboard = [
            [InlineKeyboardButton("⚔️ 사냥터", callback_data="hunt_menu"), InlineKeyboardButton("🎒 내 가방", callback_data="bag_menu")],
            [InlineKeyboardButton("🐾 영수목록", callback_data="pet_list"), InlineKeyboardButton("🏯 부적상점", callback_data="shop_menu")],
            [InlineKeyboardButton("🏛️ 거래소", callback_data="market"), InlineKeyboardButton("📖 봉신도감", callback_data="book")],
            [InlineKeyboardButton("📅 출석체크", callback_data="attendance"), InlineKeyboardButton("🏆 명예전당", callback_data="rankings")],
            [InlineKeyboardButton("🌑 비밀 암시장", callback_data="black_market"), InlineKeyboardButton("❓ 도움말", callback_data="help")],
            [InlineKeyboardButton("📢 공식 채널 바로가기", url=OFFICIAL_CHANNEL_URL)]
        ]
        await update.message.reply_text("⛩️ **봉신연의 로비**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # .관리자모드 명령어
    elif text == ".관리자모드":
        if str(update.effective_user.username) != ADMIN_HANDLE: return
        s_c = "ON" if hot_time_coin else "OFF"
        s_p = "ON" if hot_time_prob else "OFF"
        keyboard = [
            [InlineKeyboardButton(f"💰 코인 핫타임 {s_c}", callback_data="t_c"), InlineKeyboardButton(f"✨ 확률 핫타임 {s_p}", callback_data="t_p")],
            [InlineKeyboardButton("📢 공지 날리기", callback_data="adm_notice")]
        ]
        await update.message.reply_text(f"**[ 🛠️ 관리자 패널 ]**\n🌐 방: {len(active_rooms)}개 | 👥 유저: {len(users)}명", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- [4. 콜백/버튼 처리 로직] ---
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    user = users.get(uid)
    if not user: return

    if query.data == "hunt_menu":
        keyboard = [[InlineKeyboardButton("🌿 청운의 숲", callback_data="do_hunt")], [InlineKeyboardButton("🏠 로비", callback_data="main_menu_cb")]]
        await query.edit_message_text(f"⚔️ 사냥 구역을 선택하세요. (장착: {user['equipped_amulet']})", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == "do_hunt":
        if user["items"]["태을기문령"] <= 0:
            await query.answer("부적이 부족합니다!", show_alert=True); return
        user["items"]["태을기문령"] -= 1
        success = random.randint(1, 100) <= (30 + (5 if hot_time_prob else 0))
        if success:
            gain = 50000 * (2 if hot_time_coin else 1)
            user["coin"] += gain
            msg = f"✨ **봉인 성공!**\n💰 획득: {gain:,} G코인"
        else: msg = "💨 **봉인 실패...** 영수가 달아났습니다."
        save_data()
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚔️ 다시 사냥", callback_data="hunt_menu")]]), parse_mode="Markdown")

    elif query.data == "rankings":
        sorted_users = sorted(users.items(), key=lambda x: x[1]['coin'], reverse=True)[:10]
        text = "🏆 **명예의 전당 (TOP 10)**\n"
        for i, (u_id, d) in enumerate(sorted_users, 1):
            text += f"{i}위. {d['name']} | 💰 {d['coin']:,} G\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 로비", callback_data="main_menu_cb")]]), parse_mode="Markdown")

    elif query.data in ["t_c", "t_p"]:
        global hot_time_coin, hot_time_prob
        if query.data == "t_c":
            hot_time_coin = not hot_time_coin
            msg = "📢 **[핫타임 시작]** 코인 보상 2배!" if hot_time_coin else "📢 **[핫타임 종료]** 보상이 정상화되었습니다."
        else:
            hot_time_prob = not hot_time_prob
            msg = "📢 **[확률 UP 시작]** 봉인 확률 증가!" if hot_time_prob else "📢 **[확률 UP 종료]** 확률이 정상화되었습니다."
        for r in active_rooms:
            try: await context.bot.send_message(r, msg, parse_mode="Markdown")
            except: pass
        await query.answer("서버 상태가 변경되었습니다.")

    elif query.data == "main_menu_cb":
        # .메뉴와 동일한 키보드 띄우기
        keyboard = [[InlineKeyboardButton("⚔️ 사냥터", callback_data="hunt_menu"), InlineKeyboardButton("🎒 내 가방", callback_data="bag_menu")], [InlineKeyboardButton("🐾 영수목록", callback_data="pet_list"), InlineKeyboardButton("🏯 부적상점", callback_data="shop_menu")], [InlineKeyboardButton("🏆 명예전당", callback_data="rankings")]]
        await query.edit_message_text("⛩️ **봉신연의 로비**", reply_markup=InlineKeyboardMarkup(keyboard))

# --- [5. 메인 서버 실행] ---
def main():
    load_data()
    keep_alive() # 웹서버 가동
    
    app = Application.builder().token(TOKEN).build()

    # 모든 텍스트를 감시하여 마침표 명령어 인식
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    # 버튼 클릭 처리
    app.add_handler(CallbackQueryHandler(callback_handler))

    print("🚀 서버 가동 완료: 봉신연의의 문이 열렸습니다.")
    app.run_polling()

if __name__ == "__main__":
    main()
