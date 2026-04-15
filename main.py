import random
import os
import threading
import asyncio
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ==========================================
# 1. 환경 설정 및 데이터베이스
# ==========================================
ADMIN_ID = 7476630349 
BOT_TOKEN = "8484299407:AAGfYDpLhfS7eTIjsC16Fe6Bklqf6T22Gv0" 
OFFICIAL_CHANNEL_URL = "https://t.me/GCOIN7777" 
SUPPORT_URL = "https://t.me/GCOIN777_BOT"
DATA_FILE = "database_gold_final.json" # 충돌 방지용 새 파일명

# 곡괭이 및 광물 설정
PICKAXE_CONFIG = {
    "나무": {"max": 200, "repair_fixed": 5000, "luck": 0},
    "돌": {"max": 1000, "repair_fixed": 50000, "luck": 1},
    "강철": {"max": 3000, "repair_fixed": 300000, "luck": 3},
    "골드": {"max": 5000, "repair_fixed": 1000000, "luck": 5},
    "다이아": {"max": 7500, "repair_fixed": 10000000, "luck": 10},
    "아다만티움": {"max": 10000, "repair_fixed": 20000000, "luck": 20}
}

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

# [올려주신 데이터 100% 반영] 바카라 52장 덱
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
    {'name': 'HT_Q', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7HFp3mX77o4V07GRhTZ7p3VjbvEFxgACmxkAAmFN8FYOgeAm8_YYfzsE'},
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

# 데이터베이스 로드 및 저장
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        users = {int(k): v for k, v in json.load(f).items()}
else:
    users = {}

def save_db():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def init_user_data(uid, name, username):
    if uid not in users:
        users[uid] = {
            "name": name, "username": username or "없음", "money": 0, "joined": False, 
            "pickaxe": "나무", "durability": 200, "popularity": 0,
            "inventory": {m: 0 for m in minerals_config.keys()},
            "last_mine": 0
        }
        save_db()
    return users[uid]

# ==========================================
# 2. 명령어 핸들러 (인식 강화 및 가입 처리)
# ==========================================
async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    # 공백 전처리
    cmd_text = " ".join(update.message.text.split())
    if not cmd_text.startswith("."): return 
    
    parts = cmd_text.split()
    cmd = parts[0]
    uid = update.effective_user.id
    user = init_user_data(uid, update.effective_user.first_name, update.effective_user.username)

    # [가입] 0순위 처리
    if cmd == ".가입":
        if user["joined"]:
            await update.message.reply_html("<b>[ G-COIN ]</b>\n이미 가입되었습니다.")
        else:
            user["joined"] = True
            user["money"] = 100000
            save_db()
            await update.message.reply_html("<b>[ G-COIN ]</b>\n✅ <b>가입 성공!</b>\n나무 곡괭이와 100,000 G 지급!")
        return

    # 미가입자 필터
    if not user["joined"]:
        await update.message.reply_html("👋 <b>.가입</b> 명령어를 먼저 입력해주세요!")
        return

    # [내정보]
    if cmd == ".내정보":
        p = user["pickaxe"]
        fix_cost = PICKAXE_CONFIG[p]["repair_fixed"]
        msg = (f"<b>[ {user['name']} 님의 정보 ]</b>\n"
               f"💰 코인: {user['money']:,} G\n"
               f"⛏ 도구: {p} 곡괭이\n"
               f"🔧 내구: {user['durability']}/{PICKAXE_CONFIG[p]['max']}\n"
               f"🛠 수리비: {fix_cost:,}")
        kb = [[InlineKeyboardButton("공식채널", url=OFFICIAL_CHANNEL_URL)],
              [InlineKeyboardButton("📈 인기도 +1", callback_data="pop_up"), InlineKeyboardButton("📉 인기도 -1", callback_data="pop_down")]]
        await update.message.reply_html(msg, reply_markup=InlineKeyboardMarkup(kb))

    # [채광]
    elif cmd == ".채광":
        now = datetime.now().timestamp()
        if now - user.get("last_mine", 0) < 1.5: return
        
        if user["durability"] <= 0:
            await update.message.reply_html("❌ 곡괭이 파손! <b>.수리</b> 하세요.")
            return

        user["durability"] -= 1
        user["last_mine"] = now
        luck = PICKAXE_CONFIG[user["pickaxe"]]["luck"]
        roll = random.uniform(0, 100) - luck
        
        sel = "자갈"; total = 0
        for t, items, ch in mining_tiers:
            total += ch
            if roll <= total: sel = random.choice(items); break
        
        user["inventory"][sel] += 1
        save_db()
        await update.message.reply_text(f"⛏ {sel} 획득! (내구: {user['durability']})")

    # [수리]
    elif cmd == ".수리":
        p = user["pickaxe"]
        cost = PICKAXE_CONFIG[p]["repair_fixed"]
        if user["money"] >= cost:
            user["money"] -= cost; user["durability"] = PICKAXE_CONFIG[p]["max"]
            save_db(); await update.message.reply_text(f"🛠 수리 완료! (-{cost:,} G)")
        else: await update.message.reply_text(f"❌ 수리비 부족!")

    # [판매]
    elif cmd == ".판매":
        earned = sum(user["inventory"][m] * minerals_config[m] for m in minerals_config)
        if earned > 0:
            for m in user["inventory"]: user["inventory"][m] = 0
            user["money"] += earned; save_db()
            await update.message.reply_html(f"💰 판매 완료! <b>+{earned:,} G</b>")
        else: await update.message.reply_text("광물이 없습니다.")

    # [바카라]
    elif cmd in [".플", ".뱅", ".타이"]:
        try:
            amt = int(parts[1])
            if user["money"] < amt or amt <= 0: return
            user["money"] -= amt
            
            deck = BACCARAT_DECK.copy(); random.shuffle(deck)
            p_card, b_card = deck.pop(), deck.pop()
            ps, bs = p_card['score'], b_card['score']
            
            await context.bot.send_sticker(update.effective_chat.id, p_card['file_id'])
            await context.bot.send_sticker(update.effective_chat.id, b_card['file_id'])
            
            win = "player" if ps > bs else "banker" if bs > ps else "tie"
            win_map = {".플": "player", ".뱅": "banker", ".타이": "tie"}
            rates = {".플": 2, ".뱅": 1.95, ".타이": 8}
            
            if win_map[cmd] == win:
                reward = int(amt * rates[cmd]); user["money"] += reward
                await update.message.reply_html(f"✅ <b>당첨!</b> ({ps}:{bs})\n💰 +{reward:,} G")
            else:
                if ADMIN_ID in users: users[ADMIN_ID]["money"] += amt
                await update.message.reply_html(f"❌ <b>낙첨</b> ({ps}:{bs})")
            save_db()
        except: pass

    # [송금]
    elif cmd == ".송금":
        try:
            tid, amt = int(parts[1]), int(parts[2])
            if user["money"] >= amt > 0 and tid in users:
                user["money"] -= amt; users[tid]["money"] += amt
                save_db(); await update.message.reply_text(f"💸 {tid}님께 {amt:,} 송금!")
        except: pass

    # [지급] (관리자)
    elif cmd == ".지급" and uid == ADMIN_ID:
        try:
            tid, amt = int(parts[1]), int(parts[2])
            if tid in users: users[tid]["money"] += amt; save_db(); await update.message.reply_text("🎁 지급 완료!")
        except: pass

# ==========================================
# 3. 콜백 및 시스템 가동
# ==========================================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = query.from_user.id
    user = init_user_data(uid, query.from_user.first_name, query.from_user.username)
    if "pop" in query.data:
        user["popularity"] += 1 if "up" in query.data else -1
        save_db(); await query.answer(f"인기도 반영! ({user['popularity']})")

async def main():
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 8080))), BaseHTTPRequestHandler).serve_forever(), daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_commands))
    app.add_handler(CallbackQueryHandler(handle_callback))
    print("🚀 G-COIN BOT ONLINE!"); await app.initialize(); await app.updater.start_polling(); await app.start(); await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
