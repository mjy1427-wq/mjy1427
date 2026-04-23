import random
import sqlite3
import os
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# =========================
# SERVER
# =========================
app = Flask(__name__)
@app.route("/")
def home():
    return "BONGSIN MMO ENGINE RUNNING"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

TOKEN = os.environ.get("8484299407:AAERBt8Wnb5eFRmjFZ0E4ms1lL4IQK5Q2k8")
ADMIN_ID = 7476630349
GOLD_EVENT = False

# =========================
# DB
# =========================
conn = sqlite3.connect("game.db", check_same_thread=False)
db = conn.cursor()
lock = threading.Lock()

def q(sql, args=(), fetch=False):
    with lock:
        db.execute(sql, args)
        conn.commit()
        return db.fetchall() if fetch else None

# =========================
# TABLES
# =========================
q("""CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY,
name TEXT,
coin INTEGER DEFAULT 0
)""")

q("""CREATE TABLE IF NOT EXISTS pets(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
name TEXT,
rarity TEXT,
level INTEGER DEFAULT 1,
exp INTEGER DEFAULT 0,
atk INTEGER,
crit REAL,
bonus REAL,
equipped INTEGER DEFAULT 0
)""")

q("""CREATE TABLE IF NOT EXISTS market(
id INTEGER PRIMARY KEY AUTOINCREMENT,
pet_id INTEGER,
seller_id INTEGER,
price INTEGER,
status TEXT DEFAULT 'ON'
)""")

# =========================
# FULL PET DATA (NO REDUCTION)
# =========================
PET = {
"C": ["잡귀","음령","흑혼","허무령","잔영귀","부유령","그림자귀","음산혼","낙혼귀","기척령","허상귀","미약혼","잔재령","소멸귀","흑안체","야광잔혼","검은파편","혼백조각","흐릿한령","망령기운"],
"B": ["산귀","야수령","흑풍수","독안귀","혼탁령","혈야귀","광기수","암야령","흑혼수","야림귀","혼령수","적야귀","음풍령","흑수장","사령귀","야혼수","흑야령","폭풍혼","독기령","암흑수"],
"A": ["천령수","백호수","혼원수","영겁수","청령수","흑야수라","천강령","광야수","화산령","뇌풍수","수호령","철갑수","빙혼수","암령수","황혼수","천룡수","성광령","신수령","백야수","혼천수"],
"S": ["용신","흑룡령","천마귀","태양수","빙천수","적염주작","현무강림","백월호왕","폭풍신령","뇌전귀"],
"SS": ["천마귀왕","혼돈제령","신멸수","영겁파수","흑천신","태초수호","파멸신령","지옥수","천상파괴수","무극령"],
"SSS": ["혼돈마신","천멸흑룡","태초귀황","무극신","창세귀황","영겁파괴룡","차원붕괴자","신계종결자"]
}

UR = {
"name":"종말의 용 아포피스",
"rarity":"UR",
"level":999,
"atk":999999,
"crit":999999,
"bonus":999999
}

# =========================
# EXP SYSTEM (후반 폭증)
# =========================
def need_exp(lv):
    return int(100 * (lv ** 2.2))

def add_exp(pid, exp):
    pet = q("SELECT level,exp FROM pets WHERE id=?", (pid,), True)[0]
    lv, ex = pet
    ex += exp

    while ex >= need_exp(lv) and lv < 999:
        ex -= need_exp(lv)
        lv += 1

    q("UPDATE pets SET level=?, exp=? WHERE id=?", (lv, ex, pid))

# =========================
# MENU
# =========================
def menu():
    return ReplyKeyboardMarkup([
        ['⚔️ 사냥터','🎒 인벤토리'],
        ['🐾 영수목록','👤 내정보'],
        ['🏛️ 거래소','📖 봉신도감'],
        ['📅 출석','🏆 랭킹']
    ], resize_keyboard=True)

def admin_menu():
    return ReplyKeyboardMarkup([
        ['👑 UR지급','🎁 영수지급'],
        ['💰 코인지급','📊 이벤트'],
        ['🧹 회수','📢 공지']
    ], resize_keyboard=True)

# =========================
# USER INIT
# =========================
def user(uid,name):
    q("INSERT OR IGNORE INTO users(id,name,coin) VALUES(?,?,0)", (uid,name))

# =========================
# EQUIP
# =========================
def equip(uid):
    r = q("SELECT id,name,rarity,level,atk,crit,bonus FROM pets WHERE user_id=? AND equipped=1", (uid,), True)
    return r[0] if r else None

# =========================
# DROP
# =========================
def drop(uid):
    r = random.choices(["C","B","A","S","SS","SSS"], weights=[60,25,10,4,1,0.2])[0]
    name = random.choice(PET[r])

    q("""INSERT INTO pets(user_id,name,rarity,level,atk,crit,bonus)
         VALUES(?,?,?,?,?,?,?)""",
      (uid,name,r,1,
       random.randint(20,120),
       random.uniform(0.01,0.2),
       random.uniform(0,0.5)))

# =========================
# HUNT
# =========================
async def hunt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user(uid, update.effective_user.first_name)

    coin = random.randint(5000,12000)
    pet = equip(uid)

    msg = ""
    exp_gain = 0

    if pet:
        pid,n,r,l,a,c,b = pet

        coin += a * 100
        coin = int(coin * (1 + b))

        exp_gain = {
            "C": 20,
            "B": 40,
            "A": 80,
            "S": 150,
            "SS": 300,
            "SSS": 600,
            "UR": 2000
        }.get(r, 10)

        add_exp(pid, exp_gain)

        if random.random() < c:
            coin *= 2
            msg += "💥 CRIT!\n"

        msg += f"🐾 {r} {n} Lv{l}\n📈 EXP +{exp_gain}\n"

    if GOLD_EVENT:
        coin *= 3
        msg += "🔥 EVENT\n"

    q("UPDATE users SET coin=coin+? WHERE id=?", (coin, uid))
    drop(uid)

    await update.message.reply_text(f"⚔️ 사냥 완료\n💰 {coin}\n{msg}", reply_markup=menu())

# =========================
# PET LIST
# =========================
async def pets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    rows = q("SELECT name,rarity,level,atk,exp,equipped FROM pets WHERE user_id=?", (uid,), True)

    text = "🐾 인벤토리\n\n"
    for n,r,l,a,ex,e in rows:
        mark = "⚔️" if e else ""
        text += f"{r} {n} Lv{l} EXP:{ex} {mark}\n"

    await update.message.reply_text(text, reply_markup=menu())

# =========================
# RANKING (2종)
# =========================
async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = q("""
    SELECT u.name,u.coin,p.rarity,p.level,p.name
    FROM users u
    LEFT JOIN pets p ON u.id=p.user_id AND p.equipped=1
    ORDER BY u.coin DESC LIMIT 10
    """, (), True)

    text = "🏆 랭킹 TOP10\n\n"
    i=1
    for n,c,r,l,pn in top:
        text += f"{i}. {n} 💰{c}\n🐾 {r or 'NONE'} {pn or '-'} Lv{l or 0}\n\n"
        i+=1

    await update.message.reply_text(text, reply_markup=menu())

# =========================
# MARKET (FULL MMO)
# =========================
async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = q("""
    SELECT m.id,p.name,p.rarity,p.level,m.price
    FROM market m
    JOIN pets p ON p.id=m.pet_id
    WHERE m.status='ON'
    """, (), True)

    text="🏛️ 거래소\n\n"
    kb=[]

    for mid,n,r,l,p in rows:
        text += f"[{mid}] {r} {n} Lv{l} 💰{p}\n"
        kb.append([InlineKeyboardButton(f"구매 {mid}", callback_data=f"buy_{mid}")])

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

# =========================
# EQUIP TOGGLE
# =========================
async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    qy = update.callback_query
    await qy.answer()

    pid = int(qy.data.split("_")[1])
    uid = qy.from_user.id

    now = q("SELECT equipped FROM pets WHERE id=?", (pid,), True)[0][0]

    if now:
        q("UPDATE pets SET equipped=0 WHERE id=?", (pid,))
        await qy.edit_message_text("해제")
        return

    q("UPDATE pets SET equipped=0 WHERE user_id=?", (uid,))
    q("UPDATE pets SET equipped=1 WHERE id=?", (pid,))

    await qy.edit_message_text("장착 완료")

# =========================
# MAIN
# =========================
def main():
    threading.Thread(target=run_flask, daemon=True).start()

    bot = Application.builder().token(TOKEN).build()

    bot.add_handler(MessageHandler(filters.Regex("^⚔️ 사냥터$"), hunt))
    bot.add_handler(MessageHandler(filters.Regex("^🐾 영수목록$"), pets))
    bot.add_handler(MessageHandler(filters.Regex("^🏆 랭킹$"), rank))
    bot.add_handler(MessageHandler(filters.Regex("^🏛️ 거래소$"), market))

    bot.add_handler(CallbackQueryHandler(cb, pattern="^pet_|^buy_"))

    bot.run_polling()

if __name__ == "__main__":
    main()
