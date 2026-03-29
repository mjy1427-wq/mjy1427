import sqlite3
import asyncio
import random
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# --- 1. 환경 설정 및 DB 초기화 ---
TOKEN = "8771125252:AAFbKHLcDM2KhLR3MIp6ZGOnFQQWlIQUIlc"
ADMIN_ID = 7476630349

conn = sqlite3.connect('casino_mining_master.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, username TEXT, coins INTEGER DEFAULT 1000, 
                   pickaxe TEXT DEFAULT '기본 곡괭이', durability INTEGER DEFAULT 100, 
                   max_durability INTEGER DEFAULT 100, reg_date TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS inventory 
                  (user_id INTEGER, mineral TEXT, count INTEGER DEFAULT 0, PRIMARY KEY(user_id, mineral))''')
cursor.execute('''CREATE TABLE IF NOT EXISTS baccarat_history 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, result TEXT)''')
conn.commit()

# --- 2. 데이터 설정 ---
MINERAL_PRICES = {
    "네더라이트": 5000000, "다이아몬드": 3000000, "에메랄드": 2000000, "루비": 1500000,
    "사파이어": 1000000, "백금": 700000, "금": 500000, "은": 300000,
    "구리": 40000, "철": 20000, "석탄": 13000, "암석": 10000, "청동": 5000
}

PICKAXE_DATA = {
    "Wood": {"buy": 1000000, "repair": 100000, "dur": 100},
    "Stone": {"buy": 5000000, "repair": 500000, "dur": 300},
    "Iron": {"buy": 15000000, "repair": 1000000, "dur": 500},
    "Gold": {"buy": 50000000, "repair": 3000000, "dur": 1000},
    "Diamond": {"buy": 250000000, "repair": 5000000, "dur": 5000},
    "Netherite": {"buy": 1000000000, "repair": 100000000, "dur": 10000}
}

# --- 3. 유틸리티 함수 ---
def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

def get_baccarat_board():
    cursor.execute("SELECT result FROM baccarat_history ORDER BY id ASC")
    history = [row[0] for row in cursor.fetchall()]
    board = [["⬜" for _ in range(29)] for _ in range(7)]
    for i, res in enumerate(history):
        col, row = i // 7, i % 7
        if col < 29:
            board[row][col] = "🔵" if res == "P" else ("🔴" if res == "B" else "🟢")
    
    output = f"📊 **실시간 기록지 ({len(history)}/45)**\n"
    for r in board: output += "".join(r) + "\n"
    if len(history) >= 45:
        cursor.execute("DELETE FROM baccarat_history")
        conn.commit()
        output += "\n⚠️ **기록지가 45회차를 채워 다음 판에 리셋됩니다!**"
    return output

# --- 4. 메인 커맨드 핸들러 ---
async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text, user = update.message.text, update.effective_user
    u = get_user(user.id)

    if text == "!가입":
        if u: await update.message.reply_text("이미 가입된 회원입니다."); return
        cursor.execute("INSERT INTO users (user_id, username, reg_date) VALUES (?, ?, ?)", 
                       (user.id, user.username, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        await update.message.reply_text("🎊 가입 완료! 기본 곡괭이가 지급되었습니다.")
        return

    if not u: return # 미가입자 보호

    if text == "!내정보":
        await update.message.reply_text(f"👤 **닉네임**: {user.username}\n🆔 **아이디**: `{user.id}`\n💰 **G코인**: {u[2]:,}개\n📅 **가입일**: {u[6]}", parse_mode='Markdown')

    elif text == "!채광":
        if u[4] <= 0: await update.message.reply_text("💥 곡괭이가 파괴되었습니다! !곡괭이 메뉴에서 조치하세요."); return
        pick = random.choices(list(MINERAL_PRICES.keys()), weights=[1, 2, 4, 6, 8, 12, 15, 20, 40, 60, 80, 100, 150])[0]
        new_dur = u[4] - 1
        cursor.execute("INSERT INTO inventory (user_id, mineral, count) VALUES (?, ?, 1) ON CONFLICT(user_id, mineral) DO UPDATE SET count = count + 1", (user.id, pick))
        cursor.execute("UPDATE users SET durability = ? WHERE user_id = ?", (new_dur, user.id))
        conn.commit()
        msg = f"⛏ **채광 완료!**\n💎 획득: {pick} ({MINERAL_PRICES[pick]:,} G)\n📉 내구도: {new_dur}/{u[5]}"
        if new_dur <= 0:
            cursor.execute("UPDATE users SET pickaxe='기본 곡괭이', durability=100, max_durability=100 WHERE user_id=?", (user.id,))
            conn.commit()
            msg += "\n\n💥 **콰광! 곡괭이가 부서져 파괴되었습니다!**"
        await update.message.reply_text(msg)

    elif text == "!인벤":
        cursor.execute("SELECT mineral, count FROM inventory WHERE user_id = ?", (user.id,))
        inv, total = cursor.fetchall(), 0
        msg = f"🎒 **{user.username}님의 인벤토리**\n"
        for m, c in inv:
            if c > 0:
                val = MINERAL_PRICES[m] * c
                msg += f"▫️ {m} x{c}개 ({val:,} G)\n"; total += val
        await update.message.reply_text(f"{msg}─\n💰 **보유 광물 가치**: {total:,} G", parse_mode='Markdown')

    elif text == "!상점":
        keyboard = [[InlineKeyboardButton("⚒ 곡괭이 상점", callback_data="shop_p"), InlineKeyboardButton("💎 광물 일괄판매", callback_data="sell_all")]]
        await update.message.reply_text("🛒 **상점 메뉴**", reply_markup=InlineKeyboardMarkup(keyboard))

    elif text == "!곡괭이":
        keyboard = [[InlineKeyboardButton("⛏ 착용 변경", callback_data="p_change"), InlineKeyboardButton("💥 곡괭이 파괴", callback_data="p_break")], [InlineKeyboardButton("🔧 수리하기", callback_data="p_repair")]]
        await update.message.reply_text(f"⛏ **현재 곡괭이**: {u[3]}\n🔋 **내구도**: {u[4]}/{u[5]}", reply_markup=InlineKeyboardMarkup(keyboard))

    elif text == "!바카라":
        await update.message.reply_text(get_baccarat_board(), parse_mode='Markdown')

    elif any(text.startswith(x) for x in ["!플", "!뱅", "!타이"]):
        try:
            amt = int(text.split()[1])
            if u[2] < amt: await update.message.reply_text("코인이 부족합니다."); return
            b_type = "Player" if "!플" in text else ("Banker" if "!뱅" in text else "Tie")
            
            await update.message.reply_text(f"🎰 **배팅 완료!** ({b_type} {amt:,}G)\n20초 후 배팅이 마감됩니다.")
            await asyncio.sleep(20)
            msg = await update.message.reply_text("🚫 **배팅 마감!** (5초 후 결과 발표)")
            await asyncio.sleep(5)

            p1, p2, b1, b2 = [random.randint(0,9) for _ in range(4)]
            await msg.edit_text(f"🎴 **P 카드 오픈**\nP: [ {p1} ] [ ? ]\nB: [ ? ] [ ? ]")
            await asyncio.sleep(3)
            await msg.edit_text(f"🎴 **B 카드 오픈**\nP: [ {p1} ] [ ? ]\nB: [ {b1} ] [ ? ]")
            await asyncio.sleep(2)

            p_tot, b_tot = (p1+p2)%10, (b1+b2)%10
            winner = "Player" if p_tot > b_tot else ("Banker" if b_tot > p_tot else "Tie")
            win_code = "P" if winner == "Player" else ("B" if winner == "Banker" else "T")
            cursor.execute("INSERT INTO baccarat_history (result) VALUES (?)", (win_code,))
            
            win_sym = "🔵" if winner == "Player" else ("🔴" if winner == "Banker" else "🟢")
            res_txt = f"{win_sym} **{winner.upper()} 승리!** {win_sym}\nP:[{p1}][{p2}]({p_tot}점) / B:[{b1}][{b2}]({b_tot}점)\n"
            
            if b_type == winner:
                rate = 2 if winner == "Player" else (1.95 if winner == "Banker" else 9)
                win_amt = int(amt * rate)
                cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (win_amt - amt, user.id))
                res_txt += f"✅ **당첨! +{win_amt:,} G**\n"
            else:
                cursor.execute("UPDATE users SET coins = coins - ? WHERE user_id = ?", (amt, user.id))
                res_txt += f"❌ **낙첨... -{amt:,} G**\n"
            
            conn.commit()
            await msg.edit_text(f"{res_txt}\n{get_baccarat_board()}", parse_mode='Markdown')
        except: await update.message.reply_text("사용법: !플 [금액]")

# --- 5. 콜백 처리 (상점/수리) ---
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    u = get_user(query.from_user.id)
    await query.answer()

    if query.data == "p_repair":
        p_info = PICKAXE_DATA.get(u[3])
        if not p_info: await query.message.reply_text("수리 불가 품목입니다."); return
        cost = int(((u[5]-u[4])/u[5]) * p_info['repair'])
        if u[2] < cost: await query.message.reply_text(f"수리비 부족! ({cost:,} G 필요)"); return
        cursor.execute("UPDATE users SET coins=coins-?, durability=? WHERE user_id=?", (cost, u[5], u[0]))
        conn.commit()
        await query.message.reply_text(f"🔧 **수리 완료!** (-{cost:,} G)")

    elif query.data == "sell_all":
        cursor.execute("SELECT mineral, count FROM inventory WHERE user_id=?", (u[0],))
        inv, total = cursor.fetchall(), 0
        for m, c in inv: total += MINERAL_PRICES.get(m, 0) * c
        if total <= 0: await query.message.reply_text("판매할 광물이 없습니다."); return
        cursor.execute("UPDATE inventory SET count=0 WHERE user_id=?", (u[0],))
        cursor.execute("UPDATE users SET coins=coins+? WHERE user_id=?", (total, u[0]))
        conn.commit()
        await query.message.reply_text(f"♻️ **일괄 판매 완료!** (+{total:,} G코인)")

# --- 6. 가동 ---
if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_commands))
    app.add_handler(CallbackQueryHandler(on_callback))
    print("🚀 바카라&광산 마스터 시스템 가동 중...")
    app.run_polling()
