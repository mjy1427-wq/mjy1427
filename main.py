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

    # --- [ .가입 ] ---
    if text == ".가입":
        if uid in users: return await update.message.reply_text("❌ 이미 가입된 유저입니다.")
        users[uid] = {"name": name, "username": uname, "money": 100000, "pickaxe": "나무", "durability": 200, "inventory": {m: 0 for m in minerals_config}, "last_mine": 0, "last_check": ""}
        save_db()
        return await update.message.reply_html(f"<b>✅ 가입 완료!</b>\n가입 축하금 <b>100,000 G</b>가 지급되었습니다.\n\n📌 <code>.명령어</code>를 입력하여 사용법을 확인하세요!")

    if uid not in users and text.startswith("."):
        return await update.message.reply_text("❌ '.가입'을 먼저 진행해 주세요.")

    user = users.get(uid)
    admin = users.get(ADMIN_ID)
    if not admin and uid != ADMIN_ID:
        users[ADMIN_ID] = {"name": "ADMIN", "username": "admin", "money": 0, "pickaxe": "나무", "durability": 200, "inventory": {m: 0 for m in minerals_config}, "last_mine": 0, "last_check": ""}
        admin = users[ADMIN_ID]

    # --- [ .명령어 (도움말 추가) ] ---
    if text == ".명령어":
        help_msg = (
            "<b>📜 G COIN BOT 명령어 안내</b>\n\n"
            "<b>[기본 명령어]</b>\n"
            "🔹 <code>.가입</code> : 봇 이용을 위한 초기 가입 (필수)\n"
            "🔹 <code>.내정보</code> : 내 자산, 내구도, 소지품 확인\n"
            "🔹 <code>.명령어</code> : 현재 보고 있는 명령어 목록 출력\n\n"
            "<b>[경제 & 채광]</b>\n"
            "⛏ <code>.채광</code> : 광물 캐기 (쿨타임 40초, 내구도 1 소모)\n"
            "🔧 <code>.수리</code> : 곡괭이 내구도 100% 복구 (등급별 차등)\n"
            "💰 <code>.판매</code> : 보유한 광물 판매 메뉴 열기\n"
            "🎁 <code>.출석</code> : 매일 1회 출석 보상 (50,000 G)\n"
            "💸 <code>.송금 [ID] [금액]</code> : 다른 유저에게 코인 전송\n"
            "🏆 <code>.랭킹</code> : 전 서버 자산 TOP 10 확인\n\n"
            "<b>[🎰 바카라 게임]</b>\n"
            "🃏 <code>.플 [금액]</code> : 플레이어 승리에 배팅 (2배당)\n"
            "🃏 <code>.뱅 [금액]</code> : 뱅커 승리에 배팅 (1.95배당)\n"
            "🃏 <code>.타이 [금액]</code> : 타이(무승부)에 배팅 (8배당)"
        )
        return await update.message.reply_html(help_msg)

    # --- [관리자 전용] ---
    elif uid == ADMIN_ID:
        if text == ".관리자정보":
            total_money = sum(u['money'] for u in users.values())
            return await update.message.reply_html(f"<b>🏦 하우스 현황</b>\n\n👤 유저: {len(users)}명\n💰 유저 자산: {total_money:,} G\n🏢 내 잔액: {user['money']:,} G")
        elif text.startswith(".지급"):
            try:
                _, tid, amt = text.split(); tid, amt = int(tid), int(amt)
                users[tid]["money"] += amt; save_db()
                return await update.message.reply_text(f"✅ {tid}에게 {amt:,}G 지급 완료")
            except: pass
        elif text.startswith(".공지"):
            notice = text.replace(".공지", "").strip()
            for u_id in users:
                try: await context.bot.send_message(u_id, f"<b>📢 [전체 공지]</b>\n\n{notice}", parse_mode="HTML")
                except: pass
            return await update.message.reply_text("✅ 공지 발송 완료")

    # --- [유저 전용: 송금] ---
    elif text.startswith(".송금"):
        try:
            _, tid, amt = text.split(); tid, amt = int(tid), int(amt)
            if amt <= 0 or user["money"] < amt or tid not in users:
                return await update.message.reply_text("❌ 송금 실패 (잔액 부족 또는 ID 오류)")
            user["money"] -= amt; users[tid]["money"] += amt; save_db()
            await update.message.reply_html(f"<b>💸 송금 완료</b>\n대상: <code>{tid}</code>\n금액: <code>{amt:,}</code> G\n잔액: <code>{user['money']:,}</code> G")
            try: await context.bot.send_message(tid, f"💰 <code>{uid}</code>님으로부터 <code>{amt:,}</code> G가 입금되었습니다.")
            except: pass
        except: pass

    # --- [유저 전용: 판매 UI] ---
    elif text == ".판매":
        keyboard = [
            [InlineKeyboardButton("💎 1티어 판매", callback_data="sell_1"), InlineKeyboardButton("✨ 2티어 판매", callback_data="sell_2")],
            [InlineKeyboardButton("🟡 3티어 판매", callback_data="sell_3"), InlineKeyboardButton("⚪ 4티어 판매", callback_data="sell_4")],
            [InlineKeyboardButton("🪨 5티어 판매", callback_data="sell_5")],
            [InlineKeyboardButton("💰 전 체 판 매 💰", callback_data="sell_all")]
        ]
        status = "<b>📦 보관함 현황</b>\n" + " ".join([f"{t}T:{sum(user['inventory'].get(m, 0) for m in TIERS[t])}개" for t in ["1","2","3","4","5"]])
        await update.message.reply_html(f"{status}\n\n판매할 티어를 선택하세요.", reply_markup=InlineKeyboardMarkup(keyboard))

    # --- [유저 전용: 내정보 / 출석 / 랭킹 / 채광] ---
    elif text == ".내정보":
        inv_str = ", ".join([f"{m}:{c}" for m, c in user["inventory"].items() if c > 0])
        await update.message.reply_html(
            f"<b>👤 {user['name']}님의 정보</b>\n"
            f"💰 보유 코인: {user['money']:,} G\n"
            f"⛏ 곡괭이: {user['pickaxe']}\n"
            f"🔧 내구도: {user['durability']}\n"
            f"📦 소지품: {inv_str if inv_str else '텅 비어있음'}"
        )
    elif text == ".출석":
        if user.get("last_check") == str(date.today()): return await update.message.reply_text("오늘 이미 출석하셨습니다.")
        user["money"] += 50000; user["last_check"] = str(date.today()); save_db()
        await update.message.reply_text("✅ 출석 보상 50,000 G 지급!")
    elif text == ".랭킹":
        top = sorted(users.values(), key=lambda x: x['money'], reverse=True)[:10]
        msg = "<b>🏆 자산 TOP 10</b>\n\n" + "\n".join(f"{i+1}. {u['name']}: {u['money']:,} G" for i, u in enumerate(top))
        await update.message.reply_html(msg)
    elif text == ".채광":
        now = time.time()
        if now - user["last_mine"] < 40: return await update.message.reply_text(f"⏳ 대기: {int(40 - (now - user['last_mine']))}초")
        if user["durability"] <= 0: return await update.message.reply_text("⛏ 곡괭이 파손! .수리 필요")
        tier = random.choices(["5","4","3","2","1"], weights=[50, 30, 15, 4, 1])[0]
        item = random.choice(TIERS[tier])
        user["inventory"][item] += 1; user["durability"] -= 1; user["last_mine"] = now; save_db()
        await update.message.reply_html(f"⛏ <b>{item}</b> 획득! (내구도: {user['durability']})")

    # --- [유저 전용: 수리 (등급별 차등 금액)] ---
    elif text == ".수리":
        repair_prices = {"나무": 100000, "돌": 500000, "강철": 1500000, "골드": 3000000, "다이아": 7000000, "아다만티움": 15000000}
        p_type = user["pickaxe"]
        max_dur = PICKAXE_MAX.get(p_type, 200)
        cost = repair_prices.get(p_type, 100000)

        if user["durability"] >= max_dur:
            return await update.message.reply_text("✅ 이미 내구도가 최상태입니다.")
        if user["money"] < cost:
            return await update.message.reply_html(f"❌ 코인이 부족합니다!\n<b>{p_type}</b> 수리비: <code>{cost:,}</code> G")

        user["money"] -= cost; user["durability"] = max_dur; save_db()
        await update.message.reply_html(f"<b>🔧 곡괭이 수리 완료!</b>\n\n사용된 코인: <code>{cost:,}</code> G\n현재 내구도: <b>{max_dur} / {max_dur}</b>\n남은 잔액: <code>{user['money']:,}</code> G")

    # --- [유저 전용: 바카라] ---
    elif text.startswith((".플 ", ".뱅 ", ".타이 ")):
        try:
            cmd, bet = text.split()[0], int(text.split()[1])
            if user["money"] < bet: return await update.message.reply_text("❌ 잔액이 부족합니다.")
            user["money"] -= bet; admin["money"] += bet; save_db()
            game_state["current_bets"].append({"uid": uid, "cmd": cmd, "bet": bet, "user": user})
            
            await update.message.reply_html(f"<b>배팅완료 ✅</b>\n<b>회차 : {game_state['round']}회차</b>\n<b>배팅 : {cmd.replace('.', '')}</b>\n<b>금액 : {bet:,}코인 베팅 완료!</b>")

            if not game_state["is_betting"]:
                async with game_lock:
                    game_state["is_betting"] = True
                    await asyncio.sleep(30)
                    game_state["is_betting"] = False
                    
                    cid = update.effective_chat.id
                    await context.bot.send_message(cid, f"<b>📢 {game_state['round']}회차 베팅 마감!</b>", parse_mode="HTML")
                    
                    deck = FULL_DECK.copy(); random.shuffle(deck)
                    p, b = [deck.pop(), deck.pop()], [deck.pop(), deck.pop()]
                    
                    for i, (msg, cards) in enumerate([("플레이어", p), ("뱅커", b)]):
                        await context.bot.send_message(cid, f"<b>🎴 {msg} 카드 공개</b>", parse_mode="HTML")
                        for c in cards: await context.bot.send_sticker(cid, c['id']); await asyncio.sleep(1.2)

                    ps, bs = sum(c['s'] for c in p)%10, sum(c['s'] for c in b)%10
                    if ps <= 5:
                        tc = deck.pop(); p.append(tc); ps = sum(c['s'] for c in p)%10
                        await context.bot.send_message(cid, "<b>🃏 플레이어 서드 카드</b>", parse_mode="HTML"); await context.bot.send_sticker(cid, tc['id'])
                    if bs <= 5:
                        tc = deck.pop(); b.append(tc); bs = sum(c['s'] for c in b)%10
                        await context.bot.send_message(cid, "<b>🃏 뱅커 서드 카드</b>", parse_mode="HTML"); await context.bot.send_sticker(cid, tc['id'])

                    win = "P" if ps > bs else "B" if bs > ps else "T"
                    game_state["history"].append(win)
                    
                    await context.bot.send_photo(cid, photo=LOGO_ID, caption=f"<b>🔥 {win} 승리! 🔥 ({ps}:{bs})</b>", parse_mode="HTML")

                    report = ""
                    for bt in game_state["current_bets"]:
                        if (bt["cmd"]==".플" and win=="P") or (bt["cmd"]==".뱅" and win=="B") or (bt["cmd"]==".타이" and win=="T"):
                            rate = 8 if win=="T" else (1.95 if win=="B" else 2)
                            win_amt = int(bt["bet"] * rate); bt["user"]["money"] += win_amt; admin["money"] -= win_amt
                            report += f"✅ @{bt['user']['username']} +{win_amt:,}G\n"
                        else: report += f"❌ @{bt['user']['username']} 미적중\n"

                    await context.bot.send_message(cid, f"<b>📊 {game_state['round']}회차 정산</b>\n\n{report}\n{get_road_map()}", parse_mode="HTML")
                    game_state["round"] += 1; game_state["current_bets"].clear(); save_db()
        except: pass

# ==========================================
# 3. 콜백 (티어별 개별 판매 처리)
# ==========================================
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; uid = q.from_user.id; user = users.get(uid)
    if not user: return
    
    data, sold_money, tier_name = q.data, 0, ""
    if data == "sell_all":
        for m, c in user["inventory"].items(): sold_money += c * minerals_config[m]; user["inventory"][m] = 0
        tier_name = "전체"
    elif data.startswith("sell_"):
        t = data.split("_")[1]
        for m in TIERS[t]:
            count = user["inventory"].get(m, 0)
            sold_money += count * minerals_config[m]; user["inventory"][m] = 0
        tier_name = f"{t}티어"

    if sold_money > 0:
        user["money"] += sold_money; save_db()
        await q.answer(f"+{sold_money:,} G 획득!")
        await q.edit_message_text(f"<b>✅ {tier_name} 판매 완료</b>\n\n수익: <code>{sold_money:,}</code> G\n잔액: <code>{user['money']:,}</code> G", parse_mode="HTML")
    else: await q.answer("판매할 광물이 없습니다!", show_alert=True)

# ==========================================
# 4. 서버 시작
# ==========================================
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_commands))
    app.add_handler(CallbackQueryHandler(on_callback))
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', 8080), BaseHTTPRequestHandler).serve_forever(), daemon=True).start()
    await app.run_polling(drop_pending_updates=True)

if __name__ == '__main__': asyncio.run(main())
