import random
import os
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ==========================================
# 1. 환경 설정 (본인 정보로 수정!)
# ==========================================
ADMIN_ID = 7476630349
BOT_TOKEN = "8771125252:AAFyp73DyrwEudPCm4N9wGJhZpBZ_D4gRM4"
OFFICIAL_CHANNEL_URL = "https://t.me/gcoinzbot" 
SUPPORT_URL = "https://t.me/EJ1427"

# Health Check 서버
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running")

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# ==========================================
# 2. 광물 데이터 (가격 10배 및 티어 구분)
# ==========================================
minerals_config = {
    "아다만티움": 5000000, "다이아몬드": 3500000, "오리하르콘": 2500000, # 1티어
    "미스릴": 1600000, "플래티넘": 1300000, "흑요석": 1100000,        # 2티어
    "금": 800000, "은": 600000, "티타늄": 500000,                 # 3티어
    "철": 300000, "구리": 200000, "석탄": 100000,                 # 4티어
    "돌": 30000, "모래": 20000, "자갈": 15000                     # 5티어
}

# 티어별 광물 리스트 매핑
TIER_MAP = {
    "1": ["아다만티움", "다이아몬드", "오리하르콘"],
    "2": ["미스릴", "플래티넘", "흑요석"],
    "3": ["금", "은", "티타늄"],
    "4": ["철", "구리", "석탄"],
    "5": ["돌", "모래", "자갈"]
}

mining_tiers = [
    (1, TIER_MAP["1"], 2),
    (2, TIER_MAP["2"], 8),
    (3, TIER_MAP["3"], 20),
    (4, TIER_MAP["4"], 30),
    (5, TIER_MAP["5"], 40)
]

# ==========================================
# 3. 유저 데이터 관리
# ==========================================
users = {}

def get_user(user_id, name, username=""):
    if user_id not in users:
        users[user_id] = {
            "name": name, "username": f"@{username}" if username else "없음",
            "money": 0, "joined_date": datetime.now().strftime("%Y-%m-%d"),
            "joined": False, "durability": 100,
            "inventory": {m: 0 for m in minerals_config.keys()} # 인벤토리 추가
        }
    return users[user_id]

# ==========================================
# 4. 바카라 52장 덱 (생략 없이 포함)
# ==========================================
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

# ==========================================
# 5. 메인 명령어 처리 로직
# ==========================================
async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    user_id = update.effective_user.id
    user = get_user(user_id, update.effective_user.first_name, update.effective_user.username)

    # .가입
    if text == ".가입":
        if user["joined"]: await update.message.reply_text("❌ 이미 가입되어 있습니다.")
        else:
            user.update({"joined": True, "money": 100000})
            await update.message.reply_text("✅ 가입 완료! 10만 코인 지급")

    # .내정보 (6개 버튼 배치)
    elif text == ".내정보":
        now = datetime.now().strftime("%H:%M:%S")
        info = (f"**[ 사용자 정보 창 ]**\n━━━━━━━━━━━━━━\n👤 **닉네임:** {user['name']}\n🆔 **아이디:** {user['username']}\n💰 **G코인:** {user['money']:,}\n📅 **가입일:** {user['joined_date']}\n━━━━━━━━━━━━━━\n**{now}**")
        keyboard = [
            [InlineKeyboardButton("공식채널 ↗️", url=OFFICIAL_CHANNEL_URL), InlineKeyboardButton("에스코인상담 ↗️", url=SUPPORT_URL)],
            [InlineKeyboardButton("📈 인기도 +1", callback_data="pop_up"), InlineKeyboardButton("📉 인기도 -1", callback_data="pop_down")],
            [InlineKeyboardButton("렛츠벳입장 ↗️", url=LETZBET_URL), InlineKeyboardButton("암행어사 대리결제 ↗️", url=AMHAENG_URL)]
        ]
        await update.message.reply_text(info, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    # .채광
    elif text == ".채광":
        if user["durability"] <= 0:
            await update.message.reply_text("❌ 곡괭이가 부러졌습니다!")
            return
        user["durability"] -= 1
        roll = random.uniform(0, 100)
        total, selected = 0, "자갈"
        for tier, items, chance in mining_tiers:
            total += chance
            if roll <= total: selected = random.choice(items); break
        user["inventory"][selected] += 1
        await update.message.reply_text(f"⛏ **{selected}** 획득! (인벤토리에 보관됨)\n📉 내구도: {user['durability']}")

    # .판매 (티어별 & 전체판매 UI)
    elif text == ".판매":
        # 현재 인벤토리 요약 계산
        summary = "**[ 광물 판매 창 ]**\n"
        for t in ["1", "2", "3", "4", "5"]:
            count = sum(user["inventory"][m] for m in TIER_MAP[t])
            summary += f"💎 {t}티어 광물: {count}개\n"
        
        keyboard = [
            [InlineKeyboardButton("1티어 판매", callback_data="sell_1"), InlineKeyboardButton("2티어 판매", callback_data="sell_2")],
            [InlineKeyboardButton("3티어 판매", callback_data="sell_3"), InlineKeyboardButton("4티어 판매", callback_data="sell_4")],
            [InlineKeyboardButton("5티어 판매", callback_data="sell_5"), InlineKeyboardButton("✨ 전체 판매", callback_data="sell_all")]
        ]
        await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    # 바카라 (.플 .뱅 .타이)
    elif text.startswith((".플", ".뱅", ".타이")):
        try:
            parts = text.split()
            bet_type, amount = parts[0][1:], int(parts[1])
            if user["money"] < amount:
                await update.message.reply_text("❌ 잔액 부족")
                return
            user["money"] -= amount
            deck = BACCARAT_DECK.copy()
            random.shuffle(deck)
            p_hand, b_hand = [deck.pop(), deck.pop()], [deck.pop(), deck.pop()]
            p_s, b_s = sum(c['score'] for c in p_hand)%10, sum(c['score'] for c in b_hand)%10
            win = "player" if p_s > b_s else "banker" if b_s > p_s else "tie"
            await context.bot.send_sticker(update.effective_chat.id, p_hand[0]['file_id'])
            await context.bot.send_sticker(update.effective_chat.id, b_hand[0]['file_id'])
            rate = {"플": 2, "뱅": 1.95, "타이": 8}.get(bet_type)
            if (bet_type == "플" and win == "player") or (bet_type == "뱅" and win == "banker") or (bet_type == "타이" and win == "tie"):
                user["money"] += int(amount * rate)
                await update.message.reply_text(f"✅ 당첨! {win.upper()} 승 ({p_s}:{b_s})\n💰 잔액: {user['money']:,}")
            else:
                await update.message.reply_text(f"❌ 낙첨... {win.upper()} 승 ({p_s}:{b_s})\n💰 잔액: {user['money']:,}")
        except: pass

# ==========================================
# 6. 콜백 처리 (판매 버튼 작동)
# ==========================================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user = get_user(user_id, query.from_user.first_name)
    data = query.data
    total_earned = 0

    if data.startswith("sell_"):
        tier = data.split("_")[1]
        
        # 티어별 판매
        if tier in ["1", "2", "3", "4", "5"]:
            for m in TIER_MAP[tier]:
                total_earned += user["inventory"][m] * minerals_config[m]
                user["inventory"][m] = 0
            msg = f"✅ {tier}티어 광물을 모두 판매하여 {total_earned:,} 코인을 획득했습니다!"
        
        # 전체 판매
        elif tier == "all":
            for m, count in user["inventory"].items():
                total_earned += count * minerals_config[m]
                user["inventory"][m] = 0
            msg = f"✨ 모든 광물을 판매하여 총 {total_earned:,} 코인을 획득했습니다!"

        if total_earned > 0:
            user["money"] += total_earned
            await query.answer(msg, show_alert=True)
            # 판매 창 업데이트
            summary = "**[ 광물 판매 완료 ]**\n"
            for t in ["1", "2", "3", "4", "5"]:
                count = sum(user["inventory"][m] for m in TIER_MAP[t])
                summary += f"💎 {t}티어 광물: {count}개\n"
            summary += f"\n💰 현재 잔액: {user['money']:,} 코인"
            await query.edit_message_text(summary, parse_mode='Markdown')
        else:
            await query.answer("❌ 판매할 광물이 없습니다.", show_alert=True)

# ==========================================
# 7. 실행부
# ==========================================
async def main():
    threading.Thread(target=run_health_check, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_commands))
    app.add_handler(CallbackQueryHandler(handle_callback))
    print("🚀 G-COIN BOT 티어 판매 시스템 가동!")
    await app.initialize()
    await app.updater.start_polling(drop_pending_updates=True)
    await app.start()
    while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    try: asyncio.run(main())
    except KeyboardInterrupt: pass
