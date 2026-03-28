import os
from flask import Flask
from threading import Thread

# Render의 포트 에러를 방지하기 위한 가짜 서버
app = Flask('')
@app.route('/')
def home():
    return "I am alive"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# 이 아래에 기존 봇 코드를 넣으세요
# 예: keep_alive() 
# bot.polling()

import random
import datetime
from telegram.ext import Updater, MessageHandler, Filters

TOKEN ="8771125252:AAFbKHLcDM2KhLR3MIp6ZGOnFQQWlIQUIlc"
ADMIN = "EJ1427"

money = {}
attendance = {}

def message(update, context):
    text = update.message.text
    user = update.message.from_user.username

    # 가입
    if text.startswith("!가입"):
        if user not in money:
            money[user] = 1000000
            update.message.reply_text("가입완료! 100만원 지급")
        else:
            update.message.reply_text("이미 가입됨")

    # 내정보 (코인확인)
    elif text.startswith("!내정보"):
        coin = money.get(user, 0)
        update.message.reply_text(f"보유코인: {coin}")

    # 출석
    elif text.startswith("!출석"):
        today = str(datetime.date.today())
        if attendance.get(user) != today:
            attendance[user] = today
            money[user] = money.get(user, 0) + 100000
            update.message.reply_text("출석완료 +100000")
        else:
            update.message.reply_text("오늘 이미 출석함")

    # 송금
    elif text.startswith("!송금"):
        try:
            _, target, amount = text.split()
            target = target.replace("@", "")
            amount = int(amount)
        except:
            update.message.reply_text("!송금 @아이디 10000")
            return

        if money.get(user, 0) < amount:
            update.message.reply_text("코인 부족")
            return

        money[user] -= amount
        money[target] = money.get(target, 0) + amount
        update.message.reply_text("송금 완료")

    # 관리자 지급
    elif text.startswith("!관리자지급"):
        if user != ADMIN:
            update.message.reply_text("관리자만 가능")
            return

        try:
            _, target, amount = text.split()
            target = target.replace("@", "")
            amount = int(amount)
        except:
            update.message.reply_text("!관리자지급 @아이디 10000")
            return

        money[target] = money.get(target, 0) + amount
        update.message.reply_text("관리자 지급 완료")

    # 올인
    elif text.startswith("!올인"):
        bet = money.get(user, 0)

        player = random.randint(0, 9)
        banker = random.randint(0, 9)

        if player > banker:
            money[user] += bet
            result = "승리"
        elif banker > player:
            money[user] = 0
            result = "패배"
        else:
            result = "타이"

        update.message.reply_text(
            f"올인 결과\n플:{player} 뱅:{banker}\n{result}\n코인:{money[user]}"
        )

    # 랭킹
    elif text.startswith("!랭킹"):
        rank = sorted(money.items(), key=lambda x: x[1], reverse=True)
        text_rank = "🏆 랭킹\n"
        for i, (u, c) in enumerate(rank[:5]):
            text_rank += f"{i+1}. {u} - {c}\n"
        update.message.reply_text(text_rank)

    # 바카라 배팅
    elif text.startswith("!배팅"):
        try:
            _, choice, bet = text.split()
            bet = int(bet)
        except:
            update.message.reply_text("!배팅 플 10000")
            return

        if money.get(user, 0) < bet:
            update.message.reply_text("코인 부족")
            return

        player = random.randint(0, 9)
        banker = random.randint(0, 9)

        if player > banker:
            result = "플"
        elif banker > player:
            result = "뱅"
        else:
            result = "타이"

        if choice == result:
            if result == "타이":
                money[user] += bet * 8
            else:
                money[user] += bet
            msg = "승리"
        else:
            money[user] -= bet
            msg = "패배"

        update.message.reply_text(
            f"🎰 바카라\n플:{player} 뱅:{banker}\n결과:{result}\n{msg}\n코인:{money[user]}"
        )

updater = Updater(TOKEN)
updater.dispatcher.add_handler(MessageHandler(Filters.text, message))

updater.start_polling()
updater.idle()
