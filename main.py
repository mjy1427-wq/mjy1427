import random, os, threading, asyncio, json, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ==========================================
# 1. 설정 및 데이터베이스
# ==========================================
ADMIN_ID = 7476630349 
BOT_TOKEN = "8484299407:AAGfYDpLhfS7eTIjsC16Fe6Bklqf6T22Gv0" 
DATA_FILE = "gcoin_ultra_final.json"

MINING_DELAY = 40 
minerals_config = {"아다만티움": 5000000, "다이아몬드": 3500000, "오리하르콘": 2500000, "미스릴": 1600000, "플래티넘": 1300000, "흑요석": 1100000, "금": 800000, "은": 600000, "티타늄": 500000, "철": 300000, "구리": 200000, "석탄": 100000, "돌": 30000, "모래": 20000, "자갈": 15000}
TIERS = {"1": ["아다만티움", "다이아몬드", "오리하르콘"], "2": ["미스릴", "플래티넘", "흑요석"], "3": ["금", "은", "티타늄"], "4": ["철", "구리", "석탄"], "5": ["돌", "모래", "자갈"]}
PICKAXE_MAX = {"나무": 200, "돌": 1000, "강철": 3000, "골드": 5000, "다이아": 7500, "아다만티움": 10000}

# [바카라 카드 데이터]
FULL_DECK = [
    {'n': 'SP_10', 's': 0, 'id': 'CAACAgUAAxkBAAEQ7Exp3mWoCRUfVj-ZE5CmN3IUjgtvGQAC2SYAAvCQ8VbM3lvO79VzBTsE'},
    {'n': 'HT_10', 's': 0, 'id': 'CAACAgUAAxkBAAEQ7E5p3mVSE9Y_S9vS6_WAAKGhAACOv_4VpJmKq_Wz_FTOzsE'},
    {'n': 'DI_10', 's': 0, 'id': 'CAACAgUAAxkBAAEQ7Elp3mWdvgYOMw9HgRc2Il7kbpGkGwACExsAAtRO8FahNaTDKDCFzTsE'},
    {'n': 'CL_10', 's': 0, 'id': 'CAACAgUAAxkBAAEQ7Ehp3mWd8ioZzOX1iY2u7FRMlZc4fAACMRsAAhGP8FbmO81P4gZ3DdSE'},
    {'n': 'SP_J', 's': 0, 'id': 'CAACAgUAAxkBAAEQ7GJp3mXczpHSUQABLPWVYJGRB79K7GUAAs4ZAAljo_BWHVM8Q7mxKjc7BA'},
    {'n': 'HT_J', 's': 0, 'id': 'CAACAgUAAxkBAAEQ7FBp3mVVZ_S9vS6_WAAKGhAACOv_4VpJmKq_Wz_FTOzsE'},
    {'n': 'DI_J', 's': 0, 'id': 'CAACAgUAAxkBAAEQ7F5p3mXP7eNL3nEmVkYmy9EnTxmKXAACPbSAAuAa8FauMWEkVitpddSE'},
    {'n': 'CJ_J', 's': 0, 'id': 'CAACAgUAAxkBAAEQ7F1p3mXOHKrfuHvAoDFBdNEGk1YfPgACbBsAAgiy-Fb54wO73qUBddSE'},
    {'n': 'SP_Q', 's': 0, 'id': 'CAACAgUAAxkBAAEQ7HJp3mX7k8OEWVS8Gjf4e99UVKKQMgACBRcAAr0P8Fa8o_9h2ERTKdSE'},
    {'n': 'HT_Q', 's': 0, 'id': 'CAACAgUAAxkBAAEQ7HFp3mX77o4V07GRhTZ7p3VjbvEFxgACmxkAAmFN8FYOgeAm8_YYfzsE'},
    {'n': 'DI_Q', 's': 0, 'id': 'CAACAgUAAxkBAAEQ7G5p3mX09qlW7oCyp-k3Z8KA1E0K3QACdxsAAtvN8FbMD0922U9hiDSE'},
    {'n': 'CL_Q', 's': 0, 'id': 'CAACAgUAAxkBAAEQ7G1p3mXzjWB4kHKsr0AfljIrFXEDHQA C9BoAAhcI-VaN6tW2wXj8yTsE'},
    {'n': 'SP_K', 's': 0, 'id': 'CAACAgUAAxkBAAEQ7Gpp3mXt8mcHJ_JyKQgTFnHAwdWtMwACCRoAAi-h-FazQTiuzxZmEzse'},
    {'n': 'HT_K', 's': 0, 'id': 'CAACAgUAAxkBAAEQ7Glp3mXsAAEdy6_qhm4sGBCZm1DLc38AAp8cAAJqqfhWcF0OQx5DFL87BA'},
    {'n': 'DI_K', 's': 0, 'id': 'CAACAgUAAxkBAAEQ7GZp3mXKuM-jJaBuOPhPFZSFMiHaSAACax8AAjMH8FYMbgTuO1crrjsE'},
    {'n': 'CL_K', 's': 0, 'id': 'CAACAgUAAxkBAAEQ7GVp3mXje9-bjU0gVAXEVK_LZT_TMAACdxgAAgk48VaWvHPT0d5KfDsE'},
    {'n': 'SP_A', 's': 1, 'id': 'CAACAgUAAxkBAAEQ7Fhp3mW8BGcPAUjH-Xu4bsjSDHIUSgACwh4AASAz8VYhnQL59WSxmzse'},
    {'n': 'HT_A', 's': 1, 'id': 'CAACAgUAAxkBAAEQ7Fdp3mW7GOA0zTWFiMJqzdhQvuOzdgAC7RwAArhl8Faz3VKPQgKXMzse'},
    {'n': 'DI_A', 's': 1, 'id': 'CAACAgUAAxkBAAEQ7FFp3mWXiDQVv4f7uMQbflbdJfLutgACzCAAAla48Vb9T8wXbzPPfjse'},
    {'n': 'CL_A', 's': 1, 'id': 'CAACAgUAAxkBAAEQ7FBp3mWXjbV3Q5OEMdinCJfQltMsqQACHhsAAuaM8VYvC46og1B2ajse'},
    {'n': 'HT_2', 's': 2, 'id': 'CAACAgUAAxkBAAEQ7App3mSRViSy9QABBrH7Hjrq5ouaZZ8AAtcaAALQMflWUcolg756dC47BA'},
    {'n': 'SP_2', 's': 2, 'id': 'CAACAgUAAxkBAAEQ7Axp3mSaEUEgc5majSVq8OIh7ts2pwACQh4AAuxU8FYnql4-ZGGRJTsE'},
    {'n': 'CL_2', 's': 2, 'id': 'CAACAgUAAxkBAAEQ7AZp3mR_TSeuCgnjXc4qbGPN_M1yVgACWx4AAubz8VbWRCfXXRC59jsE'},
    {'n': 'DI_2', 's': 2, 'id': 'CAACAgUAAxkBAAEQ7Ahp3mSHxRGhAYCJQWfKunVrex9XKwACJx0AAhb5-VZ5zrTMtEsdvjsE'},
    {'n': 'CL_3', 's': 3, 'id': 'CAACAgUAAxkBAAEQ7A5p3mSksYYgf8iEeXDDR8fq1KRP4QACaR8AAv5Y8VaTLVf2T489ZzsE'},
    {'n': 'DI_3', 's': 3, 'id': 'CAACAgUAAxkBAAEQ7BBp3mSukxqN7O7HsmM4-5hD9GEPywACPB0AAjb28Fb2JkBj8-_NNjsE'},
    {'n': 'HT_3', 's': 3, 'id': 'CAACAgUAAxkBAAEQ7BJp3mS1yaKFOG_5CrVrxEyyZV3wAACfhwAAsgs8VZuR148a475jsE'},
    {'n': 'SP_3', 's': 3, 'id': 'CAACAgUAAxkBAAEQ7BRp3mS-_UwQIUAYhXc_AcvUY9rfvgACrxoAAuBR8VbK9G7nf3c54TsE'},
    {'n': 'HT_4', 's': 4, 'id': 'CAACAgUAAxkBAAEQ7Bpp3mTSM0lu28ee05WEDvA60gj02QACcB4AAmM48VYrEVYD2RMdTzsE'},
    {'n': 'SP_4', 's': 4, 'id': 'CAACAgUAAxkBAAEQ7Bxp3mTXgly2BFytQ15h9ry_MruqwwACjxwAAsth8FZ1KAQ0WpYDlzsE'},
    {'n': 'CL_4', 's': 4, 'id': 'CAACAgUAAxkBAAEQ7BZp3mTEreDBUC8SDd6zMknOuslsJQAC-x0AAk898VallRAp2VysPDsE'},
    {'n': 'DI_4', 's': 4, 'id': 'CAACAgUAAxkBAAEQ7Bhp3mTLrFneb4g5FGcLDQqiiXfhKwACYx0AAhbh8VaJgN_C89Ws4jsE'},
    {'n': 'CL_5', 's': 5, 'id': 'CAACAgUAAxkBAAEQ7B5p3mTciJpNbwOUcDGtJanwooEMAACHyEAAofK8FbQIR7YFejOuDsE'},
    {'n': 'DI_5', 's': 5, 'id': 'CAACAgUAAxkBAAEQ7CBp3mTk31W6hLC6UcCAv373S4akGwACVxwAAidE-FYFTRXzoYHR0jsE'},
    {'n': 'HT_5', 's': 5, 'id': 'CAACAgUAAxkBAAEQ7CJp3mTrBoeYaj9SfvexBKZAVbkZMgACNBkAAiXt8FYwis7G_aMsczsE'},
    {'n': 'SP_5', 's': 5, 'id': 'CAACAgUAAxkBAAEQ7CRp3mT632ulFb6I-YFRwOxC5biGdgACEh4AAvYr8Vb0JSaolbjdrTsE'},
    {'n': 'CL_6', 's': 6, 'id': 'CAACAgUAAxkBAAEQ7CZp3mUCEmoK8EuD6D544yHOaLu3-wAC9hgAAq89-FaiUQuOgwiwzsE'},
    {'n': 'DI_6', 's': 6, 'id': 'CAACAgUAAxkBAAEQ7Chp3mUNHWqdz7d6zLs1dzO5IJYy3QACfxwAAou88FYld8a9twT_YzsE'},
    {'n': 'HT_6', 's': 6, 'id': 'CAACAgUAAxkBAAEQ7Clp3mUOKoepG6cx3X8DQVIG9V2sLAAC5BsAAg768FbNdm1szl6UUTsE'},
    {'n': 'SP_6', 's': 6, 'id': 'CAACAgUAAxkBAAEQ7Chp3mUOCoepG6cx3X8DQVIG9V2sLAAC5BsAAg768FbNdm1szl6UUTsE'},
    {'n': 'SP_7', 's': 7, 'id': 'CAACAgUAAxkBAAEQ7DFp3mUpnCA-GEJ8oaLYcdSneGJu3QACuhoAAjFN8FbTzoXAcmpBCTsE'},
    {'n': 'HT_7', 's': 7, 'id': 'CAACAgUAAxkBAAEQ7DBp3mUpBnm0QPY0a2CaDUGGzfqmqwACiBsAAtB0-Fb1BMJRuaIUJDSE'},
    {'n': 'CL_7', 's': 7, 'id': 'CAACAgUAAxkBAAEQ7C1p3mUaD__E8YaJEA2puTxbnjHnyQACth0AAjMq8Val7P12Gpjr2DsE'},
    {'n': 'DI_7', 's': 7, 'id': 'CAACAgUAAxkBAAEQ7Hdp3mYSx96E3k_hPNMS_FOdDQAB0b4AAk0dAAITVfFW4T3rXlj6AAFWOWqQ'},
    {'n': 'SP_8', 's': 8, 'id': 'CAACAgUAAxkBAAEQ7Dlp3mVKb8CjYmV0DNZCrujiZx5S5wACqScAAnS48FYYwX-ZCyh0iDsE'},
    {'n': 'HT_8', 's': 8, 'id': 'CAACAgUAAxkBAAEQ7Dhp3mVJ5yNHLy28B9BHT2qfgsv2rQACdB4AAnMM8VZTMSvcZqfutzsE'},
    {'n': 'DI_8', 's': 8, 'id': 'CAACAgUAAxkBAAEQ7DVp3mU13uK_NKkAAUefJseY-eW03RAAAi0bAAKhoPFWLno-ReRJ4H47BA'},
    {'n': 'CL_8', 's': 8, 'id': 'CAACAgUAAxkBAAEQ7DRp3mU1sNsf-ebu7c80oVqgji32mgACpR8AAuNO8VaW49WvovXUZzsE'},
    {'n': 'SP_9', 's': 9, 'id': 'CAACAgUAAxkBAAEQ7EVp3mWUy1KHmKxHMBmbmo738zl1GQACyhkAAmI9-FY-6RY8e3-UETsE'},
    {'n': 'HT_9', 's': 9, 'id': 'CAACAgUAAxkBAAEQ7ERp3mWT3RbXuluWyAVqNgpJ4KSunwACERoAAnvy-VaomxXwVnT5RDsE'},
    {'n': 'D9_9', 's': 9, 'id': 'CAACAgUAAxkBAAEQ7EFp3mWGN5nL3ma1jSENoY1PYOLCgwACVx4AAjW7-Fa30fLUp ygsgzsE'},
    {'n': 'CL_9', 's': 9, 'id': 'CAACAgUAAxkBAAEQ7EBp3mWGYNOoFfvUelUEqB__xWN40wACQxwAAqMu8FZUMsBrOgtazjsE'}
]

baccarat_history = []

# ==========================================
# 2. 데이터 관리 및 유틸리티
# ==========================================
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        users = {int(k): v for k, v in json.load(f).items()}
else: users = {}

def save_db():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def get_u(uid, name, uname):
    if uid not in users:
        users[uid] = {"name": name, "username": uname or "익명", "money": 100000, "joined": True, "pickaxe": "나무", "durability": 200, "inventory": {m: 0 for m in minerals_config}, "last_mine": 0, "last_check": ""}
        save_db()
    return users[uid]

def get_road_map():
    display = baccarat_history[-50:]
    grid = [["⚪" for _ in range(10)] for _ in range(5)]
    for idx, res in enumerate(display):
        r, c = idx % 5, idx // 5
        if c < 10: grid[r][c] = "🔵" if res == "P" else "🔴" if res == "B" else "🟢"
    return "<b>📊 바카라 그림장 (최근 50회)</b>\n" + "\n".join("".join(row) for row in grid)

# ==========================================
# 3. 명령어 핸들러
# ==========================================
async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text, uid = update.message.text.strip(), update.effective_user.id
    user = get_u(uid, update.effective_user.first_name, update.effective_user.username)
    admin = get_u(ADMIN_ID, "관리자", "admin")

    # --- [관리자 전용] ---
    if uid == ADMIN_ID:
        if text == ".관리자정보":
            total_money = sum(u['money'] for u in users.values())
            msg = f"<b>🏦 하우스 운영 현황</b>\n\n👤 전체 유저: {len(users)}명\n💰 총 자산: {total_money:,} G\n🏢 누적 수익: {user['money']:,} G"
            return await update.message.reply_html(msg)
        elif text.startswith(".지급"):
            try:
                _, target_id, amt = text.split()
                target_id, amt = int(target_id), int(amt)
                if target_id in users:
                    users[target_id]["money"] += amt; save_db()
                    return await update.message.reply_text(f"✅ {target_id}에게 {amt:,}G 지급 완료")
            except: pass
        elif text.startswith(".공지"):
            notice = text.replace(".공지", "").strip()
            for u_id in users:
                try: await context.bot.send_message(u_id, f"<b>📢 [전체 공지]</b>\n\n{notice}", parse_mode="HTML")
                except: pass
            return await update.message.reply_text("✅ 공지 발송 완료")

    # --- [유저 명령어] ---
    if text == ".출석":
        today = str(date.today())
        if user.get("last_check") == today: return await update.message.reply_text("오늘 이미 완료!")
        user["money"] += 50000; user["last_check"] = today; save_db()
        await update.message.reply_text("✅ 출석 보상 50,000 G 지급!")
    
    elif text == ".랭킹":
        top = sorted(users.values(), key=lambda x: x['money'], reverse=True)[:10]
        msg = "<b>🏆 자산 순위 TOP 10</b>\n\n" + "\n".join(f"{i+1}. {u['name']}: {u['money']:,} G" for i, u in enumerate(top))
        await update.message.reply_html(msg)

    elif text == ".채광":
        now = time.time()
        if now - user["last_mine"] < MINING_DELAY:
            return await update.message.reply_text(f"⏳ 대기: {int(MINING_DELAY - (now - user['last_mine']))}초")
        if user["durability"] <= 0: return await update.message.reply_text("⛏ 곡괭이 파손! .수리 필요")
        tier = random.choices(["5","4","3","2","1"], weights=[50, 30, 15, 4, 1])[0]
        item = random.choice(TIERS[tier])
        user["inventory"][item] += 1; user["durability"] -= 1; user["last_mine"] = now; save_db()
        await update.message.reply_html(f"⛏ <b>{item}</b> 획득! ({minerals_config[item]:,} G)\n🔧 내구도: {user['durability']}/{PICKAXE_MAX[user['pickaxe']]}")

    elif text.startswith((".플", ".뱅", ".타")):
        try:
            cmd, bet = text.split()[0], int(text.split()[1])
            if user["money"] < bet: return await update.message.reply_text("잔액 부족")
            user["money"] -= bet; admin["money"] += bet; save_db()
            deck = FULL_DECK.copy(); random.shuffle(deck)
            p = [deck.pop(), deck.pop()]; b = [deck.pop(), deck.pop()]
            ps, bs = sum(c['s'] for c in p)%10, sum(c['s'] for c in b)%10
            await update.message.reply_html("<b>🎴 카드 공개 시작</b>")
            for c in p: await context.bot.send_sticker(uid, c['id'])
            await asyncio.sleep(1)
            for c in b: await context.bot.send_sticker(uid, c['id'])
            if ps <= 5:
                tc = deck.pop(); p.append(tc); ps = sum(c['s'] for c in p)%10
                await asyncio.sleep(0.5); await context.bot.send_sticker(uid, tc['id'])
            if bs <= 5:
                tc = deck.pop(); b.append(tc); bs = sum(c['s'] for c in b)%10
                await asyncio.sleep(0.5); await context.bot.send_sticker(uid, tc['id'])
            win = "P" if ps > bs else "B" if bs > ps else "T"
            baccarat_history.append(win)
            res = f"\n{get_road_map()}\n\n결과: {ps}:{bs} ({win})\n"
            if (cmd==".플" and win=="P") or (cmd==".뱅" and win=="B") or (cmd==".타" and win=="T"):
                rate = 8 if win=="T" else (1.95 if win=="B" else 2)
                win_amt = int(bet * rate)
                user["money"] += win_amt; admin["money"] -= win_amt
                res += f"🏆 <b>적중 +{win_amt:,} G</b>"
            else: res += "❌ 낙첨"
            save_db(); await update.message.reply_html(res)
        except: pass

    elif text == ".판매":
        btns = [[InlineKeyboardButton(f"{t}티어", callback_data=f"s_{t}") for t in ["1","2","3"]],
                [InlineKeyboardButton("4티어", callback_data="s_4"), InlineKeyboardButton("5티어", callback_data="s_5")],
                [InlineKeyboardButton("💰 전체 판매", callback_data="s_all")]]
        await update.message.reply_html("<b>📦 판매 메뉴</b>", reply_markup=InlineKeyboardMarkup(btns))

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = users.get(q.from_user.id)
    if not user: return
    data, sold = q.data, 0
    if data == "s_all":
        for m, c in user["inventory"].items(): sold += c * minerals_config[m]; user["inventory"][m] = 0
    elif data.startswith("s_"):
        for m in TIERS[data[2:]]: sold += user["inventory"][m] * minerals_config[m]; user["inventory"][m] = 0
    user["money"] += sold; save_db(); await q.answer(f"+{sold:,} G"); await q.edit_message_text(f"✅ 판매 완료: +{sold:,} G")

# ==========================================
# 4. Render 포트 에러 해결용 웹 서버
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is Running")
    def log_message(self, format, *args): return

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"✅ Health Check Server started on port {port}")
    httpd.serve_forever()

# ==========================================
# 5. 메인 실행부
# ==========================================
async def main():
    # 웹 서버를 별도 스레드에서 실행 (Render 포트 감지용)
    threading.Thread(target=run_health_server, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_commands))
    app.add_handler(CallbackQueryHandler(on_callback))

    print("🤖 Telegram Bot Starting...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
