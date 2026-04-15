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
LOGO_ID = "AgACAgUAAxkBAAEY9Exp3mX8S84P8f_1iZ...S2QQAAtseAALSG3VY_VfUv5nFjTseAgACAgUAAwE"
COIN_CHANNEL = "https://t.me/GCOIN7777"
SUPPORT_LINK = "https://t.me/GCOIN777_BOT"

minerals_config = {"아다만티움": 5000000, "다이아몬드": 3500000, "오리하르콘": 2500000, "미스릴": 1600000, "플래티넘": 1300000, "흑요석": 1100000, "금": 800000, "은": 600000, "티타늄": 500000, "철": 300000, "구리": 200000, "석탄": 100000, "돌": 30000, "모래": 20000, "자갈": 15000}
TIERS = {"1": ["아다만티움", "다이아몬드", "오리하르콘"], "2": ["미스릴", "플래티넘", "흑요석"], "3": ["금", "은", "티타늄"], "4": ["철", "구리", "석탄"], "5": ["돌", "모래", "자갈"]}
PICKAXE_MAX = {"나무": 200, "돌": 1000, "강철": 3000, "골드": 5000, "다이아": 7500, "아다만티움": 10000}

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
    {'n': 'HT_5', 's': 5, 'id': 'CAACAgUAAxkBAAEQ7CJp3mTrBoeYaj9SfvexBKZAVbkZMgACNBkAAiXt8FY'},
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

game_state = {"is_betting": False, "round": 23, "current_bets": [], "history": []}
game_lock = asyncio.Lock()

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
        users = {int(k): v for k, v in db.get("users", {}).items()}
        game_state["round"] = db.get("round", 23)
        game_state["history"] = db.get("history", [])
else: users = {}

def save_db():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"users": {str(k): v for k, v in users.items()}, "round": game_state["round"], "history": game_state["history"]}, f, ensure_ascii=False, indent=4)

def get_road_map():
    display = game_state["history"][-50:]
    grid = [["⚪" for _ in range(10)] for _ in range(5)]
    for idx, res in enumerate(display):
        r, c = idx % 5, idx // 5
        if c < 10: grid[r][c] = "🔵" if res == "P" else "🔴" if res == "B" else "🟢"
    return "<b>📊 바카라 그림장 (최근 50회)</b>\n" + "\n".join("".join(row) for row in grid)

# ==========================================
# 2. 메인 핸들러
# ==========================================
async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text, uid = update.message.text.strip(), update.effective_user.id
    name = update.effective_user.first_name
    uname = update.effective_user.username or "익명"

    if text == ".가입":
        if uid in users: return await update.message.reply_text("❌ 이미 가입됨")
        users[uid] = {"name": name, "username": uname, "money": 100000, "pickaxe": "나무", "durability": 200, "inventory": {m: 0 for m in minerals_config}, "last_mine": 0, "last_check": ""}
        save_db()
        kb = [[InlineKeyboardButton("📢 공지채널", url=COIN_CHANNEL)]]
        return await update.message.reply_html(f"<b>✅ 가입 완료!</b>\n100,000 G 지급됨.", reply_markup=InlineKeyboardMarkup(kb))

    if uid not in users and text.startswith("."): return await update.message.reply_text("❌ 가입 먼저")
    user = users.get(uid)
    admin = users.get(ADMIN_ID) or users.setdefault(ADMIN_ID, {"name":"ADMIN", "money":0, "inventory":{}, "pickaxe":"나무", "durability":200})

    if text == ".명령어":
        help_msg = "<b>📜 명령어 안내</b>\n\n.내정보, .채광, .수리, .판매, .송금 [ID] [금액]\n바카라: .플, .뱅, .타이 [금액]"
        kb = [[InlineKeyboardButton("📢 공지채널", url=COIN_CHANNEL), InlineKeyboardButton("🎧 상담원", url=SUPPORT_LINK)]]
        return await update.message.reply_html(help_msg, reply_markup=InlineKeyboardMarkup(kb))

    elif text == ".내정보":
        inv = ", ".join([f"{m}:{c}" for m, c in user["inventory"].items() if c > 0])
        await update.message.reply_html(f"<b>👤 {user['name']}</b>\n💰 코인: {user['money']:,} G\n⛏ 곡괭이: {user['pickaxe']} ({user['durability']})\n📦: {inv or '없음'}")

    elif text == ".채광":
        now = time.time()
        if now - user.get("last_mine",0) < 40: return await update.message.reply_text(f"⏳ {int(40-(now-user['last_mine']))}초 대기")
        if user["durability"] <= 0: return await update.message.reply_text("⛏ 파손됨")
        tier = random.choices(["5","4","3","2","1"], weights=[50, 30, 15, 4, 1])[0]
        item = random.choice(TIERS[tier])
        user["inventory"][item] += 1; user["durability"] -= 1; user["last_mine"] = now; save_db()
        await update.message.reply_html(f"⛏ <b>{item}</b> 획득!")

    elif text == ".수리":
        prices = {"나무": 100000, "돌": 500000, "강철": 1500000, "골드": 3000000, "다이아": 7000000, "아다만티움": 15000000}
        cost = prices.get(user["pickaxe"], 100000)
        if user["money"] < cost: return await update.message.reply_text(f"❌ {cost:,}G 부족")
        user["money"] -= cost; user["durability"] = PICKAXE_MAX[user["pickaxe"]]; save_db()
        await update.message.reply_text("🔧 수리 완료!")

    elif text == ".판매":
        kb = [[InlineKeyboardButton(f"{i}티어 판매", callback_data=f"sell_{i}") for i in ["1","2"]], [InlineKeyboardButton(f"{i}티어 판매", callback_data=f"sell_{i}") for i in ["3","4"]], [InlineKeyboardButton("💰 전체 판매", callback_data="sell_all")]]
        await update.message.reply_html("<b>판매할 티어를 선택하세요.</b>", reply_markup=InlineKeyboardMarkup(kb))

    elif text.startswith((".플 ", ".뱅 ", ".타이 ")):
        try:
            cmd, bet = text.split()[0], int(text.split()[1])
            if user["money"] < bet: return await update.message.reply_text("❌ 잔액 부족")
            user["money"] -= bet; admin["money"] += bet; save_db()
            game_state["current_bets"].append({"uid": uid, "cmd": cmd, "bet": bet, "user": user})
            await update.message.reply_html(f"<b>✅ {game_state['round']}회차 {cmd[1:]} {bet:,}G 베팅!</b>")
            if not game_state["is_betting"]:
                async with game_lock:
                    game_state["is_betting"] = True; await asyncio.sleep(25)
                    cid = update.effective_chat.id
                    await context.bot.send_message(cid, "<b>⚠️ 5초 전 마감!</b>", parse_mode="HTML"); await asyncio.sleep(5)
                    deck = FULL_DECK.copy(); random.shuffle(deck)
                    p, b = [deck.pop(), deck.pop()], [deck.pop(), deck.pop()]
                    ps, bs = sum(c['s'] for c in p)%10, sum(c['s'] for c in b)%10
                    if ps <= 5: p.append(deck.pop()); ps = sum(c['s'] for c in p)%10
                    if bs <= 5: b.append(deck.pop()); bs = sum(c['s'] for c in b)%10
                    win = "P" if ps > bs else "B" if bs > ps else "T"
                    game_state["history"].append(win)
                    report = f"<b>🏆 {game_state['round']}회차: {win} ({ps}:{bs})</b>\n"
                    for bt in game_state["current_bets"]:
                        if (bt["cmd"]==".플" and win=="P") or (bt["cmd"]==".뱅" and win=="B") or (bt["cmd"]==".타이" and win=="T"):
                            rate = 8 if win=="T" else (1.95 if win=="B" else 2)
                            w_amt = int(bt["bet"] * rate); bt["user"]["money"] += w_amt; admin["money"] -= w_amt
                            report += f"✅ {bt['user']['name']}: +{w_amt:,} G\n"
                        else: report += f"❌ {bt['user']['name']}: 낙첨\n"
                    await context.bot.send_message(cid, f"{report}\n{get_road_map()}", parse_mode="HTML")
                    game_state["round"] += 1; game_state["current_bets"].clear(); game_state["is_betting"] = False; save_db()
        except: pass

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; user = users.get(q.from_user.id)
    if not user: return
    data, sold = q.data, 0
    if data == "sell_all":
        for m, c in user["inventory"].items(): sold += c * minerals_config[m]; user["inventory"][m] = 0
    elif data.startswith("sell_"):
        t = data.split("_")[1]
        for m in TIERS[t]: sold += user["inventory"][m] * minerals_config[m]; user["inventory"][m] = 0
    if sold > 0: user["money"] += sold; save_db(); await q.answer(f"+{sold:,}G!"); await q.edit_message_text(f"✅ 판매완료! +{sold:,}G")
    else: await q.answer("판매할 것이 없음", show_alert=True)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")

async def main():
    port = int(os.environ.get("PORT", 8080))
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', port), HealthHandler).serve_forever(), daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_commands))
    app.add_handler(CallbackQueryHandler(on_callback))
    await app.run_polling(drop_pending_updates=True)

if __name__ == '__main__': asyncio.run(main())
