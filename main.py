import os
import json
import random
import asyncio
from datetime import date

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    CommandHandler
)

# =========================
# 🔐 CONFIG
# =========================

# 봇 토큰과 관리자 ID를 설정하세요.
TOKEN = "8484299407:AAERctChjsjN_B4ml7y5UzHMN7lEg_ujrPA"
ADMIN_ID = 7476630349 # 관리자 ID

NOTICE_CHANNEL = "https://t.me/GCOIN7777"
SUPPORT_CHANNEL = "https://t.me/GCOIN777_BOT"

# =========================
# 🎴 BACCARAT DECK DATA (오류 수정 및 중복 해결 완료)
# =========================

BACCARAT_DECK = [
    # --- 0점 카드 (10, J, Q, K) ---
    {'name': 'SPADE_10', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7Exp3mWoCRUfVj-ZE5CmN3IUjgtvGQAC2SYAAvCQ8VbM3lvO79VzBTsE'},
    {'name': 'HEART_10', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7E5p3mVSE9Y_S9vS6_WAAKGhAACOv_4VpJmKq_Wz_FTOzsE'},
    {'name': 'DIAMOND_10', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7Elp3mWdvgYOMw9HgRc2Il7kbpGkGwACExsAAtRO8FahNaTDKDCFzTsE'},
    {'name': 'CLOVER_10', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7Ehp3mWd8ioZzOX1iY2u7FRMlZc4fAACMRsAAhGP8FbmO81P4gZ3DdSE'},
    {'name': 'SPADE_J', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7GJp3mXczpHSUQABLPWVYJGRB79K7GUAAs4ZAAljo_BWHVM8Q7mxKjc7BA'},
    {'name': 'HEART_J', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7FBp3mVVZ_S9vS6_WAAKGhAACOv_4VpJmKq_Wz_FTOzsE'},
    {'name': 'DIAMOND_J', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7F5p3mXP7eNL3nEmVkYmy9EnTxmKXAACPbSAAuAa8FauMWEkVitpddSE'},
    {'name': 'CLOVER_J', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7F1p3mXOHKrfuHvAoDFBdNEGk1YfPgACbBsAAgiy-Fb54wO73qUBddSE'},
    {'name': 'SPADE_Q', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7HJp3mX7k8OEWVS8Gjf4e99UVKKQMgACBRcAAr0P8Fa8o_9h2ERTKdSE'},
    {'name': 'HEART_Q', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7HFp3mX77o4V07GRhTZ7p3VjbvEFxgACmxkAAmFN8FYOgeAm8_YYfzsE'}, # 공백 제거 완료
    {'name': 'DIAMOND_Q', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7G5p3mX09qlW7oCyp-k3Z8KA1E0K3QACdxsAAtvN8FbMD0922U9hiDSE'},
    {'name': 'CLOVER_Q', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7G1p3mXzjWB4kHKsr0AfljIrFXEDHQAC9BoAAhcI-VaN6tW2wXj8yTsE'}, # 공백 제거 완료
    {'name': 'SPADE_K', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7Gpp3mXt8mcHJ_JyKQgTFnHAwdWtMwACCRoAAi-h-FazQTiuzxZmEzse'},
    {'name': 'HEART_K', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7Glp3mXsAAEdy6_qhm4sGBCZm1DLc38AAp8cAAJqqfhWcF0OQx5DFL87BA'},
    {'name': 'DIAMOND_K', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7GZp3mXKuM-jJaBuOPhPFZSFMiHaSAACax8AAjMH8FYMbgTuO1crrjsE'},
    {'name': 'CLOVER_K', 'score': 0, 'file_id': 'CAACAgUAAxkBAAEQ7GVp3mXje9-bjU0gVAXEVK_LZT_TMAACdxgAAgk48VaWvHPT0d5KfDsE'},

    # --- 1점 카드 (A) ---
    {'name': 'SPADE_A', 'score': 1, 'file_id': 'CAACAgUAAxkBAAEQ7Fhp3mW8BGcPAUjH-Xu4bsjSDHIUSgACwh4AASAz8VYhnQL59WSxmzse'},
    {'name': 'HEART_A', 'score': 1, 'file_id': 'CAACAgUAAxkBAAEQ7Fdp3mW7GOA0zTWFiMJqzdhQvuOzdgAC7RwAArhl8Faz3VKPQgKXMzse'},
    {'name': 'DIAMOND_A', 'score': 1, 'file_id': 'CAACAgUAAxkBAAEQ7FFp3mWXiDQVv4f7uMQbflbdJfLutgACzCAAAla48Vb9T8wXbzPPfjse'},
    {'name': 'CLOVER_A', 'score': 1, 'file_id': 'CAACAgUAAxkBAAEQ7FBp3mWXjbV3Q5OEMdinCJfQltMsqQACHhsAAuaM8VYvC46og1B2ajse'},

    # --- 2점 카드 ---
    {'name': 'HEART_2', 'score': 2, 'file_id': 'CAACAgUAAxkBAAEQ7App3mSRViSy9QABBrH7Hjrq5ouaZZ8AAtcaAALQMflWUcolg756dC47BA'},
    {'name': 'SPADE_2', 'score': 2, 'file_id': 'CAACAgUAAxkBAAEQ7Axp3mSaEUEgc5majSVq8OIh7ts2pwACQh4AAuxU8FYnql4-ZGGRJTsE'},
    {'name': 'CLOVER_2', 'score': 2, 'file_id': 'CAACAgUAAxkBAAEQ7AZp3mR_TSeuCgnjXc4qbGPN_M1yVgACWx4AAubz8VbWRCfXXRC59jsE'},
    {'name': 'DIAMOND_2', 'score': 2, 'file_id': 'CAACAgUAAxkBAAEQ7Ahp3mSHxRGhAYCJQWfKunVrex9XKwACJx0AAhb5-VZ5zrTMtEsdvjsE'},

    # --- 3점 카드 ---
    {'name': 'CLOVER_3', 'score': 3, 'file_id': 'CAACAgUAAxkBAAEQ7A5p3mSksYYgf8iEeXDDR8fq1KRP4QACaR8AAv5Y8VaTLVf2T489ZzsE'},
    {'name': 'DIAMOND_3', 'score': 3, 'file_id': 'CAACAgUAAxkBAAEQ7BBp3mSukxqN7O7HsmM4-5hD9GEPywACPB0AAjb28Fb2JkBj8-_NNjsE'},
    {'name': 'HEART_3', 'score': 3, 'file_id': 'CAACAgUAAxkBAAEQ7BJp3mS1yaKFOG_5CrVrxEyyZV3wAACfhwAAsgs8VZuR148a475jsE'},
    {'name': 'SPADE_3', 'score': 3, 'file_id': 'CAACAgUAAxkBAAEQ7BRp3mS-_UwQIUAYhXc_AcvUY9rfvgACrxoAAuBR8VbK9G7nf3c54TsE'},

    # --- 4점 카드 ---
    {'name': 'HEART_4', 'score': 4, 'file_id': 'CAACAgUAAxkBAAEQ7Bpp3mTSM0lu28ee05WEDvA60gj02QACcB4AAmM48VYrEVYD2RMdTzsE'},
    {'name': 'SPADE_4', 'score': 4, 'file_id': 'CAACAgUAAxkBAAEQ7Bxp3mTXgly2BFytQ15h9ry_MruqwwACjxwAAsth8FZ1KAQ0WpYDlzsE'},
    {'name': 'CLOVER_4', 'score': 4, 'file_id': 'CAACAgUAAxkBAAEQ7BZp3mTEreDBUC8SDd6zMknOuslsJQAC-x0AAk898VallRAp2VysPDsE'},
    {'name': 'DIAMOND_4', 'score': 4, 'file_id': 'CAACAgUAAxkBAAEQ7Bhp3mTLrFneb4g5FGcLDQqiiXfhKwACYx0AAhbh8VaJgN_C89Ws4jsE'},

    # --- 5점 카드 ---
    {'name': 'CLOVER_5', 'score': 5, 'file_id': 'CAACAgUAAxkBAAEQ7B5p3mTciJpNbwOUcDGtJanwooEMAACHyEAAofK8FbQIR7YFejOuDsE'},
    {'name': 'DIAMOND_5', 'score': 5, 'file_id': 'CAACAgUAAxkBAAEQ7CBp3mTk31W6hLC6UcCAv373S4akGwACVxwAAidE-FYFTRXzoYHR0jsE'},
    {'name': 'HEART_5', 'score': 5, 'file_id': 'CAACAgUAAxkBAAEQ7CJp3mTrBoeYaj9SfvexBKZAVbkZMgACNBkAAiXt8FYwis7G_aMsczsE'},
    {'name': 'SPADE_5', 'score': 5, 'file_id': 'CAACAgUAAxkBAAEQ7CRp3mT632ulFb6I-YFRwOxC5biGdgACEh4AAvYr8Vb0JSaolbjdrTsE'},

    # --- 6점 카드 ---
    {'name': 'CLOVER_6', 'score': 6, 'file_id': 'CAACAgUAAxkBAAEQ7CZp3mUCEmoK8EuD6D544yHOaLu3-wAC9hgAAq89-FaiUQuOgwiwzsE'},
    {'name': 'DIAMOND_6', 'score': 6, 'file_id': 'CAACAgUAAxkBAAEQ7Chp3mUNHWqdz7d6zLs1dzO5IJYy3QACfxwAAou88FYld8a9twT_YzsE'},
    {'name': 'HEART_6', 'score': 6, 'file_id': 'CAACAgUAAxkBAAEQ7Clp3mUOKoepG6cx3X8DQVIG9V2sLAAC5BsAAg768FbNdm1szl6UUTsE'},
    {'name': 'SPADE_6', 'score': 6, 'file_id': 'CAACAgUAAxkBAAEQ7Cxp3mUa8FIpc3RZwXbfWtXujShVRQACSRkAAqkR-FbPmW2ZIf3okDsE'}, # 중복 해결 및 새로운 ID 반영 완료

    # --- 7점 카드 ---
    {'name': 'SPADE_7', 'score': 7, 'file_id': 'CAACAgUAAxkBAAEQ7DFp3mUpnCA-GEJ8oaLYcdSneGJu3QACuhoAAjFN8FbTzoXAcmpBCTsE'},
    {'name': 'HEART_7', 'score': 7, 'file_id': 'CAACAgUAAxkBAAEQ7DBp3mUpBnm0QPY0a2CaDUGGzfqmqwACiBsAAtB0-Fb1BMJRuaIUJDSE'},
    {'name': 'CLOVER_7', 'score': 7, 'file_id': 'CAACAgUAAxkBAAEQ7C1p3mUaD__E8YaJEA2puTxbnjHnyQACth0AAjMq8Val7P12Gpjr2DsE'},
    {'name': 'DIAMOND_7', 'score': 7, 'file_id': 'CAACAgUAAxkBAAEQ7Hdp3mYSx96E3k_hPNMS_FOdDQAB0b4AAk0dAAITVfFW4T3rXlj6AAFWOWqQ'},

    # --- 8점 카드 ---
    {'name': 'SPADE_8', 'score': 8, 'file_id': 'CAACAgUAAxkBAAEQ7Dlp3mVKb8CjYmV0DNZCrujiZx5S5wACqScAAnS48FYYwX-ZCyh0iDsE'},
    {'name': 'HEART_8', 'score': 8, 'file_id': 'CAACAgUAAxkBAAEQ7Dhp3mVJ5yNHLy28B9BHT2qfgsv2rQACdB4AAnMM8VZTMSvcZqfutzsE'},
    {'name': 'DIAMOND_8', 'score': 8, 'file_id': 'CAACAgUAAxkBAAEQ7DVp3mU13uK_NKkAAUefJseY-eW03RAAAi0bAAKhoPFWLno-ReRJ4H47BA'},
    {'name': 'CLOVER_8', 'score': 8, 'file_id': 'CAACAgUAAxkBAAEQ7DRp3mU1sNsf-ebu7c80oVqgji32mgACpR8AAuNO8VaW49WvovXUZzsE'},

    # --- 9점 카드 ---
    {'name': 'SPADE_9', 'score': 9, 'file_id': 'CAACAgUAAxkBAAEQ7EVp3mWUy1KHmKxHMBmbmo738zl1GQACyhkAAmI9-FY-6RY8e3-UETsE'},
    {'name': 'HEART_9', 'score': 9, 'file_id': 'CAACAgUAAxkBAAEQ7ERp3mWT3RbXuluWyAVqNgpJ4KSunwACERoAAnvy-VaomxXwVnT5RDsE'},
    {'name': 'DIAMOND_9', 'score': 9, 'file_id': 'CAACAgUAAxkBAAEQ7EFp3mWGN5nL3ma1jSENoY1PYOLCgwACVx4AAjW7-Fa30fLUpygsgzsE'}, # 공백 제거 완료
    {'name': 'CLOVER_9', 'score': 9, 'file_id': 'CAACAgUAAxkBAAEQ7EBp3mWGYNOoFfvUelUEqB__xWN40wACQxwAAqMu8FZUMsBrOgtazjsE'},
]

# =========================
# 💾 DATABASE
# =========================

users = {}
rooms = {} # 채팅방별 게임 상태 저장

def save():
    with open("db.json","w",encoding="utf-8") as f:
        json.dump(users,f,ensure_ascii=False)

def load():
    global users
    try:
        with open("db.json","r",encoding="utf-8") as f:
            users=json.load(f)
    except FileNotFoundError:
        users={}
    except json.JSONDecodeError:
        print("db.json 파일이 손상되었습니다.")
        users={}

# =========================
# 👤 INIT USER
# =========================

def init(uid,name):
    uid=str(uid)
    if uid not in users:
        users[uid]={
            "name":name,
            "money":100000, # 초기 자본 10만 G
            "inv":{},
            "pickaxe":{"name":"우드","dur":100},
            "last_attend":None,
            "streak":0
        }

# =========================
# 🎮 HUD UI
# =========================

def hud(title, tier=None, item=None, price=None, pick=None):
    return f"""
╔════════════════════╗
║      🟡 G COIN BOT      ║
╠════════════════════╣
║ {title}
║
║ 🔷 {tier if tier else '-'} {item if item else ''}
║ 💰 가격: {price if price else '-'}
║
║ ⛏ 곡괭이: {pick['name'] if pick else '-'}
║ 🔧 내구도: {pick['dur'] if pick else '-'}
╚════════════════════╝
"""

# =========================
# ⛏ MINING SYSTEM
# =========================

# 기존 MINERALS 데이터 유지
MINERALS={
"1티어":{"아다만티움":5000000,"오리하르콘":3000000,"다이아몬드":2000000},
"2티어":{"미스릴":1000000,"흑요석":700000},
"3티어":{"백금":400000,"금":250000},
"4티어":{"은":100000,"비취":50000},
"5티어":{"철":25000,"석탄":10000}
}

def mine():
    t=random.choice(list(MINERALS.keys()))
    i=random.choice(list(MINERALS[t].keys()))
    return t,i,MINERALS[t][i]

# =========================
# ⛏ 명령어 처리: .채광
# =========================

async def 채광(update:Update, context: ContextTypes.DEFAULT_TYPE):
    uid=str(update.effective_user.id)
    init(uid,update.effective_user.first_name)

    u=users[uid]
    pick=u["pickaxe"]

    if pick["dur"]<=0:
        return await update.message.reply_text("❌ 곡괭이 내구도가 부족하여 채광할 수 없습니다. 새 곡괭이를 구매하세요.")

    pick["dur"]-=1 # 내구도 감소

    t,i,p=mine()
    u["inv"][i]=u["inv"].get(i,0)+1 # 인벤토리에 추가

    save() # 변경사항 저장

    await update.message.reply_text(hud("⛏ 광물을 획득했습니다!",t,i,p,pick))

# =========================
# 📦 명령어 처리: .인벤
# =========================

async def 인벤(update:Update, context: ContextTypes.DEFAULT_TYPE):
    uid=str(update.effective_user.id)
    init(uid,update.effective_user.first_name)

    inv=users[uid]["inv"]
    msg=f"📦 {users[uid]['name']}님의 인벤토리\n\n💰 보유 G: {users[uid]['money']}\n\n"

    if not inv:
        msg+="(비어 있음)"
    else:
        for k,v in inv.items():
            msg+=f"{k} x{v}\n"

    await update.message.reply_text(msg)

# =========================
# 💰 명령어 처리: .판매
# =========================

async def 판매(update:Update, context: ContextTypes.DEFAULT_TYPE):
    uid=str(update.effective_user.id)
    init(uid,update.effective_user.first_name)

    total=0

    # 인벤토리의 모든 광물 가격 계산
    for item,qty in list(users[uid]["inv"].items()):
        for t in MINERALS:
            if item in MINERALS[t]:
                total+=MINERALS[t][item]*qty
                del users[uid]["inv"][item] # 인벤토리에서 제거

    users[uid]["money"]+=total
    save()

    await update.message.reply_text(f"💰 인벤토리의 모든 광물을 판매하여 **+{total} G**를 획득했습니다!")

# =========================
# 🎁 명령어 처리: .출석
# =========================

async def 출석(update:Update, context: ContextTypes.DEFAULT_TYPE):
    uid=str(update.effective_user.id)
    init(uid,update.effective_user.first_name)

    u=users[uid]
    today=str(date.today())

    if u["last_attend"]==today:
        return await update.message.reply_text("❌ 오늘은 이미 출석체크를 하셨습니다.")

    # 연속 출석 보너스
    u["streak"]+=1
    reward=50000+(u["streak"]*10000)

    u["money"]+=reward
    u["last_attend"]=today

    save()

    await update.message.reply_text(f"🎁 출석 완료! **+{reward} G** 지급\n(연속 {u['streak']}일차)")

# =========================
# 💸 명령어 처리: .송금
# =========================

async def 송금(update:Update, context: ContextTypes.DEFAULT_TYPE):
    uid=str(update.effective_user.id)
    init(uid,update.effective_user.first_name)

    try:
        # 송금 방식 1: .송금 ID 금액
        if not update.message.reply_to_message:
            target=context.args[0]
            amount=int(context.args[1])
        # 송금 방식 2: (답장으로) .송금 금액
        else:
            target=str(update.message.reply_to_message.from_user.id)
            amount=int(context.args[0])
    except:
        return await update.message.reply_text("💡 사용법: `.송금 [상대ID] [금액]` 또는 송금할 유저의 메시지에 `.송금 [금액]`으로 답장")

    if amount <= 0:
        return await update.message.reply_text("❌ 오류: 1 G 이상만 송금 가능합니다.")

    if uid == target:
        return await update.message.reply_text("❌ 자신에게는 송금할 수 없습니다.")

    fee=int(amount*0.08) # 수수료 8%
    total=amount+fee

    if users[uid]["money"]<total:
        return await update.message.reply_text(f"❌ 돈이 부족합니다.\n(필요: {total} G, 보유: {users[uid]['money']} G)")

    # 상대방 데이터 초기화
    init(target,"user")

    users[uid]["money"]-=total
    users[target]["money"]+=amount

    save()

    await update.message.reply_text(f"✅ 송금 완료!\n상대방에게: {amount} G\n수수료(8%): {fee} G\n총 차감: {total} G")

# =========================
# 🏆 ADMIN
# =========================

async def 관리자(update:Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID:
        return

    total_money=sum(u["money"] for u in users.values())
    total_users = len(users)

    await update.message.reply_text(f"👑 관리자 통계\n\n👤 총 유저: {total_users}명\n💰 총 발행 G: {total_money}")

async def 지급(update:Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID:
        return

    try:
        if update.message.reply_to_message:
            target=str(update.message.reply_to_message.from_user.id)
            amount=int(context.args[0])
        else:
            target=context.args[0]
            amount=int(context.args[1])
    except:
        return await update.message.reply_text("💡 사용법: `.지급 [ID] [금액]`")

    init(target,"user")
    users[target]["money"]+=amount

    save()

    await update.message.reply_text(f"👑 지급 완료!\nID {target}에게 {amount} G 지급")

# =========================
# 📊 명령어 처리: .랭킹
# =========================

async def 랭킹(update:Update, context: ContextTypes.DEFAULT_TYPE):
    top=sorted(users.items(),key=lambda x:x[1]["money"],reverse=True)

    msg="🏆 G COIN 코인 부자 랭킹 TOP 10\n\n"
    for i,(uid,u) in enumerate(top[:10],1):
        msg+=f"{i}위. {u['name']} {u['money']} G\n"

    await update.message.reply_text(msg)

# =========================
# 🎰 BACCARAT ENGINE V3.1 (로직 수정 및 통합)
# =========================

# 로직 함수: 바카라 점수 계산 (합의 일의 자리)
def score(cards):
    return sum(c["score"] for c in cards) % 10

# 로직 함수: 내추럴(처음 두 장 합이 8 또는 9) 확인
def is_natural(cards):
    return score(cards) in [8,9]

# 로직 함수: 뱅커 3번째 카드 드로우 규칙 (★★★중요: 수정됨★★★)
# b: 뱅커 현재 점수, p: 플레이어 3번째 카드 점수(없으면 None)
def banker_draw(b,p):
    if p is None: # 플레이어가 3번째 카드를 안 받은 경우
        return b<=5 # 뱅커 5점 이하면 무조건 받음
        
    # 플레이어가 3번째 카드를 받은 경우의 규칙
    if b<=2: return True
    if b==3: return p!=8 # 플레이어 3번째 카드가 8이 아니면 받음
    if b==4: return 2<=p<=7 # 플레이어 3번째 카드가 2~7이면 받음
    if b==5: return 4<=p<=7 # 플레이어 3번째 카드가 4~7이면 받음
    if b==6: return 6<=p<=7 # 플레이어 3번째 카드가 6 또는 7이면 받음
    return False # 뱅커 7점 이상은 스탠드

# 로직 함수: 새 덱 가져오기
def get_deck():
    return BACCARAT_DECK.copy()

# 비동기 함수: 카드 한 장 전송 (file_id 사용)
async def send_card(context, cid, card, label=""):
    await context.bot.send_photo(cid, card["file_id"], caption=f"{label}: {card['name']}")
    await asyncio.sleep(1.0) # 1초 대기 (애니메이션 효과)

# =========================
# 🎰 명령어 처리: .바카라 (베팅 및 게임 실행)
# =========================

async def 바카라(update:Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    uid=str(update.effective_user.id)
    init(uid,update.effective_user.first_name)

    # 방 상태 초기화
    if cid not in rooms:
        rooms[cid] = {"active": False, "timer": False, "bets": {}}
    
    room = rooms[cid]

    # 게임 진행 중 베팅 불가
    if room["active"]:
        return await update.message.reply_text("❌ 게임이 진행 중입니다. 다음 라운드를 기다려주세요.")

    # 베팅 중이 아닐 때 베팅 받기 시작
    if not room["timer"]:
        room["bets"] = {}
        room["timer"] = True
        await update.message.reply_text("🎰 20초간 바카라 베팅을 받습니다! 플레이어/뱅커/타이 금액으로 베팅하세요.")
        context.job_queue.run_once(start_baccarat_game, 20, chat_id=cid)

    # 베팅 입력 처리 (예: .바카라 플레이어 10000)
    try:
        bet_target = context.args[0]
        bet_amount = int(context.args[1])
    except:
        return await update.message.reply_text("💡 사용법: `.바카라 [플레이어/뱅커/타이] [금액]`")

    # 대상 및 금액 유효성 검사
    if bet_target not in ["플레이어", "뱅커", "타이"]:
        return await update.message.reply_text("❌ 베팅 대상은 `플레이어`, `뱅커`, `타이` 중 하나여야 합니다.")
    
    if bet_amount <= 0:
        return await update.message.reply_text("❌ 베팅 금액은 0보다 커야 합니다.")

    # 돈 확인
    if users[uid]["money"] < bet_amount:
        return await update.message.reply_text("❌ 돈이 부족하여 베팅할 수 없습니다.")

    # 베팅 성공 처리
    users[uid]["money"] -= bet_amount
    save()
    
    room["bets"][uid] = {"target": bet_target, "amount": bet_amount}
    
    await update.message.reply_text(f"✅ {bet_target}에 {bet_amount} G 베팅 완료! (총 {len(room['bets'])}명 베팅)")

# =========================
# 🎰 실제 게임 실행 및 결과 처리
# =========================

async def start_baccarat_game(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    cid = job.chat_id
    room = rooms[cid]
    
    if not room["bets"]: # 베팅이 없으면 취소
        room["timer"] = False
        return await context.bot.send_message(cid, "🎰 베팅이 없어 게임을 취소합니다.")

    room["timer"] = False
    room["active"] = True # 게임 시작, 추가 베팅 차단
    await context.bot.send_message(cid, "🎰 베팅 종료! 바카라 게임을 시작합니다.")

    # 카드 덱 준비 및 셔플
    deck=get_deck()
    random.shuffle(deck)

    # 초기 카드 지급
    player=[deck.pop(),deck.pop()]
    banker=[deck.pop(),deck.pop()]

    # 플레이어 카드 전송
    for c in player:
        await send_card(context, cid, c, "👤플레이어")

    # 뱅커 카드 전송
    for c in banker:
        await send_card(context, cid, c, "🏦뱅커")

    # 1. 내추럴 확인
    if is_natural(player) or is_natural(banker):
        await context.bot.send_message(cid, "✨ 내추럴!")
        # 결과 처리 로직 실행
        return await baccarat_finish(cid, context, player, banker)

    # 2. 플레이어 3번째 카드 드로우 (플레이어 점수 0~5)
    p3=None
    if score(player)<=5:
        p3=deck.pop()
        player.append(p3)
        await send_card(context,cid, p3, "👤플레이어 HIT")

    # 3. 뱅커 3번째 카드 드로우 (★★★드로우 규칙 수정됨★★★)
    # p3_score = 플레이어 3번째 카드 점수, b_score = 뱅커 현재 점수
    if banker_draw(score(banker), p3["score"] if p3 else None):
        b3=deck.pop()
        banker.append(b3)
        await send_card(context,cid, b3, "🏦뱅커 HIT")

    # 최종 점수 계산 및 결과 처리
    await baccarat_finish(cid, context, player, banker)

async def baccarat_finish(cid, context, player, banker):
    room=rooms[cid]
    
    p_final = score(player)
    b_final = score(banker)
    
    # 승패 판정
    if p_final > b_final: result="플레이어"
    elif b_final > p_final: result="뱅커"
    else: result="타이"

    res_msg=f"🏆 게임 결과: **{result} 승리!**\n플레이어 {p_final} vs 뱅커 {b_final}\n\n"

    # 배당금 지급 로직
    for uid,bet_info in room["bets"].items():
        win_money = 0
        target = bet_info["target"]
        amount = bet_info["amount"]

        if result=="플레이어" and target=="플레이어":
            win_money=amount*2
        elif result=="뱅커" and target=="뱅커":
            win_money=int(amount*1.95)
        elif result=="타이" and target=="타이":
            win_money=amount*8

        if win_money > 0:
            users[uid]["money"]+=win_money
            res_msg+=f"✅ {users[uid]['name']} +{win_money} G\n"
        else:
            res_msg+=f"❌ {users[uid]['name']} -{amount} G\n"

    # 게임 상태 초기화
    room["bets"]={}
    room["active"]=False

    save() # 데이터 저장

    await context.bot.send_message(cid, res_msg)

# =========================
# 🧠 ROUTER (.COMMAND)
# =========================

async def router(update:Update, context: ContextTypes.DEFAULT_TYPE):
    # 텍스트 메시지가 아니거나 봇 자신의 메시지면 무시
    if not update.message or not update.message.text:
        return

    text=update.message.text
    # 마침표(.)로 시작하는 명령어만 처리
    if not text.startswith("."):
        return

    # 명령어와 인자 분리
    cmd=text.split()[0][1:]
    context.args=text.split()[1:]

    # 명령어 매핑 테이블
    cmds={
        "채광":채광,
        "인벤":인벤,
        "판매":판매,
        "출석":출석,
        "송금":송금,
        "랭킹":랭킹,
        "관리자":관리자,
        "지급":지급,
        "바카라":바카라, # 바카라 명령어 추가
    }

    # 명령어가 존재하면 실행
    if cmd in cmds:
        await cmds[cmd](update,context)
    # 없는 명령어면 에러 메시지 (선택 사항)
    # else:
    #     await update.message.reply_text("❌ 존재하지 않는 명령어입니다.")

# =========================
# 🚀 RUN
# =========================

load() # 봇 시작 시 데이터 로드

# 봇 애플리케이션 생성
app=ApplicationBuilder().token(TOKEN).build()

# 메시지 핸들러 등록
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))

print("⚡ G COIN BOT STARTED")
# 봇 실행 (폴링 방식)
app.run_polling()
