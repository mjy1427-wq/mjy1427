import random
import time
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ==========================================
# 1. 환경 설정 (이 부분을 본인 정보로 꼭 수정하세요!)
# ==========================================
ADMIN_ID = 7476630349 #본인의 숫자 ID (예: 12345678)
BOT_TOKEN = "8771125252:AAFbKHLcDM2KhLR3MIp6ZGOnFQQWlIQUIlc" # 텔레그램 @BotFather에게 받은 토큰
OFFICIAL_CHANNEL_URL = "https://t.me/your_channel" # 공식채널 링크
SUPPORT_URL = "https://t.me/EJ1427"          # G-코인상담 (본인 아이디 링크)

# Render 포트 에러 방지용 가짜 서버
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
# 2. 데이터베이스 (채광 및 바카라 덱 전체)
# ==========================================
PICKAXE_SHOP_DATA = {
    "Wood": {"name": "나무 곡괭이", "price": 1000000, "durability": 100},
    "Stone": {"name": "돌 곡괭이", "price": 5000000, "durability": 300},
    "Iron": {"name": "철 곡괭이", "price": 15000000, "durability": 500},
    "Gold": {"name": "금 곡괭이", "price": 50000000, "durability": 1000},
    "Diamond": {"name": "다이아 곡괭이", "price": 250000000, "durability": 5000},
    "Netherite": {"name": "네더라이트 곡괭이", "price": 1000000000, "durability": 10000}
}

minerals_config = {
    "아다만티움": 500000, "다이아몬드": 350000, "오리하르콘": 250000,
    "미스릴": 160000, "플래티넘": 130000, "흑요석": 110000,
    "금": 80000, "은": 60000, "티타늄": 50000,
    "철": 30000, "구리": 20000, "석탄": 10000,
    "돌": 3000, "모래": 2000, "자갈": 1500
}

mining_tiers = [
    (1, ["아다만티움","다이아몬드","오리하르콘"], 2),
    (2, ["미스릴","플래티넘","흑요석"], 8),
    (3, ["금","은","티타늄"], 20),
    (4, ["철","구리","석탄"], 30),
    (5, ["돌","모래","자갈"], 40)
]

# 바카라 카드 데이터 (52장 풀덱)
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

def get_user(user_id, name, username=""):
    if user_id not in users:
        users[user_id] = {
            "name": name, 
            "username": f"@{username}" if username else "없음",
            "money": 0, 
            "joined_date": datetime.now().strftime("%Y-%m-%d"),
            "inv": {}, "joined": False, "pickaxe": "Wood", "durability": 100
        }
    return users[user_id]

# ==========================================
# 3. 명령어 처리 (.가입, .내정보, .채광, .상점)
# ==========================================
async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    if not text.startswith("."): return 

    user_id = update.effective_user.id
    user = get_user(user_id, update.effective_user.first_name, update.effective_user.username)
    cmd_parts = text[1:].split()
    if not cmd_parts: return
    cmd, args = cmd_parts[0], cmd_parts[1:]

    # [가입 시스템]
    if cmd == "가입":
        if user["joined"]: await update.message.reply_text("❌ 이미 가입되어 있습니다.")
        else:
            user.update({"joined": True, "money": 100000})
            await update.message.reply_text(f"✅ 가입 완료! 잔액: {user['money']:,}")

    # [내정보 시스템 - 불필요 항목 제거 및 버튼 수정]
    elif cmd == "내정보":
        now_time = datetime.now().strftime("%H:%M:%S")
        info_msg = (
            f"**[ 사용자 정보 창 ]**\n"
            f"━━━━━━━━━━━━━━\n"
            f"👤 **닉네임:** {user['name']}\n"
            f"🆔 **아이디:** {user['username']}\n"
            f"💰 **G코인:** {user['money']:,}\n"
            f"📅 **가입일:** {user['joined_date']}\n"
            f"━━━━━━━━━━━━━━\n"
            f"**{now_time}**"
        )
        keyboard = [[
            InlineKeyboardButton("공식채널 ↗️", url=OFFICIAL_CHANNEL_URL),
            InlineKeyboardButton("G-코인상담 ↗️", url=SUPPORT_URL)
        ]]
        await update.message.reply_text(info_msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    # [채광 시스템]
    elif cmd == "채광":
        if not user["joined"]:
            await update.message.reply_text("❌ `.가입`을 먼저 해주세요.")
            return
        if user["durability"] <= 0:
            await update.message.reply_text("❌ 곡괭이 파손! 상점에서 새로 구매하세요.")
            return
        
        user["durability"] -= 1
        roll = random.uniform(0, 100)
        total, selected = 0, "자갈"
        for _, items, chance in mining_tiers:
            total += chance
            if roll <= total: selected = random.choice(items); break
        
        price = minerals_config.get(selected, 0)
        user["money"] += price
        await update.message.reply_text(f"⛏ **{selected}** 획득! (+{price:,} 코인)\n📉 남은 내구도: {user['durability']}")

    # [상점 시스템]
    elif cmd == "상점":
        msg = "⛏ **곡괭이 상점**\n구매를 원하는 곡괭이를 선택하세요."
        kbd = [[InlineKeyboardButton(f"💰 {d['name']} ({d['price']:,})", callback_data=f"buy_{p}")] for p, d in PICKAXE_SHOP_DATA.items()]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kbd), parse_mode='Markdown')

    # [바카라 게임]
    elif cmd in ["플", "뱅", "타이"]:
        if args: await baccarat_logic(update, context, cmd, int(args[0]))

    # [관리자 전용 코인 생성]
    if user_id == ADMIN_ID and cmd == "생성":
        if update.message.reply_to_message and args:
            amt = int(args[0])
            t_user = get_user(update.message.reply_to_message.from_user.id, "User")
            t_user["money"] += amt
            await update.message.reply_text(f"✨ {t_user['name']}님께 {amt:,} 코인 생성 완료")

# ==========================================
# 4. 바카라 및 상점 콜백 로직
# ==========================================
async def baccarat_logic(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_type, amount):
    user = get_user(update.effective_user.id, update.effective_user.first_name)
    if user["money"] < amount: 
        await update.message.reply_text("❌ 잔액이 부족합니다.")
        return
    
    user["money"] -= amount
    deck = BACCARAT_DECK.copy()
    random.shuffle(deck)
    p_hand, b_hand = [deck.pop(), deck.pop()], [deck.pop(), deck.pop()]
    p_s = sum(c['score'] for c in p_hand) % 10
    b_s = sum(c['score'] for c in b_hand) % 10
    win = "player" if p_s > b_s else "banker" if b_s > p_s else "tie"
    bet_map = {"플": "player", "뱅": "banker", "타이": "tie"}
    
    # 카드 스티커 전송 (플레이어/뱅커 1장씩)
    await context.bot.send_sticker(update.effective_chat.id, p_hand[0]['file_id'])
    await context.bot.send_sticker(update.effective_chat.id, b_hand[0]['file_id'])

    if bet_map[bet_type] == win:
        rate = 2 if win == "player" else 1.95 if win == "banker" else 8
        user["money"] += int(amount * rate)
        res = "✅ 당첨!"
    else: res = "❌ 낙첨"
    await update.message.reply_text(f"🃏 {win.upper()} 승 ({p_s}:{b_s})\n{res}\n💰 잔액: {user['money']:,}")

async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = get_user(q.from_user.id, q.from_user.first_name)
    p_id = q.data.replace("buy_", "")
    if p_id in PICKAXE_SHOP_DATA:
        price = PICKAXE_SHOP_DATA[p_id]["price"]
        if user["money"] >= price:
            user["money"] -= price
            user["pickaxe"], user["durability"] = PICKAXE_SHOP_DATA[p_id]["name"], PICKAXE_SHOP_DATA[p_id]["durability"]
            await q.edit_message_text(f"✅ {user['pickaxe']} 장착 완료! (내구도 {user['durability']} 충전)")
        else:
            await q.answer("❌ 코인이 부족합니다!", show_alert=True)

# ==========================================
# 5. 메인 실행부
# ==========================================
if __name__ == '__main__':
    # Render 서버 유지용 쓰레드
    threading.Thread(target=run_health_check, daemon=True).start()
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # 핸들러 등록
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_commands))
    app.add_handler(CallbackQueryHandler(shop_callback))
    
    print("🚀 G COIN BOT 가동 시작!")
    app.run_polling(drop_pending_updates=True)
