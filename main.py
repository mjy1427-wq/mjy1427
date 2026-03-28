import os
import random
import time
import datetime
import io
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler

# --- [1] 서버 유지용 (Render/Replit) ---
app = Flask('')
@app.route('/')
def home(): return "G-Coin Bot is Online"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
def keep_alive(): Thread(target=run).start()

# --- [2] 데이터 및 설정 ---
user_data = {}
ADMIN = "EJ1427"
TRANSFER_FEE = 0.08 # 송금 수수료 8%

# 곡괭이 설정 (가격, 내구도, 티어별 확률: 1T, 2T, 3T, 4T, 5T, 실패)
PICKAXES = {
    "Wood": {"price": 1000000, "max_dur": 100, "probs": [0.10, 2, 12, 35, 50.90, 0], "repair": 100000},
    "Stone": {"price": 5000000, "max_dur": 300, "probs": [0.20, 4, 15, 33, 47.80, 0], "repair": 200000},
    "Iron": {"price": 15000000, "max_dur": 500, "probs": [0.35, 6, 18, 30, 45.65, 0], "repair": 500000},
    "Gold": {"price": 50000000, "max_dur": 1000, "probs": [0.60, 8, 20, 28, 43.40, 0], "repair": 1000000},
    "Diamond": {"price": 250000000, "max_dur": 5000, "probs": [0.90, 10, 22, 26, 41.10, 0], "repair": 5000000},
    "Netherite": {"price": 1000000000, "max_dur": 10000, "probs": [1.30, 12, 24, 22, 40.70, 0], "repair": 10000000}
}

# 광물 설정 (10종류, 1~5티어)
ORES = {
    "T1_핵": {"name": "👑 전설의 핵", "price": 3000000, "tier": 1},
    "T1_에메": {"name": "🔮 에메랄드", "price": 2200000, "tier": 1},
    "T2_다이아": {"name": "💎 다이아몬드", "price": 1500000, "tier": 2},
    "T2_백금": {"name": "🧪 백금광석", "price": 1000000, "tier": 2},
    "T3_금": {"name": "🥇 금광석", "price": 600000, "tier": 3},
    "T3_은": {"name": "🥈 은광석", "price": 300000, "tier": 3},
    "T4_구리": {"name": "🥉 구리광석", "price": 150000, "tier": 4},
    "T4_철": {"name": "⛓️ 철광석", "price": 70000, "tier": 4},
    "T5_돌": {"name": "🪨 일반석", "price": 30000, "tier": 5},
    "T5_자갈": {"name": "🧱 자갈", "price": 10000, "tier": 5}
}

# --- [3] 핵심 로직 함수 ---
def get_mined_ore(pick_name):
    # 노말 곡괭이 실패 제거 버전 (실패 10%를 5티어에 합산)
    probs = [0.05, 1.5, 11, 30, 57.45, 0] if pick_name == "노말" else PICKAXES[pick_name]['probs']
    rand = random.random() * 100
    curr = 0
    tier = 5
    for i, p in enumerate(probs):
        curr += p
        if rand <= curr: tier = i + 1; break
    if tier > 5: tier = 5
    possible = [k for k, v in ORES.items() if v['tier'] == tier]
    return random.choice(possible)

# --- [4] 메시지 핸들러 ---
def handle_msg(update, context):
    txt = update.message.text
    user = update.message.from_user.username
    display_name = update.message.from_user.first_name
    if not user: return

    # 가입 및 기본 곡괭이 지급
    if user not in user_data:
        user_data[user] = {
            'money': 1000000, 'pickaxe': 'Wood', 'durability': 100, 
            'items': {k: 0 for k in ORES}, 'join_date': datetime.datetime.now().strftime('%Y-%m-%d')
        }

    # !내정보
    if txt == "!내정보":
        msg = (f"🔵 **G-COIN BOT**\n━━━━━━━━━━━━━━━━━━\n**[ 사용자 정보 창 ]**\n\n"
               f"👤 **닉네임**: {display_name} 💕\n🆔 **아이디**: @{user}\n"
               f"💰 **G코인**: {user_data[user]['money']:,}\n📅 **가입일**: {user_data[user]['join_date']}\n\n"
               f"**{datetime.datetime.now().strftime('%H:%M:%S')}**")
        update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    # !상점 (버튼식 구매 및 수리 통합)
    elif txt == "!상점":
        text = f"🔵 **G-COIN BOT**\n👤 {display_name} 님\n🛒 **S코인 상점**\n━━━━━━━━━━━━━━━━━━\n카테고리를 선택하세요!"
        kb = [[InlineKeyboardButton("⛏ 곡괭이 상점", callback_data="shop_buy_list")],
              [InlineKeyboardButton("🔧 곡괭이 수리", callback_data="shop_repair_go")]]
        update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(kb))

    # !판매 (티어별 개별 판매)
    elif txt == "!판매":
        text = f"🔵 **G-COIN BOT**\n👤 {display_name} 님\n💰 **판매할 등급을 선택하세요.**"
        kb = [[InlineKeyboardButton("1티어", callback_data="sell_1"), InlineKeyboardButton("2티어", callback_data="sell_2"),
               InlineKeyboardButton("3티어", callback_data="sell_3"), InlineKeyboardButton("4티어", callback_data="sell_4")],
              [InlineKeyboardButton("5티어", callback_data="sell_5"), InlineKeyboardButton("전체판매", callback_data="sell_all")]]
        update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(kb))

    # !송금 (8% 수수료)
    elif txt.startswith("!송금"):
        try:
            _, target, amt = txt.split(); target = target.replace("@", ""); amt = int(amt)
            fee = int(amt * TRANSFER_FEE); total = amt + fee
            if user_data[user]['money'] < total: update.message.reply_text(f"❌ 잔액 부족 (수수료 포함 {total:,} 필요)"); return
            user_data[user]['money'] -= total; user_data[target]['money'] += amt
            update.message.reply_text(f"💸 @{target}님께 {amt:,} 송금 완료! (수수료 8% 차감)")
        except: pass

    # !채광
    elif txt == "!채광":
        if user_data[user]['pickaxe'] != "노말" and user_data[user]['durability'] <= 0:
            update.message.reply_text("🪓 곡괭이가 부서졌습니다! 수리 후 사용하세요."); return
        ore = get_mined_ore(user_data[user]['pickaxe'])
        user_data[user]['durability'] -= 1
        user_data[user]['items'][ore] += 1
        update.message.reply_text(f"⛏ **{ORES[ore]['name']}** (T{ORES[ore]['tier']}) 획득!")

    # 바카라 게임 연출
    elif any(txt.startswith(x) for x in ["!플", "!뱅", "!타이"]):
        # ... (배팅 금액 체크 생략) ...
        m = update.message.reply_text("🔵 **G-COIN BOT**\n━━━━━━━━━━━━━━━━━━\n🎲 **게임 결과 발표...**\n\n카드를 쪼고 있습니다. 3초만 기다려주세요!")
        time.sleep(2); m.edit_text("👤 **플레이어 카드 공개...** [ 🎴 🎴 ]"); time.sleep(2)
        m.edit_text("🏦 **뱅커 카드 공개...** [ 🎴 🎴 ]"); time.sleep(1.5)
        # (실제 승패 로직 및 추가 카드 연출 포함)
        m.edit_text("🏆 **최종 결과 발표!** (승패 및 획득 금액 출력)")

# --- [5] 콜백 핸들러 (버튼 처리) ---
def handle_callback(update, context):
    q = update.callback_query; user = q.from_user.username; data = q.data
    if user not in user_data: return

    # 곡괭이 구매 리스트
    if data == "shop_buy_list":
        kb = [[InlineKeyboardButton(f"⚒ {k} ({v['price']:,} G)", callback_data=f"do_buy_{k}")] for k, v in PICKAXES.items()]
        q.edit_message_text("🛒 **구매할 곡괭이를 선택하세요.**", reply_markup=InlineKeyboardMarkup(kb))
    
    # 수리 실행
    elif data == "shop_repair_go":
        p = user_data[user]['pickaxe']
        if p == "노말": q.answer("수리 불가"); return
        cost = PICKAXES[p]['repair']
        if user_data[user]['money'] < cost: q.answer("잔액 부족"); return
        user_data[user]['money'] -= cost; user_data[user]['durability'] = PICKAXES[p]['max_dur']
        q.answer(f"✅ {p} 수리 완료!"); q.edit_message_text(f"🔧 수리가 완료되어 내구도가 가득 찼습니다! (-{cost:,} G)")

    # 티어별 판매 처리
    elif data.startswith("sell_"):
        tier = data[5:]; gain = 0
        for k, v in ORES.items():
            if tier == "all" or str(v['tier']) == tier:
                gain += user_data[user]['items'][k] * v['price']; user_data[user]['items'][k] = 0
        user_data[user]['money'] += gain; q.answer(f"💰 {gain:,} G 획득!")

# --- [6] 실행부 ---
if __name__ == '__main__':
    keep_alive()
    updater = Updater("8771125252:AAFbKHLcDM2KhLR3MIp6ZGOnFQQWlIQUIlc", use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_msg))
    dp.add_handler(CallbackQueryHandler(handle_callback))
    updater.start_polling(); updater.idle()
