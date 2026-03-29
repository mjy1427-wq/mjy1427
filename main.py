import os, random, logging, time, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CallbackQueryHandler, CallbackContext, MessageHandler, Filters

# --- [1. Render 포트 에러 방지용 가짜 서버] ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active!")
    def log_message(self, format, *args): return

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# --- [2. 시스템 설정] ---
TOKEN = "8603959168:AAH9Jq_5erWZgvocsvnjs1rP4G_F9VW-CbQ" #
ADMIN_ID = 7476630349
TITLE = "🏆 [포켓몬월드:약육강식 에디션] 🏆"

user_data = {}
POKE_NAMES = ["피카츄", "리자몽", "뮤츠", "루기아", "칠색조", "세레비", "레쿠쟈", "디아루가", "펄기아", "아르세우스"]

# --- [3. 메뉴 UI 구성] ---
def get_main_menu():
    # 수집 도감 -> 슬롯머신으로 명칭 변경 완료
    keyboard = [
        [InlineKeyboardButton("🍃 탐험하기", callback_data="m_exp"), InlineKeyboardButton("💻 PC등록", callback_data="m_pc")],
        [InlineKeyboardButton("💳 내 정보", callback_data="m_inf"), InlineKeyboardButton("🎒 내 가방", callback_data="m_bag")],
        [InlineKeyboardButton("🏪 상점", callback_data="m_sh"), InlineKeyboardButton("💰 판매장", callback_data="m_sell")],
        [InlineKeyboardButton("🎰 슬롯머신", callback_data="m_slot"), InlineKeyboardButton("🏆 랭킹", callback_data="m_rank")],
        [InlineKeyboardButton("🎒 배틀 기어", callback_data="m_gr"), InlineKeyboardButton("⚒️ 스타포스 강화", callback_data="m_st")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button():
    # 모든 버튼에 돌아가기 추가
    return [InlineKeyboardButton("🔙 메인으로 돌아가기", callback_data="m_back")]

# --- [4. 콜백 핸들러 (버튼 로직)] ---
def callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    uid = query.from_user.id
    if uid not in user_data: return query.answer("먼저 .가입 을 해주세요!")
    
    user = user_data[uid]
    data = query.data

    if data == "m_back":
        query.edit_message_text(f"{TITLE}\n원하시는 기능을 선택하세요. ㅡㅡ+", reply_markup=get_main_menu())

    elif data == "m_exp":
        r = random.random() * 100
        # 7단계 등급 체계 적용
        if r <= 1.0: tier = "신화"
        elif r <= 3.0: tier = "환상"
        elif r <= 8.0: tier = "전설"
        elif r <= 18.0: tier = "유니크"
        elif r <= 33.0: tier = "희귀"
        elif r <= 58.0: tier = "레어"
        else: tier = "일반"
        
        context.user_data['temp_tier'] = tier
        # 조우 시 등급 명확히 표기
        msg = f"❗ **[{tier} 등급]** 조우!\n신중하게 던지세요! ㅡㅡ+"
        btns = [
            [InlineKeyboardButton("⚾️ 몬스터볼", callback_data="c_n"), 
             InlineKeyboardButton(f"🟣 마스터볼({user['items'].get('마스터볼',0)})", callback_data="c_m")],
            back_button()
        ]
        query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(btns), parse_mode='Markdown')

    elif data.startswith("c_"):
        tier = context.user_data.get('temp_tier', "일반")
        is_master = (data == "c_m")
        
        # 일반/레어 등급 일반볼 100% 포획 로직
        if not is_master and tier in ["일반", "레어"]:
            success = True
        elif is_master:
            if user['items'].get('마스터볼', 0) > 0:
                user['items']['마스터볼'] -= 1
                success = True
            else: return query.answer("마스터볼이 부족합니다!")
        else:
            rates = {"희귀": 30, "유니크": 15, "전설": 7, "환상": 3, "신화": 0.5}
            success = (random.random() * 100) <= rates.get(tier, 50)

        if success:
            reward = random.randint(10000, 100000) #
            user['gold'] += reward
            name = random.choice(POKE_NAMES)
            user['pokes'].append({"name": name, "tier": tier, "atk": 100})
            msg = f"🎊 **{name}({tier})** 포획 성공!\n💰 보상: **+{reward:,}G** 획득!"
        else:
            msg = f"💨 {tier} 등급이 도망갔습니다... ㅡㅡ"
            
        query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([back_button()]))

    # 나머지 기능들에 대한 기본 응답 및 돌아가기
    elif data in ["m_pc", "m_inf", "m_bag", "m_sh", "m_sell", "m_slot", "m_rank", "m_gr", "m_st"]:
        query.edit_message_text("🚧 현재 관리자님이 업데이트 중인 메뉴입니다! ㅡㅡ+", 
                                reply_markup=InlineKeyboardMarkup([back_button()]))

# --- [5. 명령어 및 메인 실행부] ---
def handle_msg(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    if update.message.text == ".가입":
        if uid not in user_data:
            user_data[uid] = {"name": update.effective_user.first_name, "gold": 1000000, "items": {"마스터볼": 1}, "pokes": [], "inventory": {}}
            update.message.reply_text(f"{TITLE}\n가입 완료! ㅡㅡ+")
    elif update.message.text == ".메뉴":
        if uid in user_data:
            update.message.reply_text(f"{TITLE}\n원하시는 기능을 선택하세요.", reply_markup=get_main_menu())

def main():
    # Render 포트 에러 방지 가짜 서버 가동
    threading.Thread(target=run_health_check, daemon=True).start()
    
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_msg))
    dp.add_handler(CallbackQueryHandler(callback_handler))
    
    print("🚀 서버 가동 완료! ㅡㅡ+")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
