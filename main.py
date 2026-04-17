import random
import json
import asyncio
import os
import time
from datetime import datetime
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ================= [0] 웹 서버 (Render 유지용) =================
app = Flask('')
@app.route('/')  # 오타 수정 완료
def home(): return "G-COIN Bot Running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web); t.daemon = True; t.start()

# ================= [1] 설정 및 데이터베이스 =================
BOT_TOKEN = "8484299407:AAEZ7D0DBsCn8_jbNr5fUyPob0Tpd9oD5TE" 
ADMIN_ID = 7476630349 
BASE_URL = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/"
DB_FILE = "casino_data.json"

db = {
    "users": {}, 
    "vault": 700000000000, 
    "history": [], 
    "game_count": 1, 
    "next_result": None,
    "active_rooms": [] 
}

mine_cooldowns = {}
room_betting_status = {}

MINERALS = {
    "1티어": {"아다만티움": 5000000, "오리하르콘": 3000000, "다이아몬드": 2000000},
    "2티어": {"미스릴": 1000000, "흑요석": 700000},
    "3티어": {"백금": 400000, "금": 250000, "티타늄": 180000},
    "4티어": {"은": 100000, "비취": 50000, "황동": 30000},
    "5티어": {"철": 25000, "구리": 15000, "석탄": 10000}
}

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                db.update(json.load(f))
        except: pass

load_db()

# ================= [2] 바카라 엔진 및 연출 =================
def get_baccarat_result():
    suits = ["h", "d", "c", "s"]
    p_cards = [{'val': random.randint(1, 13), 'suit': random.choice(suits)} for _ in range(2)]
    b_cards = [{'val': random.randint(1, 13), 'suit': random.choice(suits)} for _ in range(2)]
    
    def get_score(cards):
        return sum([c['val'] if c['val'] < 10 else 0 for c in cards]) % 10

    p_s = get_score(p_cards)
    b_s = get_score(b_cards)
    
    if p_s <= 5:
        p_cards.append({'val': random.randint(1, 13), 'suit': random.choice(suits)})
        p_s = get_score(p_cards)
    if b_s <= 5:
        b_cards.append({'val': random.randint(1, 13), 'suit': random.choice(suits)})
        b_s = get_score(b_cards)
        
    res_name = "타이" if p_s == b_s else "플레이어" if p_s > b_s else "뱅커"
    sym = "🟢" if p_s == b_s else "🔴" if p_s > b_s else "🔵"
    return {"name": res_name, "sym": sym, "p_cards": p_cards, "b_cards": b_cards, "p_score": p_s, "b_score": b_s}

if not db.get("next_result"):
    db["next_result"] = get_baccarat_result()

async def play_card_animation(context, cid, res, user_name, win_amt, is_win):
    suit_map = {"h": "hearts", "d": "diamonds", "c": "clubs", "s": "spades"}
    
    # 플레이어/뱅커 카드 순차 배분 (누락 없이 모두 출력)
    for i in range(2):
        await context.bot.send_photo(cid, f"{BASE_URL}{res['p_cards'][i]['val']}_of_{suit_map[res['p_cards'][i]['suit']]}.png", caption=f"👤 플레이어 카드 {i+1}")
        await context.bot.send_photo(cid, f"{BASE_URL}{res['b_cards'][i]['val']}_of_{suit_map[res['b_cards'][i]['suit']]}.png", caption=f"🏦 뱅커 카드 {i+1}")
        await asyncio.sleep(0.7)

    if len(res['p_cards']) > 2:
        await context.bot.send_photo(cid, f"{BASE_URL}{res['p_cards'][2]['val']}_of_{suit_map[res['p_cards'][2]['suit']]}.png", caption="👤 플레이어 추가 카드")
    if len(res['b_cards']) > 2:
        await context.bot.send_photo(cid, f"{BASE_URL}{res['b_cards'][2]['val']}_of_{suit_map[res['b_cards'][2]['suit']]}.png", caption="🏦 뱅커 추가 카드")
    
    await asyncio.sleep(1)
    banner = "player_win.png" if res['name'] == "플레이어" else "banker_win.png" if res['name'] == "뱅커" else "tie_win.png"
    result_txt = f"<b>{res['sym']} {res['name']} 승 !</b>\n(P:{res['p_score']} vs B:{res['b_score']})\n\n🏆 <b>적중자</b>\n- @{user_name} {'+' + str(f'{win_amt:,}') if is_win else '-'} G"
    await context.bot.send_photo(cid, f"{BASE_URL}{banner}", caption=result_txt, parse_mode='HTML')

# ================= [3] 메인 핸들러 =================
async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    msg, uid, cid = update.message.text, update.effective_user.id, update.effective_chat.id
    u = db["users"].get(str(uid))

    if cid not in db["active_rooms"]:
        db["active_rooms"].append(cid)
        save_db()

    # --- [관리자 명령어 체크 완료] ---
    if uid == ADMIN_ID:
        if msg == ".금고":
            return await update.message.reply_text(f"💰 <b>관리자 금고 현황</b>\n잔액: {db['vault']:,} G", parse_mode='HTML')
        if msg.startswith(".지급"):
            try:
                parts = msg.split()
                tid, amt = parts[1], int(parts[2])
                if str(tid) in db["users"]:
                    db["users"][str(tid)]["money"] += amt; db["vault"] -= amt; save_db()
                    return await update.message.reply_text(f"✅ 지급 완료: {amt:,} G")
            except: pass
        if msg == ".현황":
            return await update.message.reply_text(f"📊 <b>봇 가동 현황</b>\n방: {len(db['active_rooms'])}개 / 유저: {len(db['users'])}명", parse_mode='HTML')

    # --- [유저 명령어 체크 완료] ---
    if msg == ".명령어":
        help_txt = (
            "📜 <b>명령어 리스트</b>\n━━━━━━━━━━━━━━\n"
            "<b>.가입</b> ➖ 계정 생성 (기본 곡괭이 지급)\n"
            "<b>.내정보</b> ➖ 이름/ID/잔액 확인\n"
            "<b>.채광</b> ➖ 광물 채굴 (곡괭이 정보 표시)\n"
            "<b>.인벤</b> ➖ 보유 광물 (티어별 정렬)\n"
            "<b>.판매</b> ➖ 광물 정산\n"
            "<b>.송금 [아이디] [금액]</b> ➖ 코인 전송\n"
            "<b>.바카라</b> ➖ 그림장 확인\n"
            "<b>.플/뱅/타이 [금액]</b> ➖ 베팅 참여\n"
            "<b>.랭킹</b> ➖ 자산 순위 TOP 10\n"
            "━━━━━━━━━━━━━━"
        )
        return await update.message.reply_text(help_txt, parse_mode='HTML')

    if msg == ".가입":
        if str(uid) in db["users"]: return
        db["users"][str(uid)] = {"name": update.effective_user.first_name, "money": 100000, "inv": {}, "durability": 100, "max_durability": 100, "pickaxe_name": "Onyx"}
        save_db(); return await update.message.reply_text("✅ 가입 완료! 10만 G와 기본 곡괭이가 지급되었습니다.")

    if not u: return

    if msg == ".인벤":
        inv_txt = "🎒 <b>내 인벤토리</b>\n━━━━━━━━━━━━━━\n"
        for tier, minerals in MINERALS.items():
            inv_txt += f"<b>[{tier}]</b>\n"
            items = [f"▫️ {m}: {u['inv'].get(m, 0)}개 ({p:,} G)" for m, p in minerals.items() if u["inv"].get(m, 0) > 0]
            inv_txt += "\n".join(items) if items else "보유 중인 광물 없음"
            inv_txt += "\n━━━━━━━━━━━━━━\n"
        return await update.message.reply_text(inv_txt, parse_mode='HTML')

    # --- [바카라 비밀 정산 및 예지력 로직] ---
    if msg.startswith((".플", ".뱅", ".타이")):
        if cid in room_betting_status: return
        try:
            amt = int(msg.split()[1])
            if u["money"] < amt: return await update.message.reply_text("❌ 잔액 부족")
            
            u["money"] -= amt; save_db(); room_betting_status[cid] = True
            curr_game = db["game_count"]
            await update.message.reply_text(f"✅ <b>{curr_game}회차 베팅 완료</b>\n금액: {amt:,} G (30초 뒤 마감)")
            
            await asyncio.sleep(30)
            await update.message.reply_text(f"🚫 <b>{curr_game}회차 베팅 마감</b>")
            await asyncio.sleep(3)
            await update.message.reply_text(f"📣 <b>{curr_game}회차 베팅 결과 발표</b>")
            await asyncio.sleep(2)
            
            res = db["next_result"]
            win = (msg.startswith(".플") and res["name"]=="플레이어") or (msg.startswith(".뱅") and res["name"]=="뱅커") or (msg.startswith(".타이") and res["name"]=="타이")
            w_amt = int(amt * (8.0 if res["name"]=="타이" else 1.95 if res["name"]=="뱅커" else 2.0)) if win else 0
            
            # 비밀 정산: 낙첨 시 금고로, 당첨 시 유저에게
            if win: u["money"] += w_amt
            else: db["vault"] += amt
            
            await play_card_animation(context, cid, res, u['name'], w_amt, win)
            
            db["history"].append(res['sym']); db["game_count"] += 1
            db["next_result"] = get_baccarat_result()
            save_db(); del room_betting_status[cid]

            # [관리자 예지력] 관리자 베팅 시 1:1 메시지
            if uid == ADMIN_ID:
                try:
                    nr = db["next_result"]
                    await context.bot.send_message(ADMIN_ID, f"🤫 <b>[예지력] {db['game_count']}회차 결과</b>\n다음 판: <b>{nr['name']}</b> ({nr['sym']})")
                except: pass
        except: 
            if cid in room_betting_status: del room_betting_status[cid]

# ================= [4] 실행 =================
if __name__ == "__main__":
    keep_alive()
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), main_handler))
    app_bot.run_polling()
