import random
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CallbackQueryHandler, CallbackContext, MessageHandler, Filters

# 로그 설정 (Render 로그에서 확인 가능)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- [1. 기본 설정 및 관리자 정보] --- ㅡㅡ+
TOKEN = "8771125252:AAFbKHLcDM2KhLR3MIp6ZGOnFQQWlIQUIlc"
ADMIN_ID = 7476630349 

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

user_data = {}
ban_list = set()

def get_user(uid): return user_data.get(uid)

# --- [2. UI 생성 함수] ---

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

# --- [3. 핸들러 로직] ---

def handle_message(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    text = update.message.text
    if uid in ban_list: return 

    if text == ".가입":
        if uid in user_data: return update.message.reply_text("이미 등록됨.")
        user_data[uid] = {"name": update.effective_user.first_name, "gold": 100000, "pokes": [], "pc": [], "inv": {"슈퍼볼":0,"하이퍼볼":0,"마스터볼":0}, "catch_count": 0, "level": 1, "exp": 0, "partner": None}
        return update.message.reply_text("🎊 가입 완료! `.메뉴`를 입력하세요.")

    user = get_user(uid)
    if not user: return

    if text == ".메뉴" or text == ".pc" or text == ".탐험": # 이미지 속 명령어들 대응 ㅡㅡ+
        msg = "🎮 **[ 포켓몬 월드 메인 메뉴 ]**\n\n원하시는 기능을 터치해 주세요!"
        update.message.reply_text(msg, reply_markup=get_main_menu_markup(), parse_mode='Markdown')

    # 관리자 전용 권능 ㅡㅡ+
    elif uid == ADMIN_ID and text.startswith("."):
        parts = text.split()
        cmd = parts[0][1:]
        args = parts[1:]
        if cmd == "관리자지급":
            try:
                target_id, amt = int(args[0]), int(args[1])
                user_data[target_id]['gold'] += amt
                update.message.reply_text(f"💰 {target_id}에게 {amt:,}G 지급!")
            except: pass
        elif cmd == "차단":
            try:
                target_id, del_rec = int(args[0]), int(args[1])
                ban_list.add(target_id)
                if del_rec == 1 and target_id in user_data: del user_data[target_id]
                update.message.reply_text(f"🚫 {target_id} 차단 완료.")
            except: pass

def callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    uid = query.from_user.id
    user = get_user(uid)
    data = query.data
    if not user or uid in ban_list: return

    if data == "menu_pc":
        refresh_pc_screen(query, user)
    elif data == "menu_back":
        query.edit_message_text("🎮 **[ 포켓몬 월드 메인 메뉴 ]**", reply_markup=get_main_menu_markup(), parse_mode='Markdown')
    elif data == "pc_reg_list":
        if len(user['pc']) >= 6: return query.answer("슬롯 풀!", show_alert=True)
        btns = [[InlineKeyboardButton(f"{p['name']} 등록", callback_data=f"pcreg_{i}")] for i, p in enumerate(user['pokes']) if p not in user['pc']]
        query.edit_message_text("📥 등록할 포켓몬 선택:", reply_markup=InlineKeyboardMarkup(btns + [[InlineKeyboardButton("⬅️ 뒤로", callback_data="menu_pc")]]))
    elif data.startswith("pcreg_"):
        idx = int(data.split("_")[1])
        user['pc'].append(user['pokes'][idx])
        refresh_pc_screen(query, user)
    elif data == "menu_info":
        query.answer(f"💰 골드: {user['gold']:,}G\n🏆 레벨: {user['level']}", show_alert=True)

def refresh_pc_screen(query, user):
    slot_list = ""
    for p in user['pc']:
        icon = TIER_ICONS.get(p['tier'], "▫️")
        slot_list += f"{icon} {p['tier']} · B · {p['name']} Lv.{p['lv']}\n"
    msg = (f"**[ 💻 PC · 포켓몬 관리 ]**\n━━━━━━━━━━━━━━━━━━\n\n**슬롯 {len(user['pc'])}/6**\n"
           f"{slot_list if slot_list else '비어 있음'}\n━━━━━━━━━━━━━━━━━━\n\n가방 대기 {len(user['pokes'])}마리\n"
           f"**PC에 올린 포켓몬만 파트너 지정 가능합니다.**")
    query.edit_message_text(msg, reply_markup=get_pc_markup(), parse_mode='Markdown')

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(callback_handler))
    
    # Render 환경에서 중요한 부분 ㅡㅡ+
    print("Bot is running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
