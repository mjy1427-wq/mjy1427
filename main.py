import logging, time, random, os
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler

# --- [1] 서버 유지 설정 ---
app = Flask('')
@app.route('/')
def home(): return "G-COIN BOT Online"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
def keep_alive(): Thread(target=run).start()

# --- [2] 데이터 설정 ---
# 수정됨: EJ1427 님을 관리자로 설정했습니다.
ADMIN_ID = "EJ1427" 

ORES = {
    "coal": {"name": "🌑 석탄", "price": 5000, "tier": 1, "chance": 25},
    "iron": {"name": "🔘 철광석", "price": 10000, "tier": 1, "chance": 18},
    "copper": {"name": "🟤 구리광석", "price": 15000, "tier": 1, "chance": 15},
    "silver": {"name": "🥈 은광석", "price": 40000, "tier": 2, "chance": 10},
    "gold": {"name": "🥇 금광석", "price": 80000, "tier": 2, "chance": 8},
    "platinum": {"name": "⚪ 백금광석", "price": 150000, "tier": 2, "chance": 6},
    "crystal": {"name": "🔮 수정", "price": 400000, "tier": 3, "chance": 5},
    "emerald": {"name": "🧪 에메랄드", "price": 700000, "tier": 3, "chance": 4},
    "sapphire": {"name": "🌌 사파이어", "price": 1000000, "tier": 3, "chance": 3},
    "diamond": {"name": "💎 다이아몬드", "price": 2000000, "tier": 4, "chance": 2},
    "ruby": {"name": "🍎 루비", "price": 3500000, "tier": 4, "chance": 1.5},
    "obsidian": {"name": "🖤 흑요석", "price": 5000000, "tier": 4, "chance": 1},
    "core": {"name": "👑 전설의 핵", "price": 10000000, "tier": 5, "chance": 0.8},
    "dragon": {"name": "🐲 드래곤 스톤", "price": 25000000, "tier": 5, "chance": 0.2}
}

PICKS = {
    "Wood": {"price": 1000000, "durability": 100},
    "Stone": {"price": 5000000, "durability": 300},
    "Iron": {"price": 15000000, "durability": 500},
    "Gold": {"price": 50000000, "durability": 1000},
    "Diamond": {"price": 250000000, "durability": 5000},
    "Netherite": {"price": 1000000000, "durability": 10000}
}

user_data = {}
ROADMAP_URL = "https://raw.githubusercontent.com/mjy1427-wq/mjy1427/main/roadmap.png"

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {'money': 1000000, 'pick_name': 'Wood', 'durability': 100, 'max_durability': 100, 'inventory': {k: 0 for k in ORES.keys()}}
    return user_data[uid]

# --- [3] 메시지 핸들러 ---
def handle_message(update, context):
    uid = update.message.from_user.username
    if not uid: return
    user = get_user(uid); text = update.message.text

    if text.startswith("!지급") and uid == ADMIN_ID:
        try:
            p = text.split(); target = p[1].replace("@", ""); amt = int(p[2])
            get_user(target)['money'] += amt
            update.message.reply_text(f"✅ @{target}님에게 {amt:,} G 지급 완료!")
        except: update.message.reply_text("❌ 사용법: !지급 아이디 금액")
        return

    if text == "!가입":
        update.message.reply_text("🎊 가입 완료! 기본 Wood 곡괭이가 지급되었습니다.")
    elif text == "!채광":
        if user['durability'] <= 0: return update.message.reply_text("🪓 곡괭이 파손! 상점에서 구매하세요.")
        user['durability'] -= 5; rand = random.random() * 100; curr = 0; sel = "coal"
        for k, v in ORES.items():
            curr += v['chance']
            if rand <= curr: sel = k; break
        if ORES[sel]['tier'] == 5 and user['pick_name'] != "Netherite":
            sel = "coal"; update.message.reply_text("⚠️ 5티어 발견! 하지만 곡괭이가 약해 석탄을 캤습니다.")
        user['inventory'][sel] += 1
        update.message.reply_text(f"⛏ **채광 성공!**\n💎 획득: {ORES[sel]['name']}\n🔧 내구도: {user['durability']}/{user['max_durability']}", parse_mode=ParseMode.MARKDOWN)
    elif text == "!판매":
        kb = [[InlineKeyboardButton(f"{i}티어", callback_data=f"s_{i}") for i in range(1, 5)], [InlineKeyboardButton("5티어", callback_data="s_5"), InlineKeyboardButton("전체판매", callback_data="s_all")]]
        update.message.reply_text("💰 **판매 등급 선택**", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
    elif text == "!곡괭이":
        msg = "⛏ **상점**\n" + "\n".join([f"**{k}**: {v['price']:,} G" for k, v in PICKS.items()])
        kb = [[InlineKeyboardButton(f"💰 {k} 구매", callback_data=f"buy_{k}")] for k in PICKS.keys()]
        update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
    elif text == "!내정보":
        update.message.reply_text(f"👤 **@{uid}**\n💵 잔액: {user['money']:,} G\n⛏ 곡괭이: {user['pick_name']}\n🔧 내구도: {user['durability']}")
    elif text == "!바카라":
        update.message.reply_photo(photo=ROADMAP_URL, caption="📊 **바카라 출목표**")

# --- [4] 콜백 핸들러 ---
def handle_callback(update, context):
    q = update.callback_query; uid = q.from_user.username; user = get_user(uid)
    if q.data.startswith("s_"):
        gain = 0
        if q.data == "s_all":
            for k in ORES: gain += user['inventory'][k] * ORES[k]['price']; user['inventory'][k] = 0
        else:
            t = int(q.data.split("_")[1])
            for k, v in ORES.items():
                if v['tier'] == t: gain += user['inventory'][k] * v['price']; user['inventory'][k] = 0
        user['money'] += gain; q.edit_message_text(f"✅ 판매 완료! +{gain:,} G\n현재 잔액: {user['money']:,} G")
    elif q.data.startswith("buy_"):
        pk = q.data.split("_")[1]; info = PICKS[pk]
        if user['money'] >= info['price']:
            user['money'] -= info['price']; user['pick_name'] = pk
            user['durability'] = info['durability']; user['max_durability'] = info['durability']
            q.edit_message_text(f"✅ {pk} 곡괭이 구매 성공!")
        else: q.answer("❌ 잔액 부족!", show_alert=True)
    q.answer()

# --- [5] 메인 실행부 ---
if __name__ == '__main__':
    keep_alive()
    TOKEN = "8771125252:AAFbKHLcDM2KhLR3MIp6ZGOnFQQWlIQUIlc"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(handle_callback))
    updater.start_polling(); updater.idle()
