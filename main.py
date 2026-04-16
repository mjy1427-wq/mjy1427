import os
import json
import random
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# =========================
# 🔐 CONFIG
# =========================

TOKEN = "8484299407:AAERctChjsjN_B4ml7y5UzHMN7lEg_ujrPA"
ADMIN_ID = 7476630349

NOTICE_CHANNEL = "https://t.me/GCOIN7777"
SUPPORT_CHANNEL = "https://t.me/GCOIN777_BOT"

# =========================
# 💾 DB
# =========================

users = {}
rooms = {}

def save():
    with open("db.json", "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False)

def load():
    global users
    try:
        with open("db.json", "r", encoding="utf-8") as f:
            users = json.load(f)
    except:
        users = {}

# =========================
# 👤 USER INIT
# =========================

def init(uid, name):
    uid = str(uid)
    if uid not in users:
        users[uid] = {
            "name": name,
            "money": 100000,
            "inv": {},
            "pickaxe": {"name": "우드", "dur": 100},
            "bets": {}
        }

# =========================
# 🎰 ROOM
# =========================

def get_room(cid):
    cid = str(cid)
    if cid not in rooms:
        rooms[cid] = {
            "bets": {},
            "timer": False,
            "lock": False
        }
    return rooms[cid]

# =========================
# ⛏ MINING
# =========================

MINERALS = {
    "1티어": {"아다만티움": 5000000, "오리하르콘": 3000000, "다이아몬드": 2000000},
    "2티어": {"미스릴": 1000000, "흑요석": 700000},
    "3티어": {"백금": 400000, "금": 250000, "티타늄": 180000},
    "4티어": {"은": 100000, "비취": 50000, "황동": 30000},
    "5티어": {"철": 25000, "구리": 15000, "석탄": 10000}
}

PICKAXE = {
    "우드": (1000000, 100),
    "스톤": (5000000, 300),
    "아이언": (15000000, 500),
    "골드": (50000000, 1000),
    "다이아": (250000000, 5000),
    "아다만티움": (1000000000, 10000)
}

def mine():
    t = random.choice(list(MINERALS.keys()))
    i = random.choice(list(MINERALS[t].keys()))
    return t, i, MINERALS[t][i]

# =========================
# ⛏ 채광
# =========================

async def 채광(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    init(uid, update.effective_user.first_name)

    u = users[uid]
    pick = u["pickaxe"]

    if pick["dur"] <= 0:
        await update.message.reply_text("❌ 곡괭이 내구도 부족")
        return

    pick["dur"] -= 1

    t, i, p = mine()
    u["inv"][i] = u["inv"].get(i, 0) + 1

    save()
    await update.message.reply_text(f"⛏ {t}-{i} ({p})\n내구도: {pick['dur']}")

# =========================
# 📦 INVENTORY
# =========================

async def 인벤(update, context):
    uid = str(update.effective_user.id)
    init(uid, update.effective_user.first_name)

    inv = users[uid]["inv"]

    msg = "📦 인벤\n"
    for k, v in inv.items():
        msg += f"{k} x{v}\n"

    await update.message.reply_text(msg)

# =========================
# 💰 SELL
# =========================

async def 판매(update, context):
    uid = str(update.effective_user.id)
    init(uid, update.effective_user.first_name)

    total = 0

    for item, qty in users[uid]["inv"].items():
        for t in MINERALS:
            if item in MINERALS[t]:
                total += MINERALS[t][item] * qty

    users[uid]["inv"] = {}
    users[uid]["money"] += total

    save()
    await update.message.reply_text(f"💰 +{total}")

# =========================
# 🎰 BACCARAT
# =========================

def get_deck():
    cards = [1,2,3,4,5,6,7,8,9,0] * 4
    random.shuffle(cards)
    return cards

def score(cards):
    return sum(cards) % 10

async def bet(update, context, side):

    cid = update.effective_chat.id
    room = get_room(cid)

    uid = str(update.effective_user.id)
    init(uid, update.effective_user.first_name)

    if room["lock"]:
        await update.message.reply_text("⛔ 베팅 종료")
        return

    if not context.args:
        return

    amount = int(context.args[0])

    if users[uid]["money"] < amount:
        await update.message.reply_text("💸 돈 부족")
        return

    users[uid]["money"] -= amount

    room["bets"].setdefault(uid, {"PLAYER":0,"BANKER":0,"TIE":0})
    room["bets"][uid][side] += amount

    if not room["timer"]:
        room["timer"] = True
        context.application.create_task(start_round(cid, context))

    await update.message.reply_text(f"🎰 {side} {amount}")

async def 플(u,c): await bet(u,c,"PLAYER")
async def 뱅(u,c): await bet(u,c,"BANKER")
async def 타이(u,c): await bet(u,c,"TIE")

async def start_round(cid, context):
    room = get_room(cid)

    await asyncio.sleep(25)

    room["lock"] = True
    await context.bot.send_message(cid, "🔒 베팅 마감")

    await asyncio.sleep(2)
    await run_game(cid, context)

async def run_game(cid, context):

    room = get_room(cid)
    deck = get_deck()

    p = [deck.pop(), deck.pop()]
    b = [deck.pop(), deck.pop()]

    if score(p) > 5:
        p.append(deck.pop())
    if score(b) > 5:
        b.append(deck.pop())

    ps = score(p)
    bs = score(b)

    if ps > bs:
        result = "PLAYER"
    elif ps < bs:
        result = "BANKER"
    else:
        result = "TIE"

    msg = "\n📊 정산\n"

    for uid, b in room["bets"].items():

        win = 0

        if result == "PLAYER" and b["PLAYER"]:
            win = int(b["PLAYER"] * 2)
        elif result == "BANKER" and b["BANKER"]:
            win = int(b["BANKER"] * 1.95)
        elif result == "TIE" and b["TIE"]:
            win = int(b["TIE"] * 8)

        users[uid]["money"] += win
        msg += f"{users[uid]['name']} +{win}\n"

    room["bets"] = {}
    room["timer"] = False
    room["lock"] = False

    await context.bot.send_message(cid, f"🏆 {result}\n{msg}")

# =========================
# 🏪 SHOP
# =========================

async def 상점(update, context):

    kb = []
    for k, (p, d) in PICKAXE.items():
        kb.append([InlineKeyboardButton(f"{k} {p}", callback_data=f"pick_{k}")])

    await update.message.reply_text("⛏ 상점", reply_markup=InlineKeyboardMarkup(kb))

async def button(update, context):

    q = update.callback_query
    await q.answer()

    uid = str(q.from_user.id)
    init(uid, q.from_user.first_name)

    if q.data.startswith("pick_"):
        name = q.data.split("_")[1]
        price, dur = PICKAXE[name]

        if users[uid]["money"] < price:
            await q.edit_message_text("돈 부족")
            return

        users[uid]["money"] -= price
        users[uid]["pickaxe"] = {"name": name, "dur": dur}

        save()
        await q.edit_message_text("⛏ 장착 완료")

# =========================
# 🏆 RANK
# =========================

async def 랭킹(update, context):

    top = sorted(users.items(), key=lambda x: x[1]["money"], reverse=True)

    msg = "🏆 랭킹\n\n"
    i = 1

    for uid, u in top:
        msg += f"{i}. {u['name']} {u['money']}\n"
        i += 1
        if i > 10:
            break

    await update.message.reply_text(msg)

# =========================
# 🧠 ROUTER (.COMMAND)
# =========================

async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if not text.startswith("."):
        return

    cmd = text.split()[0][1:]
    args = text.split()[1:]
    context.args = args

    if cmd == "채광":
        await 채광(update, context)
    elif cmd == "인벤":
        await 인벤(update, context)
    elif cmd == "판매":
        await 판매(update, context)
    elif cmd == "플":
        await 플(update, context)
    elif cmd == "뱅":
        await 뱅(update, context)
    elif cmd == "타이":
        await 타이(update, context)
    elif cmd == "상점":
        await 상점(update, context)
    elif cmd == "랭킹":
        await 랭킹(update, context)
    else:
        await update.message.reply_text("❌ 없는 명령어")

# =========================
# 🚀 START
# =========================

load()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))
app.add_handler(CallbackQueryHandler(button))

print("BOT STARTED")
app.run_polling()
