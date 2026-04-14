import random
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ==========================================
# 1. 환경 설정 (반드시 본인 정보로 수정)
# ==========================================
ADMIN_ID =  7476630349 # 여기에 본인의 텔레그램 숫자 ID 입력
BOT_TOKEN = "8771125252:AAFbKHLcDM2KhLR3MIp6ZGOnFQQWlIQUIlc" # BotFather에게 받은 토큰 입력

# ==========================================
# 2. 데이터베이스 (바카라 덱 52장 풀세트)
# ==========================================
BACCARAT_DECK = [
    # --- 0점 카드 (10, J, Q, K) ---
    {'name': 'SP_10', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7Exp3mWoCRUfVj-ZE5CmN3IUjgtvGQAC2SYAAvCQ8VbM3lvO79VzBTsE'},
    {'name': 'HT_10', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7E5p3mVSE9Y_S9vS6_WAAKGhAACOv_4VpJmKq_Wz_FTOzsE'},
    {'name': 'DI_10', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7Elp3mWdvgYOMw9HgRc2Il7kbpGkGwACExsAAtRO8FahNaTDKDCFzTsE'},
    {'name': 'CL_10', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7Ehp3mWd8ioZzOX1iY2u7FRMlZc4fAACMRsAAhGP8FbmO81P4gZ3DdSE'},
    {'name': 'SP_J', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7GJp3mXczpHSUQABLPWVYJGRB79K7GUAAs4ZAAljo_BWHVM8Q7mxKjc7BA'},
    {'name': 'HT_J', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7FBp3mVVZ_S9vS6_WAAKGhAACOv_4VpJmKq_Wz_FTOzsE'},
    {'name': 'DI_J', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7F5p3mXP7eNL3nEmVkYmy9EnTxmKXAACPbSAAuAa8FauMWEkVitpddSE'},
    {'name': 'CL_J', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7F1p3mXOHKrfuHvAoDFBdNEGk1YfPgACbBsAAgiy-Fb54wO73qUBddSE'},
    {'name': 'SP_Q', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7HJp3mX7k8OEWVS8Gjf4e99UVKKQMgACBRcAAr0P8Fa8o_9h2ERTKdSE'},
    {'name': 'HT_Q', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7HFp3mX77o4V07GRhTZ7p3VjbvEFxgACmxkAA mFN8FYOgeAm8_YYfzsE'},
    {'name': 'DI_Q', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7G5p3mX09qlW7oCyp-k3Z8KA1E0K3QACdxsAAtvN8FbMD0922U9hiDSE'},
    {'name': 'CL_Q', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7G1p3mXzjWB4kHKsr0AfljIrFXEDHQA C9BoAAhcI-VaN6tW2wXj8yTsE'},
    {'name': 'SP_K', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7Gpp3mXt8mcHJ_JyKQgTFnHAwdWtMwACCRoAAi-h-FazQTiuzxZmEzse'},
    {'name': 'HT_K', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7Glp3mXsAAEdy6_qhm4sGBCZm1DLc38AAp8cAAJqqfhWcF0OQx5DFL87BA'},
    {'name': 'DI_K', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7GZp3mXKuM-jJaBuOPhPFZSFMiHaSAACax8AAjMH8FYMbgTuO1crrjsE'},
    {'name': 'CL_K', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7GVp3mXje9-bjU0gVAXEVK_LZT_TMAACdxgAAgk48VaWvHPT0d5KfDsE'},

    # --- 1점 카드 (A) ---
    {'name': 'SP_A', 'score': 1, 'file_id': 'CAACAgUAAxkBAAEQ7Fhp3mW8BGcPAUjH-Xu4bsjSDHIUSgACwh4AASAz8VYhnQL59WSxmzse'},
    {'name': 'HT_A', 'score': 1, 'file_id': 'CAACAgUAAxkBAAEQ7Fdp3mW7GOA0zTWFiMJqzdhQvuOzdgAC7RwAArhl8Faz3VKPQgKXMzse'},
    {'name': 'DI_A', 'score': 1, 'file_id': 'CAACAgUAAxkBAAEQ7FFp3mWXiDQVv4f7uMQbflbdJfLutgACzCAAAla48Vb9T8wXbzPPfjse'},
    {'name': 'CL_A', 'score': 1, 'file_id': 'CAACAgUAAxkBAAEQ7FBp3mWXjbV3Q5OEMdinCJfQltMsqQACHhsAAuaM8VYvC46og1B2ajse'},

    # --- 2~9점 카드 ---
    {'name': 'HT_2', 'score': 2, 'file_id': 'CAACAgUAAxkBAAEQ7App3mSRViSy9QABBrH7Hjrq5ouaZZ8AAtcaAALQMflWUcolg756dC47BA'},
    {'name': 'SP_2', 'score': 2, 'file_id': 'CAACAgUAAxkBAAEQ7Axp3mSaEUEgc5majSVq8OIh7ts2pwACQh4AAuxU8FYnql4-ZGGRJTsE'},
    {'name': 'CL_2', 'score': 2, 'file_id': 'CAACAgUAAxkBAAEQ7AZp3mR_TSeuCgnjXc4qbGPN_M1yVgACWx4AAubz8VbWRCfXXRC59jsE'},
    {'name': 'DI_2', 'score': 2, 'file_id': 'CAACAgUAAxkBAAEQ7Ahp3mSHxRGhAYCJQWfKunVrex9XKwACJx0AAhb5-VZ5zrTMtEsdvjsE'},
    {'name': 'CL_3', 'score': 3, 'file_id': 'CAACAgUAAxkBAAEQ7A5p3mSksYYgf8iEeXDDR8fq1KRP4QACaR8AAv5Y8VaTLVf2T489ZzsE'},
    {'name': 'DI_3', 'score': 3, 'file_id': 'CAACAgUAAxkBAAEQ7BBp3mSukxqN7O7HsmM4-5hD9GEPywACPB0AAjb28Fb2JkBj8-_NNjsE'},
    {'name': 'HT_3', 'score': 3, 'file_id': 'CAACAgUAAxkBAAEQ7BJp3mS1yaKFOG_5CrVrxEyyZV3wAACfhwAAsgs8VZuR148a475jsE'},
    {'name': 'SP_3', 'score': 3, 'file_id': 'CAACAgUAAxkBAAEQ7BRp3mS-_UwQIUAYhXc_AcvUY9rfvgACrxoAAuBR8VbK9G7nf3c54TsE'},
    {'name': 'HT_4', 'score': 4, 'file_id': 'CAACAgUAAxkBAAEQ7Bpp3mTSM0lu28ee05WEDvA60gj02QACcB4AAmM48VYrEVYD2RMdTzsE'},
    {'name': 'SP_4', 'score': 4, 'file_id': 'CAACAgUAAxkBAAEQ7Bxp3mTXgly2BFytQ15h9ry_MruqwwACjxwAAsth8FZ1KAQ0WpYDlzsE'},
    {'name': 'CL_4', 'score': 4, 'file_id': 'CAACAgUAAxkBAAEQ7BZp3mTEreDBUC8SDd6zMknOuslsJQAC-x0AAk898VallRAp2VysPDsE'},
    {'name': 'DI_4', 'score': 4, 'file_id': 'CAACAgUAAxkBAAEQ7Bhp3mTLrFneb4g5FGcLDQqiiXfhKwACYx0AAhbh8VaJgN_C89Ws4jsE'},
    {'name': 'CL_5', 'score': 5, 'file_id': 'CAACAgUAAxkBAAEQ7B5p3mTciJpNbwOUcDGtJanwooEMAACHyEAAofK8FbQIR7YFejOuDsE'},
    {'name': 'DI_5', 'score': 5, 'file_id': 'CAACAgUAAxkBAAEQ7CBp3mTk31W6hLC6UcCAv373S4akGwACVxwAAidE-FYFTRXzoYHR0jsE'},
    {'name': 'HT_5', 'score': 5, 'file_id': 'CAACAgUAAxkBAAEQ7CJp3mTrBoeYaj9SfvexBKZAVbkZMgACNBkAAiXt8FYwis7G_aMsczsE'},
    {'name': 'SP_5', 'score': 5, 'file_id': 'CAACAgUAAxkBAAEQ7CRp3mT632ulFb6I-YFRwOxC5biGdgACEh4AAvYr8Vb0JSaolbjdrTsE'},
    {'name': 'CL_6', 'score': 6, 'file_id': 'CAACAgUAAxkBAAEQ7CZp3mUCEmoK8EuD6D544yHOaLu3-wAC9hgAAq89-FaiUQuOgwiwzsE'},
    {'name': 'DI_6', 'score': 6, 'file_id': 'CAACAgUAAxkBAAEQ7Chp3mUNHWqdz7d6zLs1dzO5IJYy3QACfxwAAou88FYld8a9twT_YzsE'},
    {'name': 'HT_6', 'score': 6, 'file_id': 'CAACAgUAAxkBAAEQ7Clp3mUOKoepG6cx3X8DQVIG9V2sLAAC5BsAAg768FbNdm1szl6UUTsE'},
    {'name': 'SP_6', 'score': 6, 'file_id': 'CAACAgUAAxkBAAEQ7Chp3mUOCoepG6cx3X8DQVIG9V2sLAAC5BsAAg768FbNdm1szl6UUTsE'},
    {'name': 'SP_7', 'score': 7, 'file_id': 'CAACAgUAAxkBAAEQ7DFp3mUpnCA-GEJ8oaLYcdSneGJu3QACuhoAAjFN8FbTzoXAcmpBCTsE'},
    {'name': 'HT_7', 'score': 7, 'file_id': 'CAACAgUAAxkBAAEQ7DBp3mUpBnm0QPY0a2CaDUGGzfqmqwACiBsAAtB0-Fb1BMJRuaIUJDSE'},
    {'name': 'CL_7', 'score': 7, 'file_id': 'CAACAgUAAxkBAAEQ7C1p3mUaD__E8YaJEA2puTxbnjHnyQACth0AAjMq8Val7P12Gpjr2DsE'},
    {'name': 'DI_7', 'score': 7, 'file_id': 'CAACAgUAAxkBAAEQ7Hdp3mYSx96E3k_hPNMS_FOdDQAB0b4AAk0dAAITVfFW4T3rXlj6AAFWOWqQ'},
    {'name': 'SP_8', 'score': 8, 'file_id': 'CAACAgUAAxkBAAEQ7Dlp3mVKb8CjYmV0DNZCrujiZx5S5wACqScAAnS48FYYwX-ZCyh0iDsE'},
    {'name': 'HT_8', 'score': 8, 'file_id': 'CAACAgUAAxkBAAEQ7Dhp3mVJ5yNHLy28B9BHT2qfgsv2rQACdB4AAnMM8VZTMSvcZqfutzsE'},
    {'name': 'DI_8', 'score': 8, 'file_id': 'CAACAgUAAxkBAAEQ7DVp3mU13uK_NKkAAUefJseY-eW03RAAAi0bAAKhoPFWLno-ReRJ4H47BA'},
    {'name': 'CL_8', 'score': 8, 'file_id': 'CAACAgUAAxkBAAEQ7DRp3mU1sNsf-ebu7c80oVqgji32mgACpR8AAuNO8VaW49WvovXUZzsE'},
    {'name': 'SP_9', 'score': 9, 'file_id': 'CAACAgUAAxkBAAEQ7EVp3mWUy1KHmKxHMBmbmo738zl1GQACyhkAAmI9-FY-6RY8e3-UETsE'},
    {'name': 'HT_9', 'score': 9, 'file_id': 'CAACAgUAAxkBAAEQ7ERp3mWT3RbXuluWyAVqNgpJ4KSunwACERoAAnvy-VaomxXwVnT5RDsE'},
    {'name': 'DI_9', 'score': 9, 'file_id': 'CAACAgUAAxkBAAEQ7EFp3mWGN5nL3ma1jSENoY1PYOLCgwACVx4AAjW7-Fa30fLUp ygsgzsE'},
    {'name': 'CL_9', 'score': 9, 'file_id': 'CAACAgUAAxkBAAEQ7EBp3mWGYNOoFfvUelUEqB__xWN40wACQxwAAqMu8FZUMsBrOgtazjsE'},
]

# 광물 데이터
minerals = {
    "아다만티움": 500, "다이아몬드": 350, "오리하르콘": 250, "미스릴": 160,
    "플래티넘": 130, "흑요석": 110, "금": 80, "은": 60, "티타늄": 50,
    "철": 30, "구리": 20, "석탄": 10, "돌": 3, "모래": 2, "자갈": 1.5
}

tiers = [
    (1, ["아다만티움","다이아몬드","오리하르콘"], 1),
    (2, ["미스릴","플래티넘","흑요석"], 9),
    (3, ["금","은","티타늄"], 20),
    (4, ["철","구리","석탄"], 30),
    (5, ["돌","모래","자갈"], 40)
]

# ===== 통합 데이터 저장소 =====
users = {}

def get_user(user_id, name):
    if user_id not in users:
        users[user_id] = {
            "name": name,
            "money": 0,
            "inv": {},
            "pity": 0,
            "fail": 0,
            "crit": 0,
            "mine": 0,
            "last_checkin": "",
            "joined": False
        }
    return users[user_id]

# ==========================================
# 3. 게임 로직 (채광 & 바카라 규칙)
# ==========================================

def calculate_score(hand):
    return sum(card['score'] for card in hand) % 10

def mine(user):
    user["mine"] += 1
    if user["pity"] >= 100:
        mineral = random.choice(tiers[0][1])
        user["pity"] = 0
    else:
        roll = random.uniform(0, 100)
        total = 0
        for tier, items, chance in tiers:
            total += chance
            if roll <= total:
                mineral = random.choice(items)
                break
    user["pity"] = 0 if mineral in tiers[0][1] else user["pity"] + 1
    value = minerals[mineral]
    crit_text = ""
    if random.random() < 0.05:
        user["crit"] += 1
        multi = random.choice([2,3,5])
        value *= multi
        crit_text = f"\n⚡ 크리티컬 {multi}배!"
    user["inv"][mineral] = user["inv"].get(mineral, 0) + 1
    return mineral, value, crit_text

# ==========================================
# 4. 명령어 핸들러
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⛏ 채광하기", callback_data="mine")],
        [InlineKeyboardButton("🎒 인벤", callback_data="inv"), InlineKeyboardButton("💰 판매", callback_data="sell")],
        [InlineKeyboardButton("👤 내정보", callback_data="info"), InlineKeyboardButton("🏆 랭킹", callback_data="rank")]
    ]
    await update.message.reply_text("🎮 **통합 게임 시스템**\n/가입 (10만 지급)\n/출석 (30만 지급)\n/플, /뱅, /타이 (금액) 배팅", 
                                  reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id, update.effective_user.first_name)
    if user["joined"]:
        await update.message.reply_text("❌ 이미 가입되어 있습니다.")
    else:
        user["joined"], user["money"] = True, user["money"] + 100000
        await update.message.reply_text("🎊 가입 축하! 10만 원 지급되었습니다.")

async def checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id, update.effective_user.first_name)
    today = datetime.now().strftime("%Y-%m-%d")
    if user["last_checkin"] == today:
        await update.message.reply_text("❌ 오늘은 이미 출석하셨습니다.")
    else:
        user["money"], user["last_checkin"] = user["money"] + 300000, today
        await update.message.reply_text(f"✅ 출석 완료! 30만 원 지급.\n현재 잔액: {user['money']:,}원")

async def transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id, update.effective_user.first_name)
    try:
        to_id, amount = int(context.args[0]), int(context.args[1])
        if amount > 0 and user["money"] >= amount and to_id in users:
            user["money"] -= amount
            users[to_id]["money"] += amount
            await update.message.reply_text(f"💸 {to_id}님에게 {amount:,}원 송금 완료!")
        else: raise ValueError
    except: await update.message.reply_text("❌ 사용법: /송금 (ID) (금액) - 잔액 부족 또는 잘못된 정보")

async def baccarat_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id, update.effective_user.first_name)
    chat_id = update.effective_chat.id
    cmd = update.message.text.split()
    if len(cmd) < 2: return
    try:
        bet_amount = int(cmd[1])
        if bet_amount <= 0 or user["money"] < bet_amount: raise ValueError
    except:
        await update.message.reply_text("❌ 잔액이 부족하거나 올바른 금액이 아닙니다.")
        return

    bet_type = "player" if cmd[0] == "/플" else "banker" if cmd[0] == "/뱅" else "tie"
    user["money"] -= bet_amount
    await update.message.reply_text(f"🃏 {bet_type.upper()}에 {bet_amount:,}원 배팅!")

    deck = BACCARAT_DECK.copy()
    random.shuffle(deck)
    p_hand, b_hand = [deck.pop(), deck.pop()], [deck.pop(), deck.pop()]

    # 카드 공개
    await context.bot.send_message(chat_id, "👤 플레이어 카드:")
    for c in p_hand: await context.bot.send_sticker(chat_id, c['file_id'])
    await context.bot.send_message(chat_id, "🏦 뱅커 카드:")
    for c in b_hand: await context.bot.send_sticker(chat_id, c['file_id'])

    p_score, b_score = calculate_score(p_hand), calculate_score(b_hand)

    # 추가 카드 규칙
    if p_score < 8 and b_score < 8:
        if p_score <= 5:
            p_third = deck.pop()
            p_hand.append(p_third)
            await context.bot.send_message(chat_id, "👤 플레이어 추가!")
            await context.bot.send_sticker(chat_id, p_third['file_id'])
            p_score = calculate_score(p_hand)
        
        # 뱅커 3구 규칙 요약 적용
        if len(p_hand) == 2 and b_score <= 5: draw_b = True
        elif len(p_hand) == 3:
            p3 = p_hand[2]['score']
            draw_b = (b_score <= 2) or (b_score == 3 and p3 != 8) or \
                     (b_score == 4 and p3 in [2,3,4,5,6,7]) or \
                     (b_score == 5 and p3 in [4,5,6,7]) or \
                     (b_score == 6 and p3 in [6,7])
        else: draw_b = False

        if draw_b:
            b_third = deck.pop()
            b_hand.append(b_third)
            await context.bot.send_message(chat_id, "🏦 뱅커 추가!")
            await context.bot.send_sticker(chat_id, b_third['file_id'])
            b_score = calculate_score(b_hand)

    winner = "player" if p_score > b_score else "banker" if b_score > p_score else "tie"
    if bet_type == winner:
        rate = 2 if winner == "player" else 1.95 if winner == "banker" else 8
        win_money = int(bet_amount * rate)
        user["money"] += win_money
        res = f"✅ 당첨! {win_money:,}원 지급!"
    else: res = "❌ 미적중..."

    await update.message.reply_text(f"🏁 결과: {winner.upper()} ({p_score}:{b_score})\n{res}\n💰 현재 잔액: {user['money']:,}원")

# ==========================================
# 5. 관리자 및 버튼 처리
# ==========================================

async def create_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        amount = int(context.args[0])
        user = get_user(update.effective_user.id, update.effective_user.first_name)
        user["money"] += amount
        await update.message.reply_text(f"⚡ 관리자 권한: {amount:,}원 생성 완료!")
    except: await update.message.reply_text("사용법: /생성 (금액)")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(query.from_user.id, query.from_user.first_name)

    if query.data == "mine":
        m, v, c = mine(user)
        await query.edit_message_text(f"⛏ **{m}** 획득!{c}\n(가치: {minerals[m]}만원)", 
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⛏ 다시 채광", callback_data="mine")]]), parse_mode='Markdown')
    elif query.data == "inv":
        txt = "🎒 **인벤토리**\n" + "\n".join([f"• {m} x{c}" for m, c in user["inv"].items()])
        await query.edit_message_text(f"{txt}\n\n💰 총 예상가: {sum(minerals[m]*c for m,c in user['inv'].items()):,}만원", parse_mode='Markdown')
    elif query.data == "sell":
        total = sum(minerals[m]*c for m, c in user["inv"].items())
        user["money"], user["inv"] = user["money"] + total, {}
        await query.edit_message_text(f"💰 판매 완료! {total:,}원 지급됨.\n보유금: {user['money']:,}원")
    elif query.data == "info":
        await query.edit_message_text(f"👤 {user['name']}\n💰 {user['money']:,}원\n⛏ {user['mine']}회\n⚡ 크릿 {user['crit']}회")
    elif query.data == "rank":
        ranking = sorted(users.items(), key=lambda x: x[1]["money"], reverse=True)[:5]
        text = "🏆 **자산 랭킹**\n" + "\n".join([f"{i+1}. {u['name']} - {u['money']:,}원" for i,(uid,u) in enumerate(ranking)])
        await query.edit_message_text(text, parse_mode='Markdown')

# ==========================================
# 6. 실행 (Main)
# ==========================================

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("가입", join))
    app.add_handler(CommandHandler("출석", checkin))
    app.add_handler(CommandHandler("송금", transfer))
    app.add_handler(CommandHandler("생성", create_money))
    app.add_handler(CommandHandler("플", baccarat_bet))
    app.add_handler(CommandHandler("뱅", baccarat_bet))
    app.add_handler(CommandHandler("타이", baccarat_bet))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("봇 가동 중...")
    app.run_polling()
