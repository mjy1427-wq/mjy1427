import random, json, asyncio
from datetime import date
from PIL import Image, ImageDraw

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler

# =========================
# 🔐 설정
# =========================
TOKEN = "YOUR_TOKEN"
ADMIN_ID = 7476630349

# =========================
# 🏦 금고 (500억)
# =========================
bank = {"vault": 50_000_000_000}

# =========================
# 💾 DB
# =========================
users = {}
rooms = {}

def load():
    global users, rooms, bank
    try:
        with open("db.json","r",encoding="utf-8") as f:
            d=json.load(f)
            users=d.get("users",{})
            rooms=d.get("rooms",{})
            bank=d.get("bank",bank)
    except:
        pass

def save():
    with open("db.json","w",encoding="utf-8") as f:
        json.dump({"users":users,"rooms":rooms,"bank":bank},f,ensure_ascii=False)

# =========================
# 👤 유저
# =========================
def init(uid,name):
    uid=str(uid)
    if uid not in users:
        users[uid]={
            "name":name,
            "money":100000,
            "inv":{},
            "pickaxe":{"name":"Wood","dur":100,"max":100},
            "join_date":None
        }

# =========================
# 💎 광물 13종 + 레전드
# =========================
MINERALS = {
    "1티어":{"운석":5000000,"흑철":3000000,"아다만티움":1500000},
    "2티어":{"오리하르콘":900000,"미스릴":700000,"드래곤스톤":500000},
    "3티어":{"금":250000,"플래티넘":180000,"루비광석":120000},
    "4티어":{"은":80000,"수정석":50000},
    "5티어":{"철":25000,"구리":10000},
    "LEGEND":{"맹구의 희귀 컬렉션":100000000}
}

def mine():

    # 💎 레전드 0.01%
    if random.random() < 0.0001:
        return "LEGEND","맹구의 희귀 컬렉션",MINERALS["LEGEND"]["맹구의 희귀 컬렉션"]

    tiers=[("1티어",3),("2티어",8),("3티어",15),("4티어",30),("5티어",44)]

    t=random.choices([x[0] for x in tiers],[x[1] for x in tiers])[0]
    i=random.choice(list(MINERALS[t].keys()))
    return t,i,MINERALS[t][i]

# =========================
# ⛏ 채광
# =========================
async def 채광(update,context):

    uid=str(update.effective_user.id)
    init(uid,update.effective_user.first_name)

    p=users[uid]["pickaxe"]

    if p["dur"]<=0:
        return await update.message.reply_text("내구도 부족")

    p["dur"]-=1

    t,i,v = mine()

    users[uid]["inv"][i]=users[uid]["inv"].get(i,0)+1

    save()

    # 🔥 레전드 서버 공지
    if t=="LEGEND":
        msg=f"🔥 레전드 획득!\n{users[uid]['name']}\n💎 {i}\n💰 {v:,}"

        for cid in rooms.keys():
            try:
                await context.bot.send_message(cid,msg)
            except:
                pass

    await update.message.reply_text(f"⛏ {t}-{i} ({v:,})")

# =========================
# 🎰 바카라
# =========================
def value(c):
    n=int(c[1:])
    return 0 if n>=10 else n

def score(cards):
    return sum(value(c) for c in cards)%10

def baccarat(deck):
    p=[deck.pop(),deck.pop()]
    b=[deck.pop(),deck.pop()]

    ps,bs=score(p),score(b)

    if ps>=8 or bs>=8:
        return p,b

    p3=None

    if ps<=5:
        p3=deck.pop()
        p.append(p3)

    bs=score(b)

    if p3 is None:
        if bs<=5:
            b.append(deck.pop())
    else:
        pt=value(p3)
        if bs<=2 or (bs==3 and pt!=8) or (bs==4 and pt in [2,3,4,5,6,7]) \
        or (bs==5 and pt in [4,5,6,7]) or (bs==6 and pt in [6,7]):
            b.append(deck.pop())

    return p,b

def render(history):
    img=Image.new("RGB",(600,300),(20,20,20))
    d=ImageDraw.Draw(img)

    history=history[-50:]

    for i in range(50):
        x=(i%10)*60
        y=(i//10)*60

        if i<len(history):
            c=history[i]
            color=(255,50,50) if c=="플" else (50,100,255) if c=="뱅" else (50,200,100)
        else:
            color=(80,80,80)

        d.ellipse([x+5,y+5,x+55,y+55],fill=color)

    img.save("grid.png")
    return "grid.png"

# =========================
# 🏦 정산 (금고 시스템)
# =========================
async def play(cid,context):

    if cid not in rooms:
        rooms[cid]={"bets":{},"history":[],"running":False}

    deck=[f"{s}{r}" for s in "SHDC" for r in range(1,14)]
    random.shuffle(deck)

    p,b=baccarat(deck)

    ps,bs=score(p),score(b)

    result="타이"
    if ps>bs: result="플"
    elif bs>ps: result="뱅"

    room=rooms[cid]

    for uid,bet in room["bets"].items():

        if bet["type"]==result:
            payout=int(bet["amount"]*1.95)

            if bank["vault"]>=payout:
                bank["vault"]-=payout
                users[uid]["money"]+=payout
            else:
                users[uid]["money"]+=bank["vault"]
                bank["vault"]=0

        else:
            bank["vault"]+=bet["amount"]

    room["history"].append(result)

    save()

    await context.bot.send_message(cid,f"🎰 결과: {result}")
    await context.bot.send_photo(cid,open(render(room["history"]),"rb"))

    room["bets"]={}

# =========================
# ⏱ 베팅 시작
# =========================
async def round_start(cid,context):

    if cid not in rooms:
        rooms[cid]={"bets":{},"history":[],"running":False}

    if rooms[cid]["running"]:
        return

    rooms[cid]["running"]=True

    await context.bot.send_message(cid,"⏳ 베팅 30초")
    await asyncio.sleep(30)

    await play(cid,context)

    rooms[cid]["running"]=False

# =========================
# 🎲 베팅
# =========================
async def bet(update,context,typ):

    uid=str(update.effective_user.id)
    cid=str(update.effective_chat.id)

    init(uid,update.effective_user.first_name)

    amount=int(context.args[0])

    if users[uid]["money"]<amount:
        return await update.message.reply_text("잔액 부족")

    users[uid]["money"]-=amount

    if cid not in rooms:
        rooms[cid]={"bets":{},"history":[],"running":False}

    rooms[cid]["bets"][uid]={"type":typ,"amount":amount}

    await update.message.reply_text(f"{typ} {amount}")

    if not rooms[cid]["running"]:
        asyncio.create_task(round_start(cid,context))

# =========================
# 🚀 실행
# =========================
load()

app=ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("채광",채광))
app.add_handler(CommandHandler("플",lambda u,c: bet(u,c,"플")))
app.add_handler(CommandHandler("뱅",lambda u,c: bet(u,c,"뱅")))
app.add_handler(CommandHandler("타이",lambda u,c: bet(u,c,"타이")))

print("🔥 카지노 V4 FINAL RUN")
app.run_polling()
