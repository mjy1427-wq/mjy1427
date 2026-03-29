import random
import time
import json
import re
from telegram.ext import Updater, MessageHandler, Filters
from flask import Flask
from threading import Thread

TOKEN = "여기에_봇토큰"
ADMIN_ID = "EJ1427"
DATA_FILE = "data.json"

# 바카라 카드
DECK_ORIGIN = []
for suit in ["S","H","D","C"]:
    for rank,value in zip(
        ["A","2","3","4","5","6","7","8","9","10","J","Q","K"],
        [1,2,3,4,5,6,7,8,9,0,0,0,0]
    ):
        DECK_ORIGIN.append({"rank":rank,"value":value})

# 광물
ORES = {
    "stone":{"n":"돌","p":1000,"e":"🪨"},
    "iron":{"n":"철","p":3000,"e":"⛓"},
    "gold":{"n":"금","p":8000,"e":"🥇"},
    "dia":{"n":"다이아","p":20000,"e":"💎"}
}

user_data = {}
banned_users = set()
baccarat_history = []
current_round = 0

# =====================
# 데이터 저장
# =====================
def save_data():
    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump({
            "users":user_data,
            "banned":list(banned_users),
            "history":baccarat_history,
            "round":current_round
        },f)

def load_data():
    global user_data,banned_users,baccarat_history,current_round
    try:
        with open(DATA_FILE,"r",encoding="utf-8") as f:
            data=json.load(f)
            user_data=data.get("users",{})
            banned_users=set(data.get("banned",[]))
            baccarat_history=data.get("history",[])
            current_round=data.get("round",0)
    except:
        pass

# =====================
# 카드 뽑기
# =====================
def draw_card(deck):
    c=random.choice(deck)
    deck.remove(c)
    return c,deck

# =====================
# 메시지 처리
# =====================
def handle_message(update, context):
    global current_round,baccarat_history

    if not update.message or not update.message.text:
        return

    uid = update.message.from_user.username
    if not uid:
        return

    text = update.message.text.strip()

    # 차단 유저
    if uid in banned_users:
        return

    # =====================
    # 관리자 명령어
    # =====================
    if uid == ADMIN_ID:
        if text.startswith("!지급"):
            try:
                _,target,amount=text.split()
                amount=int(amount)
                if target not in user_data:
                    return update.message.reply_text("유저 없음")
                user_data[target]['money']+=amount
                save_data()
                return update.message.reply_text("지급 완료")
            except:
                return update.message.reply_text("!지급 아이디 금액")

        elif text.startswith("!차단"):
            try:
                _,target=text.split()
                banned_users.add(target)
                save_data()
                return update.message.reply_text("차단 완료")
            except:
                return update.message.reply_text("!차단 아이디")

    # =====================
    # 가입
    # =====================
    if text == "!가입":
        if uid in user_data:
            return update.message.reply_text("이미 가입됨")

        user_data[uid] = {
            'money':100000,
            'pick':'Wood',
            'dur':100,
            'max_dur':100,
            'inv':{k:0 for k in ORES},
            'last_mine':0,
            'last_attend':0,
            'attend_streak':0
        }
        save_data()
        return update.message.reply_text("가입 완료 100,000G 지급")

    # 가입 안 했으면 막기
    if uid not in user_data:
        return update.message.reply_text("!가입 먼저 하세요")

    user = user_data[uid]

    # =====================
    # 바카라
    # =====================
    bet_match = re.match(r"^!(플|뱅|타이)\s*([0-9,]+)", text)
    if bet_match:
        cmd = bet_match.group(1)
        amt = int(bet_match.group(2).replace(",",""))

        if amt > user['money']:
            return update.message.reply_text("잔액 부족")

        bet_type = "P" if cmd=="플" else ("B" if cmd=="뱅" else "T")

        current_round += 1
        deck = list(DECK_ORIGIN)

        p1,deck = draw_card(deck)
        p2,deck = draw_card(deck)
        b1,deck = draw_card(deck)
        b2,deck = draw_card(deck)

        pv = (p1['value'] + p2['value']) % 10
        bv = (b1['value'] + b2['value']) % 10

        result = "P" if pv>bv else ("B" if bv>pv else "T")

        user['money'] -= amt

        if bet_type == result:
            rate = 2 if result=="P" else (1.85 if result=="B" else 6)
            win = int(amt * rate)
            user['money'] += win
            msg = f"승리 +{win}"
        else:
            msg = f"패배 -{amt}"

        baccarat_history.append(result)
        if len(baccarat_history) > 20:
            baccarat_history.pop(0)

        save_data()
        return update.message.reply_text(f"{pv} vs {bv}\n{msg}")

    # =====================
    # 채광
    # =====================
    if text == "!채광":
        now=time.time()
        if now-user['last_mine']<40:
            return update.message.reply_text("채광 대기중")
        user['last_mine']=now

        ore=random.choice(list(ORES.keys()))
        user['inv'][ore]+=1
        user['dur']-=1

        save_data()
        return update.message.reply_text(f"{ORES[ore]['n']} 획득")

    # =====================
    # 인벤
    # =====================
    if text == "!인벤":
        msg="인벤토리\n"
        empty=True
        for k,v in ORES.items():
            if user['inv'][k]>0:
                msg += f"{v['e']} {v['n']} {user['inv'][k]}개\n"
                empty=False
        if empty:
            msg="인벤토리 비어있음"
        return update.message.reply_text(msg)

    # =====================
    # 판매
    # =====================
    if text == "!판매":
        total=0
        for k,v in ORES.items():
            qty=user['inv'][k]
            if qty>0:
                total += qty*v['p']
                user['inv'][k]=0
        if total==0:
            return update.message.reply_text("판매할 광물 없음")
        user['money']+=total
        save_data()
        return update.message.reply_text(f"{total}G 획득")

    # =====================
    # 출석
    # =====================
    if text == "!출석":
        now=time.time()
        last=user.get('last_attend',0)
        streak=user.get('attend_streak',0)

        if now-last < 86400:
            return update.message.reply_text("이미 출석함")

        if now-last > 172800:
            streak=0

        streak+=1
        user['attend_streak']=streak
        user['last_attend']=now

        if streak==1: reward=50000
        elif streak==2: reward=60000
        elif streak==3: reward=70000
        elif streak==4: reward=80000
        elif streak==5: reward=100000
        else: reward=120000

        user['money']+=reward
        save_data()

        return update.message.reply_text(f"출석 {streak}일차 +{reward}")

    # =====================
    # 랭킹
    # =====================
    if text == "!랭킹":
        rank=sorted(user_data.items(), key=lambda x:x[1]['money'], reverse=True)
        msg="랭킹\n"
        for i,(name,data) in enumerate(rank,1):
            msg += f"{i}. {name} {data['money']}\n"
        return update.message.reply_text(msg)

    # =====================
    # 바카라 기록
    # =====================
    if text == "!바카라":
        return update.message.reply_text(str(baccarat_history))

# =====================
# 서버 유지
# =====================
app = Flask('')
@app.route('/')
def home():
    return "bot running"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# =====================
# 실행
# =====================
if __name__ == '__main__':
    load_data()
    keep_alive()
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    updater.start_polling()
    updater.idle()
