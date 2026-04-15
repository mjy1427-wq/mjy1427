import random
import os
import threading
import asyncio
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ==========================================
# 1. 환경 설정 (사용자 정보 반영)
# ==========================================
ADMIN_ID = 7476630439  
BOT_TOKEN = "8484299407:AAGlmlVT292KYvRiWA_ptn7v49ZayhfK-pc"
SUPPORT_URL = "https://t.me/GCOIN777_BOT"
OFFICIAL_CHANNEL_URL = "https://t.me/GCOIN7777"

# ==========================================
# 2. 바카라 52장 무삭제 풀덱
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
# 3. 광물 데이터 및 시스템 설정
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
game_history = []

# ==========================================
# 4. 유저 관리 및 유틸리티
# ==========================================
users = {}

def get_user(user_id, name, username=""):
    if user_id not in users:
        users[user_id] = {
            "name": name, "username": f"@{username}" if username else "없음",
            "money": 0, "joined_date": datetime.now().strftime("%Y-%m-%d"),
            "joined": False, "durability": 100, "last_mine": 0, "last_checkin": 0,
            "inventory": {m: 0 for m in minerals_config.keys()}
        }
    return users[user_id]

def generate_roadmap():
    if not game_history: return "📊 기록 없음"
    display = game_history[-50:]
    rows = [[] for _ in range(6)]
    for i, res in enumerate(display):
        symbol = "🔵" if res == "P" else "🔴" if res == "B" else "🟢"
        rows[i % 6].append(symbol)
    grid = "\n".join(["".join(r) for r in rows])
    return f"📊 **바카라 최근 50회 그림장**\n━━━━━━━━━━━━━━\n{grid}\n━━━━━━━━━━━━━━"

# Health Check
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Bot Running")
def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthCheckHandler).serve_forever()

# ==========================================
# 5. 메인 명령어 핸들러 (채광 + 바카라 + 버튼)
# ==========================================
async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    user_id = update.effective_user.id
    user = get_user(user_id, update.effective_user.first_name, update.effective_user.username)

    # 기본 명령어
    if text == ".명령어":
        msg = "📜 **유저 명령어**\n.가입 .내정보 .출석 .랭킹 .바카라 .채광 .판매\n.송금 [ID/답장] [금액]\n.플/.뱅/.타이 [금액]"
        await update.message.reply_text(msg)

    elif text == ".내정보":
        msg = f"👤 **{user['name']}님의 정보**\n━━━━━━━━━━━━━━\n💰 잔액: {user['money']:,} G코인\n⛏ 곡괭이 내구도: {user['durability']}%\n📅 가입일: {user['joined_date']}\n━━━━━━━━━━━━━━"
        keyboard = [[InlineKeyboardButton("💬 G코인상담", url=SUPPORT_URL), InlineKeyboardButton("📢 공식채널", url=OFFICIAL_CHANNEL_URL)]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif text == ".가입":
        if user["joined"]: await update.message.reply_text("❌ 이미 가입됨")
        else:
            user.update({"joined": True, "money": 100000})
            await update.message.reply_text("✅ 가입 완료! 10만 G코인 지급")

    elif text == ".출석":
        now = time.time()
        if now - user["last_checkin"] < 86400: await update.message.reply_text("❌ 24시간 후 다시 가능")
        else:
            user["last_checkin"], user["money"] = now, user["money"] + 100000
            await update.message.reply_text("✅ 출석 완료! 10만 G코인 지급")

    # 채광 시스템 (40초 딜레이)
    elif text == ".채광":
        now = time.time()
        if now - user["last_mine"] < 40:
            await update.message.reply_text(f"⏳ 대기: {int(40-(now-user['last_mine']))}초")
            return
        user["last_mine"], user["durability"] = now, user["durability"] - 1
        roll = random.uniform(0, 100)
        total, res = 0, "자갈"
        for tier, items, chance in mining_tiers:
            total += chance
            if roll <= total: res = random.choice(items); break
        user["inventory"][res] += 1
        await update.message.reply_text(f"⛏ **{res}** 획득! (40초 후 다시 가능)\n📉 내구도: {user['durability']}")

    elif text == ".판매":
        summary = "**[ 광물 판매 창 ]**\n"
        keyboard = [[InlineKeyboardButton("1티어", callback_data="sell_1"), InlineKeyboardButton("2티어", callback_data="sell_2")],
                    [InlineKeyboardButton("3티어", callback_data="sell_3"), InlineKeyboardButton("4티어", callback_data="sell_4")],
                    [InlineKeyboardButton("5티어", callback_data="sell_5"), InlineKeyboardButton("✨ 전체", callback_data="sell_all")]]
        await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    # 바카라 시스템 (2초 간격)
    elif text.startswith((".플", ".뱅", ".타이")):
        try:
            parts = text.split()
            bet_type, amount = parts[0][1:], int(parts[1])
            if user["money"] < amount: await update.message.reply_text("❌ 잔액 부족"); return
            user["money"] -= amount
            chat_id = update.effective_chat.id
            await update.message.reply_text(f"✅ **베팅 완료!** ({amount:,}코인)\n30초 후 마감됩니다.")
            await asyncio.sleep(30); await context.bot.send_message(chat_id, "🚫 **베팅 마감!**")
            await asyncio.sleep(5); await context.bot.send_message(chat_id, f"📢 **제 {len(game_history)+1}회차 결과 발표!!**")
            
            deck = BACCARAT_DECK.copy(); random.shuffle(deck)
            p_hand, b_hand = [deck.pop(), deck.pop()], [deck.pop(), deck.pop()]
            
            await asyncio.sleep(2); await context.bot.send_message(chat_id, "🎴 **플레이어 카드**")
            for c in p_hand: await context.bot.send_sticker(chat_id, c['file_id'])
            await asyncio.sleep(2); await context.bot.send_message(chat_id, "🎴 **뱅커 카드**")
            for c in b_hand: await context.bot.send_sticker(chat_id, c['file_id'])
            
            p_s, b_s = sum(c['score'] for c in p_hand)%10, sum(c['score'] for c in b_hand)%10
            # 추가 카드 로직
            if p_s <= 5:
                await asyncio.sleep(2); c = deck.pop(); p_hand.append(c); p_s = sum(x['score'] for x in p_hand)%10
                await context.bot.send_message(chat_id, "➕ 플레이어 추가 카드"); await context.bot.send_sticker(chat_id, c['file_id'])
            if b_s <= 5:
                await asyncio.sleep(2); c = deck.pop(); b_hand.append(c); b_s = sum(x['score'] for x in b_hand)%10
                await context.bot.send_message(chat_id, "➕ 뱅커 추가 카드"); await context.bot.send_sticker(chat_id, c['file_id'])
            
            win = "P" if p_s > b_s else "B" if b_s > p_s else "T"
            game_history.append(win)
            rate = {"플": 2, "뱅": 1.95, "타이": 8}.get(bet_type)
            if win == bet_type[0].upper() or (win == "T" and bet_type == "타이"):
                win_amt = int(amount * rate); user["money"] += win_amt
                await context.bot.send_message(chat_id, f"✅ **당첨!** +{win_amt:,} 코인\n💰 잔액: {user['money']:,}")
            else: await context.bot.send_message(chat_id, f"❌ **낙첨...**\n💰 잔액: {user['money']:,}")
        except: pass

    elif text == ".바카라":
        await update.message.reply_text(generate_roadmap(), parse_mode='Markdown')

    # 송금 및 지급
    elif text.startswith((".송금", ".지급")):
        is_admin = text.startswith(".지급")
        if is_admin and user_id != ADMIN_ID: return
        try:
            parts = text.split()
            target_id = update.message.reply_to_message.from_user.id if update.message.reply_to_message else int(parts[1])
            amt = int(parts[-1]); target = users.get(target_id)
            if not target: return
            if not is_admin:
                if user["money"] < amt: return
                user["money"] -= amt
            target["money"] += amt; await update.message.reply_text(f"💰 {amt:,} 코인 {'지급' if is_admin else '송금'} 완료!")
        except: pass

# ==========================================
# 6. 콜백 및 실행
# ==========================================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; user = get_user(query.from_user.id, query.from_user.first_name)
    data = query.data; earned = 0
    if data.startswith("sell_"):
        tier = data.split("_")[1]
        target_minerals = TIER_MAP[tier] if tier in TIER_MAP else minerals_config.keys()
        for m in target_minerals: earned += user["inventory"][m] * minerals_config[m]; user["inventory"][m] = 0
        if earned > 0: user["money"] += earned; await query.answer(f"✅ {earned:,} 코인 획득!", show_alert=True)
        else: await query.answer("❌ 광물 없음", show_alert=True)

async def main():
    threading.Thread(target=run_health_check, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_commands))
    app.add_handler(CallbackQueryHandler(handle_callback))
    await app.initialize(); await app.updater.start_polling(drop_pending_updates=True); await app.start()
    while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
