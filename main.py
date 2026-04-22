import os
import random
import sqlite3
import threading

from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ------------------ 설정 ------------------
TOKEN = "8484299407:AAERBt8Wnb5eFRmjFZ0E4ms1lL4IQK5Q2k8"
NOTICE_URL = "https://t.me/GCOIN7777"
ADMIN_ID = 7476630349
MAX_LEVEL = 999

# ------------------ Flask ------------------
app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    return "RUNNING"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host="0.0.0.0", port=port)

# ------------------ DB ------------------
conn = sqlite3.connect("game.db", check_same_thread=False)
db = conn.cursor()

db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, coin INTEGER)")
db.execute("""
CREATE TABLE IF NOT EXISTS pets (
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
name TEXT,
level INTEGER,
exp INTEGER,
rarity TEXT,
is_equipped INTEGER DEFAULT 0
)
""")
db.execute("""
CREATE TABLE IF NOT EXISTS market (
id INTEGER PRIMARY KEY AUTOINCREMENT,
seller_id INTEGER,
pet_id INTEGER,
price INTEGER
)
""")
conn.commit()

# ------------------ 유틸 ------------------
def get_user(uid):
    db.execute("SELECT * FROM users WHERE id=?", (uid,))
    u = db.fetchone()
    if not u:
        db.execute("INSERT INTO users VALUES (?,?)",(uid,100000))
        conn.commit()
        return (uid,100000)
    return u

def update_coin(uid, amount):
    db.execute("UPDATE users SET coin = coin + ? WHERE id=?", (amount, uid))
    conn.commit()

# ------------------ 영수 ------------------
RARITIES = ["C","B","A","S","SS","SSS"]

def give_pet(uid):
    rarity = random.choice(RARITIES)
    name = f"{rarity}영수{random.randint(1,999)}"
    db.execute("INSERT INTO pets (user_id,name,level,exp,rarity) VALUES (?,?,?,?,?)",
               (uid,name,1,0,rarity))
    conn.commit()

def equip_pet(uid, pid):
    db.execute("UPDATE pets SET is_equipped=0 WHERE user_id=?", (uid,))
    db.execute("UPDATE pets SET is_equipped=1 WHERE id=?", (pid,))
    conn.commit()

# ------------------ 상태 ------------------
sell_state = {}

# ------------------ 명령 ------------------
async def register(update:Update,context):
    get_user(update.effective_user.id)
    await update.message.reply_text("가입 완료 +100000코인")

async def menu(update:Update,context):
    kb=[
        ['⚔️ 사냥','🎒 가방'],
        ['🐾 영수목록','🏪 상점'],
        ['🏛️ 거래소','📖 도감'],
        ['🏆 랭킹','📢 공지']
    ]
    await update.message.reply_text("🏮 메뉴",reply_markup=ReplyKeyboardMarkup(kb,resize_keyboard=True))

# ------------------ 관리자 ------------------
async def admin(update:Update,context):
    if update.effective_user.id != ADMIN_ID:
        return

    kb=[
        [InlineKeyboardButton("💰 코인지급",callback_data="admin_coin")],
        [InlineKeyboardButton("📢 공지발송",callback_data="admin_notice")]
    ]
    await update.message.reply_text("👑 관리자모드",reply_markup=InlineKeyboardMarkup(kb))

# ------------------ 기능 ------------------
async def hunt(update:Update,context):
    uid=update.effective_user.id
    get_user(uid)
    coin=random.randint(100,500)
    update_coin(uid,coin)
    give_pet(uid)
    await update.message.reply_text(f"사냥 완료 +{coin}")

async def bag(update:Update,context):
    uid=update.effective_user.id
    db.execute("SELECT coin FROM users WHERE id=?", (uid,))
    coin=db.fetchone()[0]

    db.execute("SELECT name,level,rarity,is_equipped FROM pets WHERE user_id=?", (uid,))
    rows=db.fetchall()

    txt=f"💰 {coin}\n\n"
    for r in rows[:20]:
        mark="⚔️" if r[3] else ""
        txt+=f"{r[0]} Lv{r[1]} [{r[2]}]{mark}\n"

    await update.message.reply_text(txt)

async def pets(update:Update,context):
    uid=update.effective_user.id
    db.execute("SELECT id,name,level,is_equipped FROM pets WHERE user_id=?", (uid,))
    rows=db.fetchall()

    btn=[]
    for r in rows:
        mark="⚔️" if r[3] else ""
        btn.append([InlineKeyboardButton(f"{r[1]} Lv{r[2]} {mark}",callback_data=f"pet_{r[0]}")])

    await update.message.reply_text("영수목록",reply_markup=InlineKeyboardMarkup(btn))

async def shop(update:Update,context):
    btn=[
        [InlineKeyboardButton("무료 소환",callback_data="shop_free")]
    ]
    await update.message.reply_text("상점",reply_markup=InlineKeyboardMarkup(btn))

async def market(update:Update,context):
    db.execute("""
    SELECT m.id,p.name,p.level,m.price
    FROM market m JOIN pets p ON m.pet_id=p.id
    """)
    rows=db.fetchall()

    txt="거래소\n"
    btn=[]

    for r in rows:
        txt+=f"{r[1]} Lv{r[2]} {r[3]}\n"
        btn.append([InlineKeyboardButton("구매",callback_data=f"buy_{r[0]}")])

    await update.message.reply_text(txt,reply_markup=InlineKeyboardMarkup(btn))

async def ranking(update:Update,context):
    db.execute("SELECT id,coin FROM users ORDER BY coin DESC LIMIT 10")
    rows=db.fetchall()

    txt="🏆 랭킹\n"
    for i,r in enumerate(rows,1):
        txt+=f"{i}위 {r[1]}\n"

    await update.message.reply_text(txt)

async def notice(update:Update,context):
    btn=[[InlineKeyboardButton("공지 이동",url=NOTICE_URL)]]
    await update.message.reply_text("공지",reply_markup=InlineKeyboardMarkup(btn))

# ------------------ 콜백 ------------------
async def callback(update:Update,context):
    q=update.callback_query
    await q.answer()
    uid=q.from_user.id
    data=q.data

    if data=="shop_free":
        give_pet(uid)
        await q.edit_message_text("영수 획득")

    elif data.startswith("pet_"):
        pid=int(data.split("_")[1])
        btn=[
            [InlineKeyboardButton("장착",callback_data=f"equip_{pid}")],
            [InlineKeyboardButton("판매",callback_data=f"sell_{pid}")]
        ]
        await q.edit_message_text("선택",reply_markup=InlineKeyboardMarkup(btn))

    elif data.startswith("equip_"):
        pid=int(data.split("_")[1])
        equip_pet(uid,pid)
        await q.edit_message_text("장착 완료")

    elif data.startswith("sell_"):
        pid=int(data.split("_")[1])
        sell_state[uid]=pid
        await q.edit_message_text("가격 입력")

    elif data.startswith("buy_"):
        mid=int(data.split("_")[1])
        db.execute("SELECT seller_id,pet_id,price FROM market WHERE id=?", (mid,))
        m=db.fetchone()
        if not m: return

        seller,pid,price=m

        db.execute("SELECT coin FROM users WHERE id=?", (uid,))
        coin=db.fetchone()[0]
        if coin < price:
            await q.answer("코인 부족",show_alert=True)
            return

        update_coin(uid,-price)
        update_coin(seller,price)

        db.execute("UPDATE pets SET user_id=? WHERE id=?", (uid,pid))
        db.execute("DELETE FROM market WHERE id=?", (mid,))
        conn.commit()

        await q.edit_message_text("구매 완료")

# ------------------ 가격 입력 ------------------
async def sell_price(update:Update,context):
    uid=update.effective_user.id

    if uid not in sell_state:
        return

    try:
        price=int(update.message.text)
    except:
        return

    pid=sell_state.pop(uid)
    db.execute("INSERT INTO market (seller_id,pet_id,price) VALUES (?,?,?)",(uid,pid,price))
    conn.commit()

    await update.message.reply_text("거래소 등록 완료")

# ------------------ 실행 ------------------
def main():
    threading.Thread(target=run_flask, daemon=True).start()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.Regex("^\.가입$"), register))
    app.add_handler(MessageHandler(filters.Regex("^\.메뉴$"), menu))
    app.add_handler(MessageHandler(filters.Regex("^\.관리자모드$"), admin))

    app.add_handler(MessageHandler(filters.Regex("^⚔️ 사냥$"), hunt))
    app.add_handler(MessageHandler(filters.Regex("^🎒 가방$"), bag))
    app.add_handler(MessageHandler(filters.Regex("^🐾 영수목록$"), pets))
    app.add_handler(MessageHandler(filters.Regex("^🏪 상점$"), shop))
    app.add_handler(MessageHandler(filters.Regex("^🏛️ 거래소$"), market))
    app.add_handler(MessageHandler(filters.Regex("^🏆 랭킹$"), ranking))
    app.add_handler(MessageHandler(filters.Regex("^📢 공지$"), notice))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, sell_price))
    app.add_handler(CallbackQueryHandler(callback))

    print("RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()
