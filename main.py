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
ADMIN_ID =   7476630349 # 본인의 숫자 ID 입력
BOT_TOKEN = "8484299407:AAF9Ja2dM0vlHSnsooJsZtsWIw-ayU2dyaY" 
OFFICIAL_CHANNEL_URL = "https://t.me/GCOIN7777" 
SUPPORT_URL = "https://t.me/GCOIN777_BOT"

# ==========================================
# 2. 광물 데이터 및 경제 설정
# ==========================================
minerals_config = {
    "아다만티움": 5000000, "다이아몬드": 3500000, "오리하르콘": 2500000, # 1티어
    "미스릴": 1600000, "플래티넘": 1300000, "흑요석": 1100000,        # 2티어
    "금": 800000, "은": 600000, "티타늄": 500000,                 # 3티어
    "철": 300000, "구리": 200000, "석탄": 100000,                 # 4티어
    "돌": 30000, "모래": 20000, "자갈": 15000                     # 5티어
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
# 3. 바카라 52장 카드 풀 데이터
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
# 4. 유저 데이터 및 헬스체크
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
        self.wfile.write(b"G-COIN BOT IS ONLINE")

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# ==========================================
# 5. 메인 명령어 핸들러 (지급/송금/관리자정보 포함)
# ==========================================
async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    user_id = update.effective_user.id
    user = get_user(user_id, update.effective_user.first_name, update.effective_user.username)

    # [1] 가입
    if text == ".가입":
        if user["joined"]: await update.message.reply_text("❌ 이미 가입되어 있습니다.")
        else:
            user.update({"joined": True, "money": 100000})
            await update.message.reply_text("✅ 가입 완료! 10만 코인이 지급되었습니다.")

    # [2] 내정보 (일반 유저용)
    elif text == ".내정보":
        now = datetime.now().strftime("%H:%M:%S")
        info = (f"**[ 사용자 정보 창 ]**\n━━━━━━━━━━━━━━\n👤 **닉네임:** {user['name']}\n🆔 **아이디:** `{user_id}`\n💰 **G코인:** {user['money']:,}\n🔥 **인기도:** {user['popularity']}\n📅 **가입일:** {user['joined_date']}\n━━━━━━━━━━━━━━\n**{now}**")
        keyboard = [
            [InlineKeyboardButton("공식채널 ↗️", url=OFFICIAL_CHANNEL_URL), InlineKeyboardButton("상담 ↗️", url=SUPPORT_URL)],
            [InlineKeyboardButton("📈 인기도 +1", callback_data="pop_up"), InlineKeyboardButton("📉 인기도 -1", callback_data="pop_down")],
            [InlineKeyboardButton("렛츠벳입장 ↗️", url=LETZBET_URL), InlineKeyboardButton("암행어사 대리결제 ↗️", url=AMHAENG_URL)]
        ]
        await update.message.reply_text(info, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    # [3] 관리자정보 (관리자 전용)
    elif text == ".관리자정보" and user_id == ADMIN_ID:
        total_users = len(users)
        total_money = sum(u["money"] for u in users.values())
        admin_revenue = user["money"] # 회수된 수익
        msg = (f"**[ 🔧 G-COIN 제어실 ]**\n━━━━━━━━━━━━━━\n👥 **가입 유저:** {total_users}명\n💰 **총 유통량:** {total_money:,} 코인\n🏦 **누적 수익:** {admin_revenue:,} 코인\n━━━━━━━━━━━━━━")
        await update.message.reply_text(msg, parse_mode='Markdown')

    # [4] 채광
    elif text == ".채광":
        if user["durability"] <= 0:
            await update.message.reply_text("❌ 곡괭이가 파손되었습니다!"); return
        user["durability"] -= 1
        roll = random.uniform(0, 100); total = 0; selected = "자갈"
        for tier, items, chance in mining_tiers:
            total += chance
            if roll <= total: selected = random.choice(items); break
        user["inventory"][selected] += 1
        await update.message.reply_text(f"⛏ **{selected}** 획득! (내구도: {user['durability']})")

    # [5] 판매
    elif text == ".판매":
        summary = "**[ 광물 판매 메뉴 ]**\n"
        for t in ["1", "2", "3", "4", "5"]:
            count = sum(user["inventory"][m] for m in TIER_MAP[t])
            summary += f"💎 {t}티어 광물: {count}개\n"
        keyboard = [[InlineKeyboardButton(f"{i}티어 판매", callback_data=f"sell_{i}") for i in range(1, 4)],
                    [InlineKeyboardButton("4티어 판매", callback_data="sell_4"), InlineKeyboardButton("5티어 판매", callback_data="sell_5")],
                    [InlineKeyboardButton("✨ 전체 판매", callback_data="sell_all")]]
        await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    # [6] 송금 / 지급
    elif text.startswith(".송금"):
        try:
            _, to_id, amt = text.split(); to_id, amt = int(to_id), int(amt)
            if user["money"] >= amt > 0 and to_id in users and to_id != user_id:
                user["money"] -= amt; users[to_id]["money"] += amt
                await update.message.reply_text(f"💸 {users[to_id]['name']}님께 {amt:,} 코인 송금!")
            else: await update.message.reply_text("❌ 송금 실패.")
        except: pass
    elif text.startswith(".지급") and user_id == ADMIN_ID:
        try:
            _, t_id, amt = text.split(); t_id, amt = int(t_id), int(amt)
            if t_id in users:
                users[t_id]["money"] += amt
                await update.message.reply_text(f"🎁 {users[t_id]['name']}님께 {amt:,} 코인 지급 완료!")
        except: pass

    # [7] 바카라 (수수료 회수 시스템)
    elif text.startswith((".플", ".뱅", ".타이")):
        try:
            bet_type, amount = text.split()[0][1:], int(text.split()[1])
            if user["money"] < amount: await update.message.reply_text("❌ 잔액 부족"); return
            user["money"] -= amount
            deck = BACCARAT_DECK.copy(); random.shuffle(deck)
            p_hand, b_hand = [deck.pop(), deck.pop()], [deck.pop(), deck.pop()]
            p_s, b_s = sum(c['score'] for c in p_hand)%10, sum(c['score'] for c in b_hand)%10
            win = "player" if p_s > b_s else "banker" if b_s > p_s else "tie"
            
            # 카드 전송 (스티커)
            await context.bot.send_sticker(update.effective_chat.id, p_hand[0]['file_id'])
            await context.bot.send_sticker(update.effective_chat.id, b_hand[0]['file_id'])
            
            rate = {"플": 2, "뱅": 1.95, "타이": 8}.get(bet_type)
            if (bet_type == "플" and win == "player") or (bet_type == "뱅" and win == "banker") or (bet_type == "타이" and win == "tie"):
                win_amt = int(amount * rate); user["money"] += win_amt
                await update.message.reply_text(f"✅ 당첨! {win.upper()} 승 ({p_s}:{b_s})\n💰 잔액: {user['money']:,}")
            else:
                if ADMIN_ID in users: users[ADMIN_ID]["money"] += amount # 수익 회수
                await update.message.reply_text(f"❌ 낙첨... {win.upper()} 승 ({p_s}:{b_s})\n💰 패배 금액은 관리자에게 회수됩니다.")
        except: pass

# ==========================================
# 6. 콜백 핸들러 (인기도 및 판매 버튼)
# ==========================================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; user_id = query.from_user.id
    user = get_user(user_id, query.from_user.first_name); data = query.data

    if data.startswith("pop"):
        user["popularity"] += 1 if "up" in data else -1
        await query.answer(f"인기도가 반영되었습니다! (현재: {user['popularity']})")
    
    elif data.startswith("sell"):
        tier = data.split("_")[1]; total_earned = 0
        if tier == "all":
            for m, count in user["inventory"].items():
                total_earned += count * minerals_config[m]; user["inventory"][m] = 0
        else:
            for m in TIER_MAP[tier]:
                total_earned += user["inventory"][m] * minerals_config[m]; user["inventory"][m] = 0
        
        if total_earned > 0:
            user["money"] += total_earned
            await query.answer(f"✨ {total_earned:,} 코인 획득!", show_alert=True)
            await query.edit_message_text(f"✅ 판매 완료! 현재 잔액: {user['money']:,} 코인")
        else: await query.answer("❌ 판매할 광물이 없습니다.", show_alert=True)

# ==========================================
# 7. 실행부
# ==========================================
async def main():
    threading.Thread(target=run_health_check, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_commands))
    app.add_handler(CallbackQueryHandler(handle_callback))
    print("🚀 G-COIN BOT 찐최종본 가동 시작!")
    await app.initialize(); await app.updater.start_polling(drop_pending_updates=True); await app.start()
    while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    try: asyncio.run(main())
    except: pass
