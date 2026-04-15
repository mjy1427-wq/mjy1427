import random
import os
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ==========================================
# 1. 환경 설정 (반드시 본인 정보로 수정!)
# ==========================================
ADMIN_ID = 7476630349  # 본인의 숫자 ID 입력 (따옴표 없이 숫자만)
BOT_TOKEN = "8484299407:AAF9Ja2dM0vlHSnsooJsZtsWIw-ayU2dyaY" 
OFFICIAL_CHANNEL_URL = "https://t.me/GCOIN7777" 
SUPPORT_URL = "https://t.me/GCOIN777_BOT"


# ==========================================
# 2. 광물 데이터 및 경제 설정
# ==========================================
minerals_config = {
    "아다만티움": 5000000, "다이아몬드": 3500000, "오리하르콘": 2500000,
    "미스릴": 1600000, "플래티넘": 1300000, "흑요석": 1100000,
    "금": 800000, "은": 600000, "티타늄": 500000,
    "철": 300000, "구리": 200000, "석탄": 100000,
    "돌": 30000, "모래": 20000, "자갈": 15000
}

TIER_MAP = {
    "1": ["아다만티움", "다이아몬드", "오리하르콘"],
    "2": ["미스릴", "플래티넘", "흑요석"],
    "3": ["금", "은", "티타늄"],
    "4": ["철", "구리", "석탄"],
    "5": ["돌", "모래", "자갈"]
}

mining_tiers = [(1, TIER_MAP["1"], 2), (2, TIER_MAP["2"], 8), (3, TIER_MAP["3"], 20), (4, TIER_MAP["4"], 30), (5, TIER_MAP["5"], 40)]

# ==========================================
# 3. 바카라 52장 카드 데이터
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
# 4. 유저 데이터 관리 및 헬스체크
# ==========================================
users = {}

def get_user(user_id, name, username=""):
    if user_id not in users:
        users[user_id] = {
            "name": name, "username": f"@{username}" if username else "없음",
            "money": 0, "joined_date": datetime.now().strftime("%Y-%m-%d"),
            "joined": False, "durability": 100, "popularity": 0,
            "inventory": {m: 0 for m in minerals_config.keys()}
        }
    return users[user_id]

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"ONLINE")

def run_health_check():
    server = HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 8080))), HealthCheckHandler)
    server.serve_forever()

# ==========================================
# 5. 메인 로직 (가입 안 됨 현상 수정완료)
# ==========================================
async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    text = update.message.text.strip()
    user_id = update.effective_user.id
    user = get_user(user_id, update.effective_user.first_name, update.effective_user.username)

    # [가입 처리] - 공백 제거 및 우선순위 최상단
    if text == ".가입":
        if user.get("joined") is True:
            await update.message.reply_text("❌ 이미 가입되어 있습니다.")
        else:
            user["joined"] = True
            user["money"] = 100000
            await update.message.reply_text("✅ 가입 완료! 100,000 코인이 지급되었습니다.")
        return

    # [미가입자 차단]
    if not user.get("joined"):
        # 가입하지 않은 유저가 다른 명령어를 칠 경우 안내
        if text.startswith("."):
            await update.message.reply_text("👋 먼저 `.가입`을 입력하여 시작해주세요!")
        return

    # [내정보 / 관리자정보]
    if text == ".내정보":
        now = datetime.now().strftime("%H:%M:%S")
        info = (f"**[ 사용자 정보 ]**\n━━━━━━━━━━━━━━\n👤 **닉네임:** {user['name']}\n🆔 **아이디:** `{user_id}`\n💰 **G코인:** {user['money']:,}\n🔥 **인기도:** {user['popularity']}\n━━━━━━━━━━━━━━")
        keyboard = [[InlineKeyboardButton("공식채널", url=OFFICIAL_CHANNEL_URL), InlineKeyboardButton("상담", url=SUPPORT_URL)],
                    [InlineKeyboardButton("📈 인기도 +1", callback_data="pop_up"), InlineKeyboardButton("📉 인기도 -1", callback_data="pop_down")]]
        await update.message.reply_text(info, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif text == ".관리자정보" and user_id == ADMIN_ID:
        total_money = sum(u["money"] for u in users.values())
        msg = (f"**[ 🔧 제어실 ]**\n━━━━━━━━━━━━━━\n👥 **유저수:** {len(users)}명\n💰 **총유통:** {total_money:,}\n🏦 **수익(내잔액):** {user['money']:,}\n━━━━━━━━━━━━━━")
        await update.message.reply_text(msg, parse_mode='Markdown')

    # [채광 / 판매]
    elif text == ".채광":
        if user["durability"] <= 0: await update.message.reply_text("❌ 곡괭이 파손!"); return
        user["durability"] -= 1
        roll = random.uniform(0, 100); total = 0; sel = "자갈"
        for t, items, ch in mining_tiers:
            total += ch
            if roll <= total: sel = random.choice(items); break
        user["inventory"][sel] += 1
        await update.message.reply_text(f"⛏ **{sel}** 획득! (내구도: {user['durability']})")

    elif text == ".판매":
        summary = "**[ 광물 판매 ]**\n"
        for t in ["1", "2", "3", "4", "5"]:
            summary += f"💎 {t}티어: {sum(user['inventory'][m] for m in TIER_MAP[t])}개\n"
        keyboard = [[InlineKeyboardButton(f"{i}티어 판매", callback_data=f"sell_{i}") for i in range(1, 4)],
                    [InlineKeyboardButton("4티어", callback_data="sell_4"), InlineKeyboardButton("5티어", callback_data="sell_5")],
                    [InlineKeyboardButton("전체판매", callback_data="sell_all")]]
        await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    # [송금 / 지급]
    elif text.startswith(".송금"):
        try:
            _, tid, amt = text.split(); tid, amt = int(tid), int(amt)
            if user["money"] >= amt > 0 and tid in users:
                user["money"] -= amt; users[tid]["money"] += amt
                await update.message.reply_text(f"💸 {tid}님께 {amt:,} 송금 완료!")
        except: pass
    elif text.startswith(".지급") and user_id == ADMIN_ID:
        try:
            _, tid, amt = text.split(); tid, amt = int(tid), int(amt)
            if tid in users: users[tid]["money"] += amt; await update.message.reply_text(f"🎁 {tid}님께 {amt:,} 지급!")
        except: pass

    # [바카라]
    elif text.startswith((".플", ".뱅", ".타이")):
        try:
            bt, amt = text.split()[0][1:], int(text.split()[1])
            if user["money"] < amt: return
            user["money"] -= amt
            dk = BACCARAT_DECK.copy(); random.shuffle(dk)
            ph, bh = [dk.pop(), dk.pop()], [dk.pop(), dk.pop()]
            ps, bs = sum(c['score'] for c in ph)%10, sum(c['score'] for c in bh)%10
            wn = "player" if ps > bs else "banker" if bs > ps else "tie"
            await context.bot.send_sticker(update.effective_chat.id, ph[0]['file_id'])
            await context.bot.send_sticker(update.effective_chat.id, bh[0]['file_id'])
            rt = {"플": 2, "뱅": 1.95, "타이": 8}.get(bt)
            if (bt == "플" and wn == "player") or (bt == "뱅" and wn == "banker") or (bt == "타이" and wn == "tie"):
                user["money"] += int(amt * rt); await update.message.reply_text(f"✅ 당첨! {wn.upper()} ({ps}:{bs})")
            else:
                if ADMIN_ID in users: users[ADMIN_ID]["money"] += amt
                await update.message.reply_text(f"❌ 낙첨 ({ps}:{bs})")
        except: pass

# ==========================================
# 6. 콜백 핸들러 및 실행부
# ==========================================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; user = get_user(query.from_user.id, query.from_user.first_name)
    if query.data.startswith("pop"):
        user["popularity"] += 1 if "up" in query.data else -1
        await query.answer(f"인기도 반영 ({user['popularity']})")
    elif query.data.startswith("sell"):
        t = query.data.split("_")[1]; earned = 0
        m_list = list(minerals_config.keys()) if t == "all" else TIER_MAP[t]
        for m in m_list: earned += user["inventory"][m] * minerals_config[m]; user["inventory"][m] = 0
        if earned > 0: user["money"] += earned; await query.answer(f"💰 {earned:,} 코인 획득!", show_alert=True)
        else: await query.answer("판매할 광물이 없습니다.")

async def main():
    threading.Thread(target=run_health_check, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_commands))
    app.add_handler(CallbackQueryHandler(handle_callback))
    await app.initialize(); await app.updater.start_polling(drop_pending_updates=True); await app.start()
    print("🚀 G-COIN BOT READY!"); await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
