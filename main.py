import random, logging, time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CallbackQueryHandler, CallbackContext, MessageHandler, Filters

# --- [1. 시스템 설정] ---
TOKEN = "8603959168:AAFfP7bH_LA5214i1OaRSH3uPPzr5daovBc"
ADMIN_ID = 7476630349 
TITLE = "🏆 [포켓몬월드:약육강식 에디션] 🏆"

# 배율 및 설정 데이터
GEAR_BONUS = {"C급": 1.0, "B급": 1.2, "A급": 1.5, "S급": 2.0, "SS급": 3.0}
POKE_NAMES = ["피카츄", "리자몽", "뮤츠", "루기아", "칠색조", "세레비", "레쿠쟈", "그란돈", "가이오가", "디아루가", "펄기아", "아르세우스"]

user_data = {}

# --- [2. 확률 및 보상 엔진] ---
def get_encounter_tier():
    r = random.random() * 100
    if r <= 1.0: return "신화"
    elif r <= 3.0: return "환상"
    elif r <= 8.0: return "전설"
    elif r <= 18.0: return "유니크"
    elif r <= 33.0: return "희귀"
    elif r <= 58.0: return "레어"
    else: return "일반"

def get_catch_rate(tier):
    # 신화 포획 0.5% 고정 ㅡㅡ+
    rates = {"신화": 0.5, "환상": 3.0, "전설": 7.0, "유니크": 15.0, "희귀": 30.0, "레어": 50.0, "일반": 70.0}
    return rates.get(tier, 50.0)

def get_random_reward(tier):
    # 등급별 랜덤 보상 범위 설정 ㅡㅡ+
    if tier == "일반": return random.randint(10000, 50000)
    elif tier == "레어": return random.randint(60000, 100000)
    elif tier == "희귀": return random.randint(110000, 400000)
    elif tier == "유니크": return random.randint(500000, 900000)
    elif tier == "전설": return random.randint(1000000, 3000000)
    elif tier == "환상": return random.randint(5000000, 10000000)
    elif tier == "신화": return random.randint(50000000, 200000000)
    return 10000

# --- [3. 메뉴 UI 구성 (이미지 순서 10개 버튼)] ---
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("🍃 탐험하기", callback_data="m_explore"), InlineKeyboardButton("💻 PC등록", callback_data="m_pc_main")],
        [InlineKeyboardButton("💳 내 정보", callback_data="m_info"), InlineKeyboardButton("🎒 내 가방", callback_data="m_bag")],
        [InlineKeyboardButton("🏪 상점", callback_data="m_shop"), InlineKeyboardButton("💰 판매장", callback_data="m_sell")],
        [InlineKeyboardButton("🎰 슬롯머신", callback_data="m_slot"), InlineKeyboardButton("🏆 랭킹", callback_data="m_rank")],
        [InlineKeyboardButton("🎒 배틀 기어", callback_data="m_gear"), InlineKeyboardButton("⚒️ 스타포스 강화", callback_data="m_star")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- [4. 콜백 쿼리 핸들러] ---
def callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    uid = query.from_user.id
    user = user_data.get(uid)
    data = query.data
    if not user: return query.answer("가입이 필요합니다!")

    # [탐험하기 및 포획]
    if data == "m_explore":
        tier = get_encounter_tier()
        context.user_data['temp_tier'] = tier
        btns = [[InlineKeyboardButton("⚾️ 몬스터볼", callback_data="c_norm"),
                 InlineKeyboardButton(f"🟣 마스터볼({user['items'].get('마스터볼',0)})", callback_data="c_mast")]]
        query.edit_message_text(f"❗ **[{tier} 등급]** 조우!\n(포획 확률: {get_catch_rate(tier)}%)\n결과를 지켜보십시오. ㅡㅡ+", reply_markup=InlineKeyboardMarkup(btns), parse_mode='Markdown')

    elif data.startswith("c_"):
        ball = "마스터볼" if "mast" in data else "몬스터볼"
        tier = context.user_data.get('temp_tier', "일반")
        if ball == "마스터볼" and user['items'].get("마스터볼", 0) <= 0: return query.answer("볼 부족!")
        if ball == "마스터볼": user['items']["마스터볼"] -= 1
        
        query.edit_message_text(f"⚙️ {ball} 투척 중...")
        time.sleep(1.2)
        
        success_rate = get_catch_rate(tier) * (1000.0 if ball == "마스터볼" else 1.0)
        if (random.random() * 100) <= success_rate:
            reward = get_random_reward(tier)
            user['gold'] += reward
            # 장비 드랍 (0.1% SS급 공지)
            g_rand = random.random() * 100
            fg = "SS급" if g_rand <= 0.1 else "S급" if g_rand <= 0.5 else "A급" if g_rand <= 1.5 else "B급" if g_rand <= 5.0 else None
            
            name = random.choice(POKE_NAMES)
            new_poke = {"name": name, "tier": tier, "gear": "C급", "star": 0, "atk": 100}
            user['pokes'].append(new_poke)
            
            msg = f"🎊 **{name}({tier})** 포획 성공!\n💰 보상: **+{reward:,}G** 획득!"
            if fg:
                user['inventory'][fg] = user['inventory'].get(fg, 0) + 1
                msg += f"\n📦 **[{fg}]** 장비를 가방에 넣었습니다!"
                if fg == "SS급":
                    for u in user_data.keys():
                        try: context.bot.send_message(u, f"📣 **[서버 공지]**\n🎊 **{user['name']}**님이 ✨**[SS급 장비]**✨를 획득했습니다!", parse_mode='Markdown')
                        except: pass
            query.edit_message_text(msg, reply_markup=get_main_menu())
        else:
            query.edit_message_text(f"💨 {tier} 등급이 도망갔습니다. ㅡㅡ", reply_markup=get_main_menu())

    # [PC 등록 (추가/제거)]
    elif data == "m_pc_main":
        btns = [[InlineKeyboardButton("➕ 추가", callback_data="pc_add"), InlineKeyboardButton("➖ 제거", callback_data="pc_rem")],
                [InlineKeyboardButton("🔙 메인으로", callback_data="m_back")]]
        query.edit_message_text(f"💻 **PC 관리** (보호 중: {len(user['pc'])}/6)\n등록된 포켓몬은 판매 및 전달이 불가합니다.", reply_markup=InlineKeyboardMarkup(btns))

    elif data == "pc_add":
        if len(user['pc']) >= 6: return query.answer("PC 용량 초과 (최대 6마리)!")
        btns = [[InlineKeyboardButton(p['name'], callback_data=f"pado_{i}")] for i, p in enumerate(user['pokes']) if p not in user['pc']]
        btns.append([InlineKeyboardButton("🔙 뒤로", callback_data="m_pc_main")])
        query.edit_message_text("➕ PC에 등록할 포켓몬을 선택하세요.", reply_markup=InlineKeyboardMarkup(btns))

    elif data.startswith("pado_"):
        idx = int(data.split("_")[1])
        user['pc'].append(user['pokes'][idx])
        query.edit_message_text("✅ PC에 안전하게 등록되었습니다.", reply_markup=get_main_menu())

    # [배틀 기어 (장착)]
    elif data == "m_gear":
        btns = [[InlineKeyboardButton(f"{p['name']} [{p['gear']}]", callback_data=f"gsel_{i}")] for i, p in enumerate(user['pokes'])]
        btns.append([InlineKeyboardButton("🔙 메인으로", callback_data="m_back")])
        query.edit_message_text("🎒 장비를 장착할 포켓몬을 선택하세요.", reply_markup=InlineKeyboardMarkup(btns))

    elif data.startswith("gsel_"):
        p_idx = int(data.split("_")[1])
        btns = [[InlineKeyboardButton(f"{g} (보유:{c})", callback_data=f"gfit_{p_idx}_{g}")] for g, c in user['inventory'].items() if c > 0]
        btns.append([InlineKeyboardButton("🔙 뒤로", callback_data="m_gear")])
        query.edit_message_text("🛠 가방에서 장착할 장비를 선택하세요.", reply_markup=InlineKeyboardMarkup(btns))

    elif data.startswith("gfit_"):
        _, _, p_idx, g_tier = data.split("_")
        p = user['pokes'][int(p_idx)]
        user['inventory'][g_tier] -= 1
        p['gear'] = g_tier
        p['atk'] = int((100 + (p['star'] * 100)) * GEAR_BONUS[g_tier])
        query.answer(f"{g_tier} 장착 완료!")
        query.edit_message_text(f"✅ {p['name']}에게 {g_tier} 장비를 장착했습니다.", reply_markup=get_main_menu())

    # [메인으로]
    elif data == "m_back":
        query.edit_message_text(f"{TITLE}\n메뉴를 선택하세요. ㅡㅡ+", reply_markup=get_main_menu())

# --- [5. 메시지 핸들러] ---
def handle_msg(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    text = update.message.text
    if text == ".가입":
        if uid not in user_data:
            user_data[uid] = {"name": update.effective_user.first_name, "gold": 1000000, 
                              "items": {"마스터볼": 1}, "pokes": [], "pc": [], "inventory": {}}
            update.message.reply_text(f"{TITLE}\n가입을 환영합니다! .메뉴를 입력해보세요.")
        else: update.message.reply_text("이미 가입되어 있습니다!")
    elif text == ".메뉴":
        if uid in user_data: update.message.reply_text(f"{TITLE}\n원하시는 기능을 선택하세요. ㅡㅡ+", reply_markup=get_main_menu())
        else: update.message.reply_text(".가입 을 먼저 해주세요.")

# --- [6. 서버 구동] ---
def main():
    up = Updater(TOKEN)
    dp = up.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_msg))
    dp.add_handler(CallbackQueryHandler(callback_handler))
    up.start_polling(); up.idle()

if __name__ == "__main__": main()
