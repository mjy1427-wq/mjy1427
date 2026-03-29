import random
import logging
import os
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CallbackQueryHandler, CallbackContext, MessageHandler, Filters

# 로그 설정 (Render 대시보드에서 확인 가능)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- [1. 기본 설정 및 관리자 정보] ---
TOKEN = "8603959168:AAH9Jq_5erWZgvocsvnjS1rP4G_F9VW-CbQ”
ADMIN_ID = 7476630349 

# 등급별 아이콘 설정 (이미지 UI 재현)
TIER_ICONS = {
    "신화": "◽", "환상": "◽", "전설": "⭐", "유니크": "🔹", "희귀": "🔸", "레어": "▫️", "일반": "▫️"
}

POKEMON_DB = {
    "루기아": {"tier": "전설", "atk": 130}, 
    "아르세우스": {"tier": "환상", "atk": 160},
    "뮤츠": {"tier": "신화", "atk": 154}, 
    "디아루가": {"tier": "신화", "atk": 150},
    "리자몽": {"tier": "유니크", "atk": 109}, 
    "피카츄": {"tier": "레어", "atk": 55}
}

# 유저 데이터 저장소 (실제 운영 시에는 DB 연결 권장)
user_data = {}
ban_list = set()

# Render 포트 체크 통과를 위한 가짜 웹 서버
app = Flask('')
@app.route('/')
def home(): return "Bot is Alive!"

def run_web():
    # Render의 환경변수 PORT를 사용하거나 기본 10000번 사용
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# --- [2. UI 마크업 함수] ---

def get_main_menu_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🍃 탐험하기", callback_data="menu_explore"), 
         InlineKeyboardButton("💻 포켓몬 관리 (PC)", callback_data="menu_pc")],
        [InlineKeyboardButton("💳 내 정보 (트레이너)", callback_data="menu_info"),
         InlineKeyboardButton("🎒 내 가방", callback_data="menu_bag")],
        [InlineKeyboardButton("🏪 상점", callback_data="menu_shop"),
         InlineKeyboardButton("💰 판매장", callback_data="menu_market")],
        [InlineKeyboardButton("📖 수집 도감", callback_data="menu_pokedex"),
         InlineKeyboardButton("🏆 랭킹", callback_data="menu_rank")],
        [InlineKeyboardButton("🎒 내 장비", callback_data="menu_equip"),
         InlineKeyboardButton("⚒️ 스타포스 강화", callback_data="menu_starforce")]
    ])

def get_pc_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 PC에 등록", callback_data="pc_reg_list"),
         InlineKeyboardButton("📤 PC에서 해제", callback_data="pc_del_list")],
        [InlineKeyboardButton("🔙 메인 메뉴", callback_data="menu_back")]
    ])

# --- [3. 핵심 로직 핸들러] ---

def handle_message(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    text = update.message.text
    if uid in ban_list: return 

    if text == ".가입":
        if uid in user_data: return update.message.reply_text("이미 등록된 트레이너입니다.")
        user_data[uid] = {
            "name": update.effective_user.first_name, "gold": 100000, 
            "pokes": [], "pc": [], "inv": {"슈퍼볼":0,"하이퍼볼":0,"마스터볼":0},
            "level": 1, "partner": None
        }
        return update.message.reply_text("🎊 가입 완료! `.메뉴`를 입력하세요.")

    user = user_data.get(uid)
    if not user: return

    # .pc, .탐험 등 유저 입력 시 메뉴 응답
    if text.startswith("."):
        if text == ".pc":
            refresh_pc_screen(update, user, is_message=True)
        else:
            msg = "🎮 **[ 포켓몬 월드 메인 메뉴 ]**\n\n원하시는 기능을 터치해 주세요!"
            update.message.reply_text(msg, reply_markup=get_main_menu_markup(), parse_mode='Markdown')

def callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    uid = query.from_user.id
    user = user_data.get(uid)
    if not user: return

    if query.data == "menu_pc":
        refresh_pc_screen(query, user)
    elif query.data == "menu_back":
        query.edit_message_text("🎮 **[ 포켓몬 월드 메인 메뉴 ]**", reply_markup=get_main_menu_markup(), parse_mode='Markdown')

# --- [4. 가방 숫자 자동화 적용된 PC 화면] ---

def refresh_pc_screen(target, user, is_message=False):
    slot_list = ""
    for p in user['pc']:
        icon = TIER_ICONS.get(p['tier'], "▫️")
        slot_list += f"{icon} {p['tier']} · B · {p['name']} Lv.{p['lv']}\n"
    
    # 가방 대기 숫자를 실제 데이터(len)로 계산 ㅡㅡ+
    pokes_count = len(user['pokes'])
    
    msg = (f"**[ 💻 PC · 포켓몬 관리 ]**\n"
           f"━━━━━━━━━━━━━━━━━━\n\n"
           f"**슬롯 {len(user['pc'])}/6**\n"
           f"{slot_list if slot_list else '비어 있음'}\n"
           f"━━━━━━━━━━━━━━━━━━\n\n"
           f"가방 대기 {pokes_count}마리\n"
           f"**PC에 올린 포켓몬만 파트너 지정 가능합니다.**")
    
    if is_message:
        target.message.reply_text(msg, reply_markup=get_pc_markup(), parse_mode='Markdown')
    else:
        target.edit_message_text(msg, reply_markup=get_pc_markup(), parse_mode='Markdown')

# --- [5. 메인 실행부] ---

def main():
    # Render 웹 서버 시작
    Thread(target=run_web).start()
    
    # 텔레그램 봇 시작
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(callback_handler))
    
    print("Bot is running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
