import logging
import json
import os
import random
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- [설정 및 데이터 관리] ---
ADMIN_HANDLE = "EJ1427" 
TOKEN = "8484299407:AAHgLqmlVS2cMG5_zYUJSTNjbb7KJBxGLks" 
OFFICIAL_CHANNEL_URL = "https://t.me/GCOIN7777"

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

# --- [1. 가입 및 메인 메뉴] ---

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    active_rooms.add(update.effective_chat.id)
    if uid in users:
        await update.message.reply_text("이미 수행자로 등록되어 있습니다.")
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
    await update.message.reply_text("⛩️ **수행자 등록 완료**\n보상: 10만 G / 태을기문령 20장", parse_mode="Markdown")

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("⚔️ 사냥터", callback_data="hunt_menu"), InlineKeyboardButton("🎒 내 가방", callback_data="bag_menu")],
        [InlineKeyboardButton("🐾 영수목록", callback_data="pet_list"), InlineKeyboardButton("🏯 부적상점", callback_data="shop_menu")],
        [InlineKeyboardButton("🏛️ 거래소", callback_data="market"), InlineKeyboardButton("📖 봉신도감", callback_data="book")],
        [InlineKeyboardButton("📅 출석체크", callback_data="attendance"), InlineKeyboardButton("🏆 명예전당", callback_data="rankings")],
        [InlineKeyboardButton("🌑 비밀 암시장", callback_data="black_market"), InlineKeyboardButton("❓ 도움말", callback_data="help")],
        [InlineKeyboardButton("📢 공식 채널 바로가기", url=OFFICIAL_CHANNEL_URL)]
    ]
    text = "⛩️ **봉신연의 로비**"
    if query: await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else: await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- [2. 사냥터 및 부적 상점] ---

async def hunt_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    user = users[uid]
    keyboard = [
        [InlineKeyboardButton("🌿 청운의 숲 (C)", callback_data="do_hunt_C")],
        [InlineKeyboardButton("🌑 안개 낀 골짜기 (B)", callback_data="do_hunt_B")],
        [InlineKeyboardButton("🔥 타오르는 고원 (A)", callback_data="do_hunt_A")],
        [InlineKeyboardButton("🏠 로비로", callback_data="main_menu")]
    ]
    await query.edit_message_text(f"⚔️ **사냥 지역 선택**\n현재 장착 부적: {user['equipped_amulet']}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def do_hunt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    user = users[uid]
    amulet = user["equipped_amulet"]

    if user["items"].get(amulet, 0) <= 0:
        await query.answer("부적이 부족합니다!", show_alert=True)
        return

    user["items"][amulet] -= 1
    success_rate = 30 + (5 if hot_time_prob else 0)
    
    if random.randint(1, 100) <= success_rate:
        gain = 50000 * (2 if hot_time_coin else 1)
        user["coin"] += gain
        msg = f"✨ **봉인 성공!**\n💰 획득: {gain:,} G코인"
    else:
        msg = "💨 **봉인 실패...**\n영수가 달아났습니다."
    
    save_data()
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚔️ 재탐색", callback_data="hunt_menu")]]), parse_mode="Markdown")

async def shop_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text = "🏯 **부적 상점**\n\n1. 태을기문령: 1만G\n2. 하급 영양제: 500만G\n3. 상급 영양제: 1,000만G"
    keyboard = [
        [InlineKeyboardButton("📜 태을기문령 구매", callback_data="buy_amulet_1")],
        [InlineKeyboardButton("🧪 하급 영양제 구매", callback_data="buy_nut_1")],
        [InlineKeyboardButton("🏠 로비", callback_data="main_menu")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- [3. 가방 및 명예전당] ---

async def bag_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = users[str(query.from_user.id)]
    text = f"🎒 **수행자 가방**\n💰 코인: {user['coin']:,} G\n\n"
    for item, count in user["items"].items():
        text += f"▫️ {item}: {count}개\n"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 로비", callback_data="main_menu")]]), parse_mode="Markdown")

async def attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    today = datetime.now().strftime("%Y-%m-%d")
    if users[uid]["last_attendance"] == today:
        await query.answer("이미 오늘 출석체크를 완료했습니다!", show_alert=True)
    else:
        users[uid]["last_attendance"] = today
        users[uid]["items"]["태을기문령"] += 10
        save_data()
        await query.edit_message_text("⛩️ **오늘의 수행 보급**\n출석 보상으로 **태을기문령 10장**을 획득하였습니다.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 로비", callback_data="main_menu")]]), parse_mode="Markdown")

async def rankings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    sorted_users = sorted(users.items(), key=lambda x: x[1]['coin'], reverse=True)[:10]
    text = "🏆 **명예의 전당 (G코인 부유자)**\n━━━━━━━━━━━━━━━━━━━━\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        pet = data["pets"][data["main_pet_idx"]]["name"] if data["main_pet_idx"] is not None else "없음"
        text += f"{i}위. {data['name']} | 💰 {data['coin']:,} G\n🐾 {pet}\n\n"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 로비", callback_data="main_menu")]]), parse_mode="Markdown")

# --- [4. 관리자 시스템] ---

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.username) != ADMIN_HANDLE: return
    s_c = "ON" if hot_time_coin else "OFF"
    s_p = "ON" if hot_time_prob else "OFF"
    text = f"**[ 🛠️ 관리자 패널 ]**\n🌐 방: {len(active_rooms)}개\n💰 코인: {s_c} | ✨ 확률: {s_p}"
    keyboard = [
        [InlineKeyboardButton(f"💰 코인 핫타임 {s_c}", callback_data="t_c"), InlineKeyboardButton(f"✨ 확률 핫타임 {s_p}", callback_data="t_p")],
        [InlineKeyboardButton("📢 공지", callback_data="adm_n"), InlineKeyboardButton("🏠 로비", callback_data="main_menu")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def toggle_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global hot_time_coin, hot_time_prob
    query = update.callback_query
    if query.data == "t_c":
        hot_time_coin = not hot_time_coin
        msg = "📢 **[공지]** 핫타임 시작 (코인 2배)!" if hot_time_coin else "📢 **[공지]** 핫타임 종료!"
    else:
        hot_time_prob = not hot_time_prob
        msg = "📢 **[공지]** 확률 UP 이벤트 시작!" if hot_time_prob else "📢 **[공지]** 확률 UP 종료!"
    for r in active_rooms:
        try: await context.bot.send_message(r, msg, parse_mode="Markdown")
        except: pass
    await query.answer("적용 완료")

# --- [메인 실행] ---
def main():
    load_data()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("가입", register))
    app.add_handler(CommandHandler("메뉴", main_menu))
    app.add_handler(CommandHandler("관리자모드", admin_panel))
    app.add_handler(CallbackQueryHandler(main_menu, pattern="main_menu"))
    app.add_handler(CallbackQueryHandler(hunt_menu, pattern="hunt_menu"))
    app.add_handler(CallbackQueryHandler(do_hunt, pattern="^do_hunt_"))
    app.add_handler(CallbackQueryHandler(bag_menu, pattern="bag_menu"))
    app.add_handler(CallbackQueryHandler(shop_menu, pattern="shop_menu"))
    app.add_handler(CallbackQueryHandler(attendance, pattern="attendance"))
    app.add_handler(CallbackQueryHandler(rankings, pattern="rankings"))
    app.add_handler(CallbackQueryHandler(toggle_event, pattern="^t_"))
    app.run_polling()

if __name__ == "__main__":
    main()
