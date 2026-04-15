import random
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ==========================================
# 1. 환경 설정 (본인 정보로 수정 필수)
# ==========================================
ADMIN_ID = 123456789  # 여기에 본인의 숫자 ID를 넣으세요 (예: 61234567)
BOT_TOKEN = "여기에_토큰_입력" # BotFather에게 받은 토큰

# ==========================================
# 2. 데이터베이스 설정 (곡괭이, 광물, 바카라 덱)
# ==========================================
PICKAXE_SHOP_DATA = {
    "Wood": {"name": "나무 곡괭이", "price": 1000000, "durability": 100},
    "Stone": {"name": "돌 곡괭이", "price": 5000000, "durability": 300},
    "Iron": {"name": "철 곡괭이", "price": 15000000, "durability": 500},
    "Gold": {"name": "금 곡괭이", "price": 50000000, "durability": 1000},
    "Diamond": {"name": "다이아 곡괭이", "price": 250000000, "durability": 5000},
    "Netherite": {"name": "네더라이트 곡괭이", "price": 1000000000, "durability": 10000}
}

minerals = {
    "아다만티움": 500000, "다이아몬드": 350000, "오리하르콘": 250000,
    "미스릴": 160000, "플래티넘": 130000, "흑요석": 110000,
    "금": 80000, "은": 60000, "티타늄": 50000,
    "철": 30000, "구리": 20000, "석탄": 10000,
    "돌": 3000, "모래": 2000, "자갈": 1500
}

tiers = [
    (1, ["아다만티움","다이아몬드","오리하르콘"], 2),
    (2, ["미스릴","플래티넘","흑요석"], 8),
    (3, ["금","은","티타늄"], 20),
    (4, ["철","구리","석탄"], 30),
    (5, ["돌","모래","자갈"], 40)
]

# 사용자님이 제공하신 바카라 덱 (코드 보존)
BACCARAT_DECK = [
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
    {'name': 'SP_A', 'score': 1, 'file_id': 'CAACAgUAAxkBAAEQ7Fhp3mW8BGcPAUjH-Xu4bsjSDHIUSgACwh4AASAz8VYhnQL59WSxmzse'},
    {'name': 'HT_A', 'score': 1, 'file_id': 'CAACAgUAAxkBAAEQ7Fdp3mW7GOA0zTWFiMJqzdhQvuOzdgAC7RwAArhl8Faz3VKPQgKXMzse'},
    {'name': 'DI_A', 'score': 1, 'file_id': 'CAACAgUAAxkBAAEQ7FFp3mWXiDQVv4f7uMQbflbdJfLutgACzCAAAla48Vb9T8wXbzPPfjse'},
    {'name': 'CL_A', 'score': 1, 'file_id': 'CAACAgUAAxkBAAEQ7FBp3mWXjbV3Q5OEMdinCJfQltMsqQACHhsAAuaM8VYvC46og1B2ajse'},
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

users = {}
admin_vault = 0 # 시스템 금고

def get_user(user_id, name):
    if user_id not in users:
        users[user_id] = {
            "name": name, "money": 0, "inv": {}, "mine_count": 0,
            "last_checkin": "", "joined": False, "pickaxe": "Wood", "durability": 100
        }
    return users[user_id]

def calculate_score(hand):
    return sum(card['score'] for card in hand) % 10

# ==========================================
# 3. 핵심 핸들러: 마침표(.) 기반 한글 명령어 처리
# ==========================================

async def handle_korean_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global admin_vault
    if not update.message or not update.message.text: return
    
    text = update.message.text.strip()
    if not text.startswith("."): return 

    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    user = get_user(user_id, user_name)
    
    cmd_parts = text[1:].split()
    if not cmd_parts: return
    cmd = cmd_parts[0]
    args = cmd_parts[1:]

    # --- [ 유저 일반 명령어 ] ---
    if cmd == "명령어" or cmd == "도움말":
        msg = (
            "┏━━━━ G COIN BOT ━━━━┓\n"
            "┃ .가입 : 시작금 10만 지급\n"
            "┃ .출석 : 매일 30만 지급\n"
            "┃ .채광 : 광물 캐기 (내구도 소모)\n"
            "┃ .상점 : 곡괭이 구매 및 수리\n"
            "┃ .랭킹 : 부자 순위 확인\n"
            "┃ .송금 [금액] : 유저에게 돈 보내기(수수료 6%)\n"
            "┃ .플/뱅/타이 [금액] : 바카라 베팅\n"
            "┃ .내정보 : 내 상태 확인\n"
            "┗━━━━━━━━━━━━━━━━━━┛"
        )
        await update.message.reply_text(msg)

    elif cmd == "가입":
        if user["joined"]:
            await update.message.reply_text("❌ 이미 가입된 계정입니다.")
        else:
            user["joined"] = True
            user["money"] += 100000
            await update.message.reply_text(f"✅ 가입 완료! 💰 잔액: {user['money']:,}")

    elif cmd == "출석":
        today = datetime.now().strftime("%Y-%m-%d")
        if user["last_checkin"] == today:
            await update.message.reply_text("❌ 오늘은 이미 출석하셨습니다.")
        else:
            user["money"] += 300000
            user["last_checkin"] = today
            await update.message.reply_text(f"✅ 출석 완료! 30만 코인 지급\n💰 잔액: {user['money']:,}")

    elif cmd == "채광":
        if user["durability"] <= 0:
            await update.message.reply_text("❌ 곡괭이가 파손되었습니다! .상점에서 새로 구매하세요.")
            return
        
        user["durability"] -= 1
        user["mine_count"] += 1
        
        roll = random.uniform(0, 100)
        total, selected = 0, "자갈"
        for t, items, chance in tiers:
            total += chance
            if roll <= total:
                selected = random.choice(items)
                break
        
        user["inv"][selected] = user["inv"].get(selected, 0) + 1
        await update.message.reply_text(
            f"┏━━━━ G COIN BOT ━━━━┓\n┃ ⛏ 채광 완료!\n┃ 💎 획득: {selected}\n┃ 🔧 내구도: {user['durability']}\n┗━━━━━━━━━━━━━━━━━━┛"
        )

    elif cmd == "상점":
        shop_text = "⛏ **곡괭이 상점**\n━━━━━━━━━━━━━━\n"
        keyboard = []
        for p_id, data in PICKAXE_SHOP_DATA.items():
            shop_text += f"**{data['name']}** - {data['price']:,} 코인\n"
            keyboard.append([InlineKeyboardButton(f"💰 {data['name']} 구매", callback_data=f"buy_{p_id}")])
        await update.message.reply_text(shop_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif cmd == "송금":
        if not update.message.reply_to_message or not args:
            await update.message.reply_text("❌ 송금 대상을 지정(답장)하고 금액을 적어주세요.")
            return
        try:
            amount = int(args[0])
            if amount <= 0: raise ValueError
        except:
            await update.message.reply_text("❌ 올바른 송금 금액을 입력하세요.")
            return

        fee = int(amount * 0.06)
        actual_send = amount - fee
        target_id = update.message.reply_to_message.from_user.id
        if user["money"] < amount:
            await update.message.reply_text("❌ 잔액이 부족합니다.")
        elif user_id == target_id:
            await update.message.reply_text("❌ 본인에게 송금할 수 없습니다.")
        else:
            target_user = get_user(target_id, update.message.reply_to_message.from_user.first_name)
            user["money"] -= amount
            target_user["money"] += actual_send
            admin_vault += fee
            await update.message.reply_text(f"💸 송금 완료! (수수료 6% 차감)\n받는이: {target_user['name']}\n실전달: {actual_send:,} 코인")

    elif cmd == "랭킹":
        rank_list = {uid: udata for uid, udata in users.items() if uid != ADMIN_ID}
        if not rank_list:
            await update.message.reply_text("📊 아직 유저가 없습니다.")
            return
        sorted_rank = sorted(rank_list.items(), key=lambda x: x[1]['money'], reverse=True)[:10]
        msg = "🏆 **부자 랭킹 TOP 10**\n━━━━━━━━━━━━━━\n"
        for i, (uid, udata) in enumerate(sorted_rank, 1):
            msg += f"{i}위. {udata['name']} — {udata['money']:,} 코인\n"
        await update.message.reply_text(msg)

    elif cmd == "내정보":
        await update.message.reply_text(
            f"👤 이름: {user['name']}\n"
            f"💰 잔액: {user['money']:,} 코인\n"
            f"🔨 곡괭이: {user['pickaxe']}\n"
            f"🔧 내구도: {user['durability']}"
        )

    elif cmd in ["플", "뱅", "타이"]:
        if not args: return
        try:
            bet_amt = int(args[0])
            await baccarat_logic(update, context, cmd, bet_amt)
        except:
            await update.message.reply_text("❌ 배팅 금액을 숫자로 입력하세요.")

    # --- [ 관리자 전용 명령어 ] ---
    if user_id == ADMIN_ID:
        if cmd == "생성":
            if not update.message.reply_to_message or not args:
                await update.message.reply_text("❌ 생성 대상을 지정(답장)하고 금액을 적어주세요.")
                return
            amount = int(args[0])
            target_id = update.message.reply_to_message.from_user.id
            target_user = get_user(target_id, update.message.reply_to_message.from_user.first_name)
            target_user["money"] += amount
            await update.message.reply_text(f"✨ {target_user['name']}님께 {amount:,} 코인을 생성했습니다.")
        elif cmd == "관리자정보":
            await update.message.reply_text(f"👑 **관리자 센터**\n금고수익: {admin_vault:,}\n총 유저수: {len(users)}명")

# ==========================================
# 4. 바카라 게임 핵심 로직 (스티커 포함)
# ==========================================
async def baccarat_logic(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_type_kor, amount):
    global admin_vault
    user = get_user(update.effective_user.id, update.effective_user.first_name)
    chat_id = update.effective_chat.id
    if user["money"] < amount:
        await update.message.reply_text("❌ 코인이 부족합니다.")
        return

    user["money"] -= amount
    deck = BACCARAT_DECK.copy()
    random.shuffle(deck)
    
    p_hand = [deck.pop(), deck.pop()]
    b_hand = [deck.pop(), deck.pop()]
    
    # 카드 스티커 전송
    await context.bot.send_message(chat_id, "👤 플레이어 카드:")
    for c in p_hand: await context.bot.send_sticker(chat_id, c['file_id'])
    await context.bot.send_message(chat_id, "🏦 뱅커 카드:")
    for c in b_hand: await context.bot.send_sticker(chat_id, c['file_id'])

    p_score, b_score = calculate_score(p_hand), calculate_score(b_hand)
    
    # 3구 규칙 생략 (단순 결과 처리)
    winner = "player" if p_score > b_score else "banker" if b_score > p_score else "tie"
    
    bet_map = {"플": "player", "뱅": "banker", "타이": "tie"}
    if bet_map[bet_type_kor] == winner:
        rate = 2 if winner == "player" else 1.95 if winner == "banker" else 8
        win_money = int(amount * rate)
        user["money"] += win_money
        res_text = f"✅ 당첨! {win_money:,} 코인 획득"
    else:
        admin_vault += amount
        res_text = "❌ 낙첨되었습니다."

    await update.message.reply_text(
        f"┏━━━━ BACCARAT ━━━━┓\n"
        f"┃ 결과: {winner.upper()} ({p_score}:{b_score})\n"
        f"┃ {res_text}\n"
        f"┃ 💰 잔액: {user['money']:,}\n"
        f"┗━━━━━━━━━━━━━━━━━━┛"
    )

# ==========================================
# 5. 상점 구매 핸들러
# ==========================================
async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = get_user(query.from_user.id, query.from_user.first_name)
    pick_id = query.data.replace("buy_", "")
    
    if pick_id in PICKAXE_SHOP_DATA:
        price = PICKAXE_SHOP_DATA[pick_id]["price"]
        if user["money"] >= price:
            user["money"] -= price
            user["pickaxe"] = PICKAXE_SHOP_DATA[pick_id]["name"]
            user["durability"] = PICKAXE_SHOP_DATA[pick_id]["durability"]
            await query.edit_message_text(f"✅ {PICKAXE_SHOP_DATA[pick_id]['name']} 장착 완료!")
        else:
            await query.answer("❌ 코인이 부족합니다.", show_alert=True)

# ==========================================
# 6. 실행부
# ==========================================
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # 텍스트 핸들러 등록 (마침표 명령어 감지)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_korean_commands))
    
    # 버튼 클릭 핸들러 등록
    app.add_handler(CallbackQueryHandler(shop_callback))
    
    print("G COIN BOT + 바카라 통합 시스템 가동 시작...")
    app.run_polling()
