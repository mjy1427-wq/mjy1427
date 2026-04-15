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
SUPPORT_URL = "https://t.me/GCOIN777_BOT" 
NOTICE_URL = "https://t.me/GCOIN7777"

# 바카라 회차 관리
game_room = {"is_open": False, "round_no": 1, "end_time": 0, "bets": []}
baccarat_history = []

MINING_DELAY = 40 
minerals_config = {"아다만티움": 5000000, "다이아몬드": 3500000, "오리하르콘": 2500000, "미스릴": 1600000, "플래티넘": 1300000, "흑요석": 1100000, "금": 800000, "은": 600000, "티타늄": 500000, "철": 300000, "구리": 200000, "석탄": 100000, "돌": 30000, "모래": 20000, "자갈": 15000}
TIERS = {"1": ["아다만티움", "다이아몬드", "오리하르콘"], "2": ["미스릴", "플래티넘", "흑요석"], "3": ["금", "은", "티타늄"], "4": ["철", "구리", "석탄"], "5": ["돌", "모래", "자갈"]}
PICKAXE_MAX = {"나무": 200, "돌": 1000, "강철": 3000, "골드": 5000, "다이아": 7500, "아다만티움": 10000}

# [바카라 52장 전체 데이터 - 절대 생략 없음]
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

# --- DB 처리 및 데이터 로드 ---
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        users = {int(k): v for k, v in json.load(f).items()}
else: users = {}

def save_db():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def get_u(uid, name, uname):
    if uid not in users:
        users[uid] = {"name": name, "username": uname or "익명", "money": 100000, "pickaxe": "나무", "durability": 200, "inventory": {m: 0 for m in minerals_config}, "last_mine": 0, "last_check": ""}
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
# 2. 실시간 멀티 바카라 엔진
# ==========================================
async def process_baccarat(context: ContextTypes.DEFAULT_TYPE, chat_id):
    global game_room
    round_no = game_room["round_no"]
    
    # 1. 베팅 마감
    await context.bot.send_message(chat_id, f"<b>🚨 [제 {round_no}회차] 베팅 마감!</b>", parse_mode="HTML")
    
    # 2. 결과 예고 (5초)
    await asyncio.sleep(5)
    await context.bot.send_message(chat_id, "<b>🔔 5초 후 결과를 발표합니다!</b>", parse_mode="HTML")
    await asyncio.sleep(2)

    deck = FULL_DECK.copy(); random.shuffle(deck)
    p, b = [deck.pop(), deck.pop()], [deck.pop(), deck.pop()]
    ps, bs = sum(c['s'] for c in p)%10, sum(c['s'] for c in b)%10

    # 3. 카드 오픈 연출
    await context.bot.send_message(chat_id, "<b>[Player Card]</b>", parse_mode="HTML")
    for c in p: await context.bot.send_sticker(chat_id, c['id'])
    await asyncio.sleep(1)
    await context.bot.send_message(chat_id, "<b>[Banker Card]</b>", parse_mode="HTML")
    for c in b: await context.bot.send_sticker(chat_id, c['id'])

    # [바카라 서드 카드 룰]
    if ps <= 5:
        await asyncio.sleep(1); tc = deck.pop(); p.append(tc); ps = sum(c['s'] for c in p)%10
        await context.bot.send_message(chat_id, "🃏 플레이어 추가 카드!"); await context.bot.send_sticker(chat_id, tc['id'])
    if bs <= 5:
        await asyncio.sleep(1); tc = deck.pop(); b.append(tc); bs = sum(c['s'] for c in b)%10
        await context.bot.send_message(chat_id, "🃏 뱅커 추가 카드!"); await context.bot.send_sticker(chat_id, tc['id'])

    # 4. 정산
    win = "P" if ps > bs else "B" if bs > ps else "T"
    baccarat_history.append(win)
    admin = get_u(ADMIN_ID, "관리자", "admin")
    
    res_msg = f"<b>🏆 제 {round_no}회차 결과: {win} ({ps}:{bs})</b>\n\n"
    for bet in game_room["bets"]:
        u = users[bet['uid']]
        rate = 8 if win=="T" else (1.95 if win=="B" else 2)
        if (bet['side']=="P" and win=="P") or (bet['side']=="B" and win=="B") or (bet['side']=="T" and win=="T"):
            w_amt = int(bet['amount'] * rate); u["money"] += w_amt; admin["money"] -= w_amt
            res_msg += f"✅ {u['name']}: +{w_amt:,} G\n"
        else: res_msg += f"❌ {u['name']}: 낙첨\n"
    
    res_msg += f"\n{get_road_map()}"
    await context.bot.send_message(chat_id, res_msg, parse_mode="HTML")
    
    game_room["is_open"] = False; game_room["bets"] = []; game_room["round_no"] += 1; save_db()

# ==========================================
# 3. 메인 핸들러
# ==========================================
async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_room
    if not update.message or not update.message.text: return
    text, uid, chat_id = update.message.text.strip(), update.effective_user.id, update.message.chat_id
    user = get_u(uid, update.effective_user.first_name, update.effective_user.username)
    admin = get_u(ADMIN_ID, "관리자", "admin")

    # --- 관리자 전용 ---
    if uid == ADMIN_ID:
        if text == ".관리자정보":
            total_money = sum(u['money'] for u in users.values())
            msg = (f"<b>🏦 하우스 운영 현황</b>\n\n👤 유저: {len(users)}명\n💰 총 유통량: {total_money:,} G\n🏢 금고 잔액: {user['money']:,} G")
            return await update.message.reply_html(msg)
        elif text.startswith(".공지"):
            msg = text.replace(".공지", "").strip()
            for tid in users:
                try: await context.bot.send_message(tid, f"<b>📢 공지:</b> {msg}", parse_mode="HTML")
                except: pass
            return

    # --- 유저 명령어 ---
    if text.startswith((".플", ".뱅", ".타")):
        try:
            side = "P" if ".플" in text else "B" if ".뱅" in text else "T"
            amt = int(text.split()[1])
            if user["money"] < amt: return await update.message.reply_text("❌ 잔액 부족")

            if not game_room["is_open"]:
                game_room["is_open"] = True
                game_room["end_time"] = time.time() + 30
                asyncio.create_task(asyncio.sleep(30)).add_done_callback(lambda _: asyncio.create_task(process_baccarat(context, chat_id)))
                await update.message.reply_html(f"<b>🎰 제 {game_room['round_no']}회차 베팅 시작!</b>\n30초 후 마감됩니다.")

            user["money"] -= amt; admin["money"] += amt; save_db()
            game_room["bets"].append({"uid": uid, "side": side, "amount": amt})
            await update.message.reply_text(f"✅ {side} {amt:,}G 완료!")
        except: pass

    elif text == ".채광":
        now = time.time()
        if now - user["last_mine"] < MINING_DELAY: return await update.message.reply_text(f"⏳ {int(MINING_DELAY-(now-user['last_mine']))}초 대기")
        if user["durability"] <= 0: return await update.message.reply_text("⛏ 내구도 0!")
        tier = random.choices(["5","4","3","2","1"], weights=[50, 30, 15, 4, 1])[0]
        item = random.choice(TIERS[tier])
        user["inventory"][item] += 1; user["durability"] -= 1; user["last_mine"] = now; save_db()
        await update.message.reply_html(f"⛏ <b>{item}</b> 획득! (🔧 {user['durability']}/{PICKAXE_MAX[user['pickaxe']]})")

    elif text in [".문의", ".상담"]:
        await update.message.reply_html("상담채널", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("센터 이동", url=SUPPORT_URL)]]))
    elif text in [".공지", ".채널"]:
        await update.message.reply_html("공지채널", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("채널 입장", url=NOTICE_URL)]]))

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_commands))
    await app.initialize(); await app.updater.start_polling(); await app.start(); await asyncio.Event().wait()

if __name__ == '__main__': asyncio.run(main())
