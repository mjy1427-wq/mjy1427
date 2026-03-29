import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

# --- [1. 관리자 설정 및 데이터] ---
TOKEN = "8603959168:AAH9Jq_5erWZgvocsvnjS1rP4G_F9VW-CbQ"
user_data = {}
user_status = {} # 상점 수량 입력 대기 상태

TIER_CONFIG = {
    "신화": {"mult": 10.0, "flee": 99.0, "bounty": 100000000},
    "전설": {"mult": 5.0, "flee": 60.0, "bounty": 5000000},
    "유니크": {"mult": 3.0, "flee": 30.0, "bounty": 3000000},
    "희귀": {"mult": 1.5, "flee": 15.0, "bounty": 500000},
    "일반": {"mult": 1.0, "flee": 5.0, "bounty": 100000}
}

# --- [2. 핵심 유틸리티] ---
def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {
            "gold": 50000, "inv": {"슈퍼볼": 0, "하이퍼볼": 0, "마스터볼": 0},
            "pokes": [], "partner": None, "gear": {"tier": "F", "star": 0}
        }
    return user_data[uid]

# --- [3. 주요 명령어 핸들러] ---

def explore(update: Update, context: CallbackContext):
    user = get_user(update.effective_user.id)
    gain = random.randint(100, 5000000) # 최대 500만G 랜덤 획득
    user['gold'] += gain
    
    tier = random.choices(list(TIER_CONFIG.keys()), weights=[1, 4, 15, 20, 30])[0]
    poke = {"name": f"{tier} 포켓몬", "tier": tier, "lv": random.randint(1, 100)}
    user['encounter'] = poke
    
    msg = f"🌲 탐험 성공! **+{gain:,} G** 획득!\n\n🐾 **[{tier}] {poke['name']}** 출현!\n도망가기 전에 볼을 던지세요! (신화 도망 99%)"
    keyboard = [
        [InlineKeyboardButton("⚾ 몬스터볼 (무제한)", callback_data="c_normal")],
        [InlineKeyboardButton(f"🔵 슈퍼볼 ({user['inv']['슈퍼볼']})", callback_data="c_super")],
        [InlineKeyboardButton(f"🟡 하이퍼볼 ({user['inv']['하이퍼볼']})", callback_data="c_hyper")],
        [InlineKeyboardButton(f"💜 마스터볼 ({user['inv']['마스터볼']})", callback_data="c_master")]
    ]
    update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

def shop(update: Update, context: CallbackContext):
    user = get_user(update.effective_user.id)
    msg = f"💰 **현재 자산: {user['gold']:,} G**\n구매할 아이템을 선택하세요. ㅡㅡ+"
    keyboard = [
        [InlineKeyboardButton("🔵 슈퍼볼 (5,000G)", callback_data="buy_슈퍼볼")],
        [InlineKeyboardButton("🟡 하이퍼볼 (50,000G)", callback_data="buy_하이퍼볼")],
        [InlineKeyboardButton("💜 마스터볼 (800,000G)", callback_data="buy_마스터볼")]
    ]
    update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

def gamble(update: Update, context: CallbackContext):
    user = get_user(update.effective_user.id)
    try:
        bet = int(context.args[0])
        if bet > user['gold'] or bet <= 0: return update.message.reply_text("❌ 금액 오류!")
        
        user['gold'] -= bet
        roll = random.uniform(0, 100)
        
        # [관리자 EJ1427 커스텀: 꽝 55% / 본전 5%] 지옥의 밸런스
        if roll <= 0.5: mult, res = 100, "🎊 [JACKPOT] 100배!!"
        elif roll <= 1.5: mult, res = 30, "💎 [초대박] 30배!!"
        elif roll <= 5.0: mult, res = 5, "🌟 [대박] 5배!"
        elif roll <= 15.0: mult, res = 2, "🍀 [중박] 2배!"
        elif roll <= 40.0: mult, res = 1.2, "✨ [소박] 1.2배!"
        elif roll <= 45.0: mult, res = 1, "⚖️ [본전] 1배 생존!"
        else: mult, res = 0, "💀 [꽝] 55% 확률의 전액 몰수... ㅡㅡ+"
        
        win = int(bet * mult)
        user['gold'] += win
        update.message.reply_text(f"{res}\n결과: **{win:,} G** 획득! (잔액: {user['gold']:,}G)", parse_mode='Markdown')
    except: update.message.reply_text("사용법: `.도박 [금액]`")

def partner_status(update: Update, context: CallbackContext):
    user = get_user(update.effective_user.id)
    p = user['partner']
    if not p: return update.message.reply_text("❌ 파트너가 없습니다.")
    
    # 공격력 합산 로직 (가상)
    power = (TIER_CONFIG[p['tier']]['mult'] * p['lv'] * 1000) + (user['gear']['star'] * 5000)
    update.message.reply_text(f"🐾 **[{p['tier']}] {p['name']}**\nLv: {p['lv']} / Exp: {p['exp']}\n🛡️ 장비: {user['gear']['tier']} ({user['gear']['star']}성)\n⚔️ 공격력: {int(power):,}")

# --- [4. 상점 수량 입력 및 콜백 처리] ---

def handle_text(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    user = get_user(uid)
    if uid in user_status and user_status[uid]['action'] == 'wait_qty':
        try:
            qty = int(update.message.text)
            status = user_status[uid]
            total = status['price'] * qty
            if qty > 0 and user['gold'] >= total:
                user['gold'] -= total
                user['inv'][status['item']] += qty
                update.message.reply_text(f"✅ {status['item']} {qty}개 구매 완료!\n💰 잔액: {user['gold']:,}G")
                del user_status[uid]
            else: update.message.reply_text("❌ 자금 부족 또는 수량 오류!")
        except: update.message.reply_text("❌ 숫자만 입력해주세요.")

def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    uid = query.from_user.id
    user = get_user(uid)
    data = query.data

    if data.startswith("c_"): # 포획 로직
        p = user.get('encounter')
        if not p: return query.answer("사라졌습니다.")
        if random.uniform(0, 100) <= TIER_CONFIG[p['tier']]['flee']:
            del user['encounter']
            return query.edit_message_text(f"💨 **[도주]** {p['name']}이(가) 99% 확률로 도망갔습니다!")
        
        ball = {"c_normal": "몬스터볼", "c_super": "슈퍼볼", "c_hyper": "하이퍼볼", "c_master": "마스터볼"}[data]
        if ball != "몬스터볼":
            if user['inv'][ball] <= 0: return query.answer("볼 부족!", show_alert=True)
            user['inv'][ball] -= 1
        
        success = (ball == "마스터볼") or (random.randint(1, 100) <= 25)
        if success:
            bounty = TIER_CONFIG[p['tier']]['bounty']
            user['gold'] += bounty
            user['pokes'].append(p)
            res = f"🎉 **[성공]** {p['tier']} 포획! **{bounty:,}G** 획득!"
        else: res = "💢 실패! 도망갔습니다."
        del user['encounter']
        query.edit_message_text(res, parse_mode='Markdown')

    elif data.startswith("buy_"): # 상점 수량 입력 대기
        item = data.split("_")[1]
        price = {"슈퍼볼": 5000, "하이퍼볼": 50000, "마스터볼": 800000}[item]
        user_status[uid] = {"action": "wait_qty", "item": item, "price": price}
        query.edit_message_text(f"🛒 **[{item}]** 개당 {price:,}G\n구매할 **수량**을 숫자로 입력하세요! ㅡㅡ+")

# --- [5. 실행] ---
def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("탐험", explore))
    dp.add_handler(CommandHandler("상점", shop))
    dp.add_handler(CommandHandler("도박", gamble))
    dp.add_handler(CommandHandler("파트너", partner_status))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    dp.add_handler(CallbackQueryHandler(button_callback))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__": main()
