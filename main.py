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

# ================= 🌐 [0] 웹 서버 (Render 유지용) =================
app = Flask('')
@app.route('/')
def home(): return "G-COIN Bot Running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web); t.daemon = True; t.start()

# ================= 🔐 [1] 설정 및 데이터베이스 =================
BOT_TOKEN = "8484299407:AAERctChjsjN_B4ml7y5UzHMN7lEg_ujrPA" 
ADMIN_ID = 7476630349 
NOTICE_CHANNEL = "https://t.me/GCOIN7777"
CS_LINK = "https://t.me/GCOINZ_BOT" 

BASE_URL = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/"
DB_FILE = "casino_data.json"

db = {"users": {}, "vault": 500000000000, "history": [], "active_rooms": [], "game_count": 1}
mine_cooldowns = {}
pending_replies = {}
room_betting_status = {}

SHOP_ITEMS = {
    "Onyx": {"price": 1000000, "durability": 100, "repair": 200000},
    "Sapphire": {"price": 5000000, "durability": 300, "repair": 1000000},
    "Topaz": {"price": 15000000, "durability": 500, "repair": 3000000},
    "Emerald": {"price": 50000000, "durability": 1000, "repair": 10000000},
    "Ruby": {"price": 250000000, "durability": 5000, "repair": 50000000},
    "Opal": {"price": 1000000000, "durability": 10000, "repair": 200000000},
    "Diamond": {"price": 2000000000, "durability": 25000, "repair": 400000000}
}

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

# ================= 🛠 [2] 메인 핸들러 =================
async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    msg, uid, cid = update.message.text, update.effective_user.id, update.effective_chat.id
    u = db["users"].get(str(uid))

    if str(cid) not in db["active_rooms"]: db["active_rooms"].append(str(cid))

    if uid == ADMIN_ID and uid in pending_replies:
        target_id = pending_replies[uid]
        await context.bot.send_message(chat_id=target_id, text=f"📞 <b>상담 답변:</b>\n\n{msg}", parse_mode='HTML')
        await update.message.reply_text("✅ 답변 전달 완료.")
        del pending_replies[uid]
        return

    if not u and msg != ".가입":
        await update.message.reply_text("⚠️ 먼저 <code>.가입</code>을 입력하여 계정을 생성해주세요.", parse_mode='HTML')
        return

    if not msg.startswith("."):
        if uid == ADMIN_ID: return
        kb = [[InlineKeyboardButton("✉️ 답변하기", callback_data=f"reply_{uid}")]]
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"🔴 <b>문의</b>\n유저: {u['name']}\nID: <code>{uid}</code>\n내용: {msg}", reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')
        await update.message.reply_text("✅ 관리자에게 전달되었습니다.")
        return

    # --- 명령어 로직 ---
    if msg == ".가입":
        if u: return await update.message.reply_text("이미 가입된 계정입니다.")
        now = datetime.now()
        db["users"][str(uid)] = {
            "name": update.effective_user.first_name, "money": 100000, "inv": {}, "last_check": "",
            "durability": 100, "max_durability": 100, "pickaxe_name": "Onyx",
            "joined": True, "join_date": now.strftime("%Y-%m-%d"), "join_time": now.strftime("%H:%M:%S")
        }
        await update.message.reply_text("✅ <b>가입 완료!</b> 초기 자금 100,000 G 지급.", parse_mode='HTML')

    elif msg == ".채광":
        now_ts = time.time()
        last_mine = mine_cooldowns.get(str(uid), 0)
        remaining = 40 - int(now_ts - last_mine)
        if remaining > 0:
            return await update.message.reply_text(f"⏳ <b>채광 대기 중</b>\n남은 시간: {remaining}초", parse_mode='HTML')
        
        if u["durability"] <= 0: return await update.message.reply_text("❌ 내구도 부족! .수리 가 필요합니다.")
        
        p_name = u["pickaxe_name"]
        if p_name == "Diamond": weights = [15, 20, 20, 25, 20]     
        elif p_name == "Opal": weights = [11, 18, 20, 25, 26]      
        elif p_name == "Ruby": weights = [8, 15, 20, 27, 30]       
        elif p_name == "Emerald": weights = [6, 12, 20, 30, 32]    
        elif p_name == "Topaz": weights = [4, 10, 21, 30, 35]      
        elif p_name == "Sapphire": weights = [2, 7, 21, 35, 35]    
        else: weights = [1, 5, 14, 30, 50]                         

        mine_cooldowns[str(uid)] = now_ts; u["durability"] -= 1
        tier = random.choices(list(MINERALS.keys()), weights=weights)[0]
        m_name = random.choice(list(MINERALS[tier].keys())); m_price = MINERALS[tier][m_name]
        u["inv"][m_name] = u["inv"].get(m_name, 0) + 1
        await update.message.reply_text(f"⛏ <b>채광 완료!</b>\n\n💎 <b>광물이름:</b> {m_name}\n💵 <b>광물가격:</b> {m_price:,} G\n🛠 <b>착용곡괭이:</b> {p_name}\n🔋 <b>내구도:</b> {u['durability']} / {u['max_durability']}", parse_mode='HTML')

    elif msg == ".판매":
        kb = [[InlineKeyboardButton("💎 1티어", callback_data="sell_1"), InlineKeyboardButton("✨ 2티어", callback_data="sell_2")],
              [InlineKeyboardButton("📀 3티어", callback_data="sell_3"), InlineKeyboardButton("🥈 4티어", callback_data="sell_4")],
              [InlineKeyboardButton("🪵 5티어", callback_data="sell_5"), InlineKeyboardButton("💰 전체 판매", callback_data="sell_all")]]
        await update.message.reply_text("💰 <b>판매 티어를 선택하세요.</b>", reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')

    elif msg == ".인벤":
        inv_text = "🎒 <b>보유 광물 목록</b>\n\n"
        has_item = False
        for tier in MINERALS.values():
            for name, price in tier.items():
                count = u["inv"].get(name, 0)
                if count > 0:
                    inv_text += f"📦 {name} | {count}개 ({price:,}G)\n"
                    has_item = True
        await update.message.reply_text(inv_text if has_item else "가방이 비어 있습니다.", parse_mode='HTML')

    elif msg == ".상점":
        shop_text = "⚒ <b>G-COIN 장비 상점</b>\n\n"
        for n, i in SHOP_ITEMS.items():
            shop_text += f"🔹 <b>{n}</b>: {i['price']:,} G (내구도: {i['durability']})\n"
        kb = [[InlineKeyboardButton(f"{n} 구매", callback_data=f"buy_{n}")] for n in SHOP_ITEMS.keys()]
        await update.message.reply_text(shop_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')

    elif msg == ".수리":
        item = SHOP_ITEMS.get(u["pickaxe_name"])
        cost = item["repair"]
        if u["money"] < cost: return await update.message.reply_text(f"❌ 수리비 부족 ({cost:,} G 필요)")
        u["money"] -= cost; u["durability"] = u["max_durability"]
        await update.message.reply_text(f"🔧 <b>수리 완료!</b>\n정산 금액: {cost:,} G")

    elif msg == ".출석":
        today = datetime.now().strftime("%Y-%m-%d")
        if u["last_check"] == today: return await update.message.reply_text("오늘 이미 출석하셨습니다.")
        u["money"] += 50000; u["last_check"] = today
        await update.message.reply_text("✅ 출석 완료! 50,000 G 지급.")

    elif msg == ".송금":
        try:
            _, tid, amt = msg.split(); amt = int(amt)
            if u["money"] < amt or tid == str(uid): return await update.message.reply_text("❌ 불가")
            fee = int(amt * 0.08); net = amt - fee
            if tid in db["users"]:
                u["money"] -= amt; db["users"][tid]["money"] += net; db["vault"] += fee
                await update.message.reply_text(f"✅ <b>송금 완료</b>\n대상: {db['users'][tid]['name']}\n금액: {net:,} G (수수료 8% 제외)")
            else: await update.message.reply_text("❌ 유저 없음")
        except: await update.message.reply_text(".송금 아이디 금액")

    elif msg == ".내정보":
        kb = [[InlineKeyboardButton("📢 공지채널", url=NOTICE_CHANNEL), InlineKeyboardButton("💬 상담하기", url=CS_LINK)]]
        await update.message.reply_text(f"👤 <b>이름:</b> {u['name']}\n🆔 <b>아이디:</b> <code>{uid}</code>\n💰 <b>G코인:</b> {u['money']:,} G\n🛠 <b>곡괭이:</b> {u['pickaxe_name']}\n\n📅 <b>가입:</b> {u['join_date']}", reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')

    elif msg == ".바카라":
        hist = "".join([f"{h} " + ("\n" if (i+1)%10==0 else "") for i, h in enumerate(db["history"][-50:])])
        await update.message.reply_photo(photo=BASE_URL+"grid.png.JPG", caption=f"📊 <b>최근 전적</b>\n{hist}", parse_mode='HTML')

    elif msg.startswith((".플", ".뱅", ".타이")):
        if cid in room_betting_status: return 
        try:
            amt = int(msg.split()[1])
            if u["money"] < amt: return await update.message.reply_text("❌ 잔액 부족")
            room_betting_status[cid] = True
            await update.message.reply_text(f"🎲 <b>{db['game_count']}회차 베팅 시작!</b>\n30초 후 베팅이 마감됩니다.")
            
            p_score = (random.randint(1, 9) + random.randint(1, 9)) % 10
            b_score = (random.randint(1, 9) + random.randint(1, 9)) % 10
            if p_score <= 5: p_score = (p_score + random.randint(1, 9)) % 10
            if b_score <= 5: b_score = (b_score + random.randint(1, 9)) % 10
            res_name = "타이 승" if p_score == b_score else "플레이어 승" if p_score > b_score else "뱅커 승"
            sym = "🟢" if p_score == b_score else "🔴" if p_score > b_score else "🔵"

            # [핵심 수정] 관리자가 직접 베팅했을 때만 예고 전송
            if uid == ADMIN_ID:
                await context.bot.send_message(chat_id=ADMIN_ID, text=f"📢 <b>관리자 베팅 확인: 다음 회차 예고</b>\n결과: {sym} {res_name}")

            await asyncio.sleep(30)
            await update.message.reply_text("🚫 <b>베팅 마감!</b>")
            await asyncio.sleep(3)
            await update.message.reply_text(f"🎊 <b>{db['game_count']}회차 결과 발표!!</b>")
            await asyncio.sleep(2)
            
            u["money"] -= amt 
            is_win = (msg.startswith(".플") and "플레이어" in res_name) or (msg.startswith(".뱅") and "뱅커" in res_name) or (msg.startswith(".타이") and "타이" in res_name)
            res_msg = f"🃏 <b>{db['game_count']}회차 게임 결과</b>\n\n🏆 <b>결과: {sym} {res_name}</b>\n━━━━━━━━━━━━━\n"
            
            if is_win:
                rate = 8.0 if "타이" in res_name else 1.95 if "뱅커" in res_name else 2.0
                win_amt = int(amt * rate); u["money"] += win_amt; db["vault"] -= (win_amt - amt)
                res_msg += f"✅ <b>{u['name']}님 당첨!</b>\n💰 +{win_amt:,} G"
            else:
                db["vault"] += amt; res_msg += f"💀 <b>{u['name']}님 미당첨</b>\n💸 -{amt:,} G"

            await update.message.reply_photo(photo=BASE_URL+"dealer.jpg", caption=res_msg, parse_mode='HTML')
            db["history"].append(sym); db["game_count"] += 1; del room_betting_status[cid]
        except: 
            if cid in room_betting_status: del room_betting_status[cid]
            await update.message.reply_text("베팅 형식 오류")

    elif uid == ADMIN_ID:
        # [핵심 수정] .지급 [아이디] [금액] 로직
        if msg.startswith(".지급"):
            try:
                parts = msg.split()
                target_id, a = parts[1], int(parts[2])
                if target_id in db["users"]:
                    db["vault"] -= a; db["users"][target_id]["money"] += a
                    await update.message.reply_text(f"✅ <b>지급 완료</b>\n대상: {db['users'][target_id]['name']}\n금액: {a:,} G")
                else:
                    await update.message.reply_text("❌ 해당 유저를 찾을 수 없습니다.")
            except: 
                await update.message.reply_text("💡 사용법: <code>.지급 [아이디] [금액]</code>", parse_mode='HTML')
        
        elif msg == ".금고": await update.message.reply_text(f"🏦 <b>금고:</b> {db['vault']:,} G")
        elif msg == ".현황": await update.message.reply_text(f"📊 유저: {len(db['users'])}명 / 방: {len(db['active_rooms'])}개")

    elif msg == ".랭킹":
        top = sorted(db["users"].items(), key=lambda x: x[1]['money'], reverse=True)[:10]
        text = "🏆 <b>G코인 랭킹 TOP 10</b>\n\n"
        for i, (id, data) in enumerate(top, 1): text += f"{i}위. {data['name']} | {data['money']:,} G\n"
        await update.message.reply_text(text, parse_mode='HTML')

    elif msg == ".명령어":
        await update.message.reply_text("📜 .가입 .내정보 .채광 .인벤 .판매 .상점 .수리 .출석 .송금 .랭킹 .바카라 .플 .뱅 .타이", parse_mode='HTML')

    save_db()

# ================= 🖱 [3] 콜백 핸들러 =================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); u = db["users"].get(uid); data = query.data
    await query.answer()
    if data.startswith("sell_"):
        t_num = data.split("_")[1]; gain = 0
        for t_name, mins in MINERALS.items():
            if t_num == "all" or t_num in t_name:
                for m, p in mins.items():
                    c = u["inv"].get(m, 0); gain += (p * c); u["inv"][m] = 0
        if gain > 0: u["money"] += gain; await query.edit_message_text(f"✅ <b>판매 완료!</b>\n정산: {gain:,} G")
    elif data.startswith("buy_"):
        n = data.split("_")[1]; i = SHOP_ITEMS[n]
        if u["money"] >= i["price"]:
            u["money"] -= i["price"]; u["pickaxe_name"] = n; u["durability"] = i["durability"]; u["max_durability"] = i["durability"]
            await query.edit_message_text(f"✅ <b>{n}</b> 구매 완료!")
    elif data.startswith("reply_") and int(uid) == ADMIN_ID:
        pending_replies[ADMIN_ID] = int(data.split("_")[1])
        await query.message.reply_text("✍️ 답장을 입력하세요.")
    save_db()

def main():
    keep_alive()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), main_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()

if __name__ == "__main__": main()
