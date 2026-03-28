import os
from flask import Flask
from threading import Thread
import random
import datetime
from telegram.ext import Updater, MessageHandler, Filters

# 1. Render의 포트 에러를 방지하기 위한 웹 서버 설정
app = Flask('')

@app.route('/')
def home():
    return "I am alive"

def run():
    # Render는 PORT 환경변수를 사용하므로 이를 맞춰줍니다.
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 데이터 저장용 변수 ---
money = {}
attendance = {}
ADMIN = "EJ1427" # 관리자 아이디

# --- 봇 기능 함수 ---
def message(update, context):
    if not update.message or not update.message.text:
        return
        
    text = update.message.text
    user = update.message.from_user.username

    if not user:
        update.message.reply_text("텔레그램 아이디(@username)를 설정해주세요!")
        return

    # 가입
    if text.startswith("!가입"):
        if user not in money:
            money[user] = 1000000
            update.message.reply_text(f"@{user}님 가입완료! 100만원 지급")
        else:
            update.message.reply_text("이미 가입되어 있습니다.")

    # 내정보
    elif text.startswith("!내정보"):
        coin = money.get(user, 0)
        update.message.reply_text(f"@{user}님의 보유코인: {coin}")

    # 출석
    elif text.startswith("!출석"):
        today = str(datetime.date.today())
        if attendance.get(user) != today:
            attendance[user] = today
            money[user] = money.get(user, 0) + 100000
            update.message.reply_text("출석완료! +100,000코인")
        else:
            update.message.reply_text("오늘 이미 출석하셨습니다.")

    # 송금
    elif text.startswith("!송금"):
        try:
            parts = text.split()
            target = parts[1].replace("@", "")
            amount = int(parts[2])
            
            if money.get(user, 0) < amount:
                update.message.reply_text("코인이 부족합니다.")
                return

            money[user] -= amount
            money[target] = money.get(target, 0) + amount
            update.message.reply_text(f"@{target}님에게 {amount}코인 송금 완료!")
        except:
            update.message.reply_text("사용법: !송금 @아이디 10000")

    # 관리자 지급
    elif text.startswith("!관리자지급"):
        if user != ADMIN:
            update.message.reply_text("관리자 전용 기능입니다.")
            return
        try:
            parts = text.split()
            target = parts[1].replace("@", "")
            amount = int(parts[2])
            money[target] = money.get(target, 0) + amount
            update.message.reply_text(f"관리자 권한으로 @{target}님에게 {amount}코인 지급 완료!")
        except:
            update.message.reply_text("사용법: !관리자지급 @아이디 10000")

    # 바카라 배팅
    elif text.startswith("!배팅"):
        try:
            parts = text.split()
            choice = parts[1] # 플, 뱅, 타이
            bet = int(parts[2])
            
            if money.get(user, 0) < bet:
                update.message.reply_text("코인이 부족합니다.")
                return

            p_card = random.randint(0, 9)
            b_card = random.randint(0, 9)

            if p_card > b_card: result = "플"
            elif b_card > p_card: result = "뱅"
            else: result = "타이"

            if choice == result:
                win_amt = bet * 8 if result == "타이" else bet
                money[user] += win_amt
                msg = f"✨ 승리! (+{win_amt})"
            else:
                money[user] -= bet
                msg = f"💀 패배 (-{bet})"

            update.message.reply_text(
                f"🎰 결과: [플:{p_card} vs 뱅:{b_card}]\n결과값: {result}\n{msg}\n현재잔액: {money[user]}"
            )
        except:
            update.message.reply_text("사용법: !배팅 플 10000 (플/뱅/타이)")

    # 랭킹
    elif text.startswith("!랭킹"):
        rank = sorted(money.items(), key=lambda x: x[1], reverse=True)
        text_rank = "🏆 TOP 5 랭킹\n"
        for i, (u, c) in enumerate(rank[:5]):
            text_rank += f"{i+1}위. @{u} : {c}코인\n"
        update.message.reply_text(text_rank)

# --- 실행부 ---
if __name__ == '__main__':
    # 1. 가짜 웹서버 실행 (Render 유지용)
    keep_alive()
    
    # 2. 텔레그램 봇 실행
    TOKEN = "8771125252:AAFbKHLcDM2KhLR3MIp6ZGOnFQQWlIQUIlc"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, message))

    print("봇이 시작되었습니다...")
    updater.start_polling()
    updater.idle()
