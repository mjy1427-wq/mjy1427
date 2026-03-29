import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CallbackQueryHandler, CallbackContext, MessageHandler, Filters

# --- [1. 기본 설정 및 관리자 정보] ---
TOKEN = "여기에_봇_토큰_입력"
ADMIN_ID = 12345678  # 관리자님 ID ㅡㅡ+

# 포켓몬 데이터베이스 (1~4세대 혼합)
POKEMON_DB = {
    "뮤츠": {"tier": "신화", "atk": 154}, "아르세우스": {"tier": "신화", "atk": 160},
    "디아루가": {"tier": "신화", "atk": 150}, "펄기아": {"tier": "신화", "atk": 150},
    "레쿠쟈": {"tier": "신화", "atk": 150}, "망나뇽": {"tier": "전설", "atk": 134},
    "한카리아스": {"tier": "전설", "atk": 130}, "메타그로스": {"tier": "전설", "atk": 135},
    "리자몽": {"tier": "유니크", "atk": 109}, "루카리오": {"tier": "유니크", "atk": 115},
    "갸라도스": {"tier": "유니크", "atk": 125}, "잠만보": {"tier": "희귀", "atk": 110},
    "피카츄": {"tier": "레어", "atk": 55}, "이브이": {"tier": "레어", "atk": 55},
    "비버니": {"tier": "일반", "atk": 40}, "구구": {"tier": "일반", "atk": 45}
}

# 상점 볼 설정
BALL_CONFIG = {
    "몬스터볼": {"price": 0, "rate": 30},
    "슈퍼볼": {"price": 50000, "rate": 50},
    "하이퍼볼": {"price": 200000, "rate": 80},
    "마스터볼": {"price": 5000000, "rate": 100}
}

user_data = {}
ban_list = set() # 차단 유저 목록 ㅡㅡ+

def get_user(uid): return user_data.get(uid)

# --- [2. UI 생성 함수 (이미지 기반)] ---

# 메인 메뉴 마크업
def get_main_menu_markup():
    keyboard = [
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
    ]
    return InlineKeyboardMarkup(keyboard)

# PC 관리 마크업
def get_pc_markup():
    keyboard = [
        [InlineKeyboardButton("📥 PC에 등록", callback_data="pc_reg_list"),
         InlineKeyboardButton("📤 PC에서 해제", callback_data="pc_del_list")],
        [InlineKeyboardButton("⬅️ 메인 메뉴", callback_data="menu_back")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- [3. 메시지 핸들러 (명령어)] ---

def handle_message(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    text = update.message.text
    
    # 🚫 차단 유저 체크
    if uid in ban_list: return 

    # 1. 가입 로직
    if text == ".가입":
        if uid in user_data: return update.message.reply_text("이미 등록된 트레이너입니다.")
        user_data[uid] = {
            "name": update.effective_user.first_name, "gold": 100000, 
            "pokes": [], "pc": [], "inv": {"슈퍼볼": 0, "하이퍼볼": 0, "마스터볼": 0},
            "catch_count": 0, "level": 1, "exp": 0, "partner": None
        }
        return update.message.reply_text("🎊 가입 완료! `.메뉴`를 입력하세요.")

    user = get_user(uid)
    if not user: return

    # 2. 통합 메뉴 호출
    if text == ".메뉴":
        msg = ("🎮 **[ 포켓몬 월드 메인 메뉴 ]**\n\n원하시는 기능을 터치해 주세요!\n"
               "(버튼 조작을 통해 빠르고 편리하게 즐길 수 있습니다.)")
        update.message.reply_text(msg, reply_markup=get_main_menu_markup(), parse_mode='Markdown')

    # 3. [관리자 전용 권능] ㅡㅡ+
    elif uid == ADMIN_ID:
        parts = text.split()
        if not parts[0].startswith('.'): return
        cmd = parts[0][1:]
        args = parts[1:]

        # .제작 [이름] [레벨]
        if cmd == "제작":
            try:
                name, lv = args[0], int(args[1])
                t = POKEMON_DB.get(name, {"tier":"일반", "atk":50})
                user['pokes'].append({"name": name, "tier": t['tier'], "atk": t['atk'], "lv": lv})
                update.message.reply_text(f"🛠️ [ADMIN] {name}(Lv.{lv}) 제작 완료!")
            except: pass

        # .관리자지급 [유저ID] [금액]
        elif cmd == "관리자지급":
            try:
                target_id, amt = int(args[0]), int(args[1])
                if target_id in user_data:
                    user_data[target_id]['gold'] += amt
                    update.message.reply_text(f"💰 유저 {target_id}에게 {amt:,}G 지급 완료!")
                    context.bot.send_message(chat_id=target_id, text=f"🎁 관리자 보상 {amt:,}G가 도착했습니다!")
                else: update.message.reply_text("❌ 유저를 찾을 수 없습니다.")
            except: pass

        # .전체지급 [금액]
        elif cmd == "전체지급":
            try:
                amt = int(args[0])
                for u in user_data.values(): u['gold'] += amt
                update.message.reply_text(f"📢 전체 유저에게 {amt:,}G 지급 완료!")
            except: pass

        # .차단 [ID] [기록삭제여부]
        elif cmd == "차단":
            try:
                target_id, del_rec = int(args[0]), int(args[1])
                ban_list.add(target_id)
                msg = f"🚫 유저 {target_id} 차단 완료."
                if del_rec == 1 and target_id in user_data:
                    del user_data[target_id]
                    msg += " 🔥 모든 기록이 삭제되었습니다."
                update.message.reply_text(msg)
            except: pass

        # .해제 [ID]
        elif cmd == "해제":
            try:
                target_id = int(args[0])
                if target_id in ban_list:
                    ban_list.remove(target_id)
                    update.message.reply_text(f"✅ 유저 {target_id} 차단 해제.")
            except: pass

# --- [4. 콜백 핸들러 (버튼 로직 전체)] ---

def callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    uid = query.from_user.id
    user = get_user(uid)
    data = query.data
    if not user or uid in ban_list: return

    # 메인 메뉴 -> 각 기능 연결
    if data == "menu_info":
        p_name = user['partner']['name'] if user['partner'] else "없음"
        res = (f"💳 **트레이너 정보**\nID: `{uid}`\nLv.{user['level']} (EXP: {user['exp']}/100)\n"
               f"💰 자산: {user['gold']:,} G\n🐾 파트너: {p_name}")
        query.answer(res, show_alert=True)

    elif data == "menu_pc":
        refresh_pc_screen(query, user)

    elif data == "menu_bag":
        if not user['pokes']: return query.answer("가방이 비어있습니다.")
        msg = "🎒 **내 가방 목록**\n"
        for i, p in enumerate(user['pokes']):
            pc_mark = "[PC]" if p in user['pc'] else ""
            msg += f"{i+1}. {pc_mark} {p['name']} (Lv.{p['lv']}) [{p['tier']}]\n"
        query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ 뒤로", callback_data="menu_back")]]), parse_mode='Markdown')

    elif data == "menu_shop":
        msg = "🏪 **[ 볼 상점 ]**\n최대 100개까지 구매 가능!\n\n• 슈퍼볼: 50,000 G\n• 하이퍼볼: 200,000 G\n• 마스터볼: 5,000,000 G\n\n주문: `.구매 [이름] [수량]`"
        query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ 뒤로", callback_data="menu_back")]]), parse_mode='Markdown')

    elif data == "menu_back":
        query.edit_message_text("🎮 **[ 포켓몬 월드 메인 메뉴 ]**\n\n원하시는 기능을 터치하세요!", reply_markup=get_main_menu_markup(), parse_mode='Markdown')

    # PC 관리 버튼 로직
    elif data == "pc_reg_list":
        if len(user['pc']) >= 6: return query.answer("슬롯 풀!", show_alert=True)
        btns = [[InlineKeyboardButton(f"{p['name']} 등록", callback_data=f"pcreg_{i}")] for i, p in enumerate(user['pokes']) if p not in user['pc']]
        query.edit_message_text("📥 등록할 포켓몬 선택:", reply_markup=InlineKeyboardMarkup(btns + [[InlineKeyboardButton("⬅️ 취소", callback_data="menu_pc")]]))

    elif data == "pc_del_list":
        btns = [[InlineKeyboardButton(f"{p['name']} 해제", callback_data=f"pcdel_{i}")] for i, p in enumerate(user['pc'])]
        query.edit_message_text("📤 해제할 포켓몬 선택:", reply_markup=InlineKeyboardMarkup(btns + [[InlineKeyboardButton("⬅️ 취소", callback_data="menu_pc")]]))

    elif data.startswith("pcreg_"):
        idx = int(data.split("_")[1])
        user['pc'].append(user['pokes'][idx])
        refresh_pc_screen(query, user)

    elif data.startswith("pcdel_"):
        idx = int(data.split("_")[1])
        removed = user['pc'].pop(idx)
        if user['partner'] == removed: user['partner'] = None
        refresh_pc_screen(query, user)

    # 탐험 & 포획 로직 (간략화)
    elif data == "menu_explore":
        p_name = random.choice(list(POKEMON_DB.keys()))
        p_data = POKEMON_DB[p_name]
        user['encounter'] = {"name": p_name, "tier": p_data['tier'], "atk": p_data['atk']}
        msg = f"🐾 **[{p_data['tier']}] {p_name}** 발견!\n어떤 볼을 던질까?"
        btns = [[InlineKeyboardButton("⚾ 몬스터볼 (무제한)", callback_data="catch_몬스터볼")],
                [InlineKeyboardButton(f"🔵 슈퍼볼 ({user['inv']['슈퍼볼']})", callback_data="catch_슈퍼볼")],
                [InlineKeyboardButton(f"🟣 마스터볼 ({user['inv']['마스터볼']})", callback_data="catch_마스터볼")]]
        query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(btns))

    elif data.startswith("catch_"):
        ball = data.split("_")[1]
        p = user.get('encounter')
        if not p: return query.answer("사라짐.")
        if ball != "몬스터볼" and user['inv'][ball] <= 0: return query.answer("볼 부족!", show_alert=True)
        if ball != "몬스터볼": user['inv'][ball] -= 1
        
        chance = 5 if p['tier'] == "신화" else BALL_CONFIG[ball]['rate']
        if random.randint(1, 100) <= chance:
            user['catch_count'] += 1; user['exp'] += 20
            if user['exp'] >= 100: user['level'] += 1; user['exp'] = 0
            p['lv'] = random.randint(1, 30); user['pokes'].append(p)
            res = f"🎉 {p['name']} 포획 성공!"
        else: res = f"💨 {p['name']}가 도망갔습니다!"
        del user['encounter']
        query.edit_message_text(res, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("메뉴로", callback_data="menu_back")]]))

def refresh_pc_screen(query, user):
    slots = "".join([f"▫️ {p['tier']} · B · {p['name']} Lv.{p['lv']}\n" for p in user['pc']])
    msg = (f"**[ 💻 PC · 포켓몬 관리 ]**\n━━━━━━━━━━━━━━━━━━\n\n**슬롯 {len(user['pc'])}/6**\n"
           f"{slots if slots else '비어 있음'}\n━━━━━━━━━━━━━━━━━━\n\n가방 대기 {len(user['pokes'])}마리\n"
           f"*PC에 올린 포켓몬만 파트너 지정 가능합니다.*")
    query.edit_message_text(msg, reply_markup=get_pc_markup(), parse_mode='Markdown')

# --- [5. 실행 부분] ---
def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(callback_handler))
    updater.start_polling(); updater.idle()

if __name__ == "__main__": main()
