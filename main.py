import random, os, threading, asyncio, json, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- [이전 설정 및 FULL_DECK 데이터는 동일하게 유지] ---
ADMIN_ID = 7476630349 
BOT_TOKEN = "8484299407:AAGfYDpLhfS7eTIjsC16Fe6Bklqf6T22Gv0"
DATA_FILE = "gcoin_ultra_final.json"
SUPPORT_URL = "https://t.me/your_support_link" 
NOTICE_URL = "https://t.me/your_notice_link"

game_room = {
    "is_open": False,
    "round_no": 1,
    "end_time": 0,
    "bets": [] 
}

# [바카라 카드 데이터 - 생략된 부분은 이전 답변의 52장 데이터를 그대로 넣으세요]
FULL_DECK = [...] 

# --- [DB 및 유저 관리 로직 동일] ---

async def process_baccarat(context: ContextTypes.DEFAULT_TYPE, chat_id):
    global game_room
    round_no = game_room["round_no"]
    
    # 1. 베팅 마감 알림
    await context.bot.send_message(chat_id, f"<b>🚨 [제 {round_no}회차] 베팅이 마감되었습니다!</b>", parse_mode="HTML")
    
    # 2. 5초 대기 후 결과 예고
    await asyncio.sleep(5)
    await context.bot.send_message(chat_id, "<b>🔔 5초 후 결과를 발표합니다!</b>", parse_mode="HTML")
    await asyncio.sleep(2) # 짧은 추가 긴장감

    deck = FULL_DECK.copy(); random.shuffle(deck)
    p, b = [deck.pop(), deck.pop()], [deck.pop(), deck.pop()]
    ps, bs = sum(c['s'] for c in p)%10, sum(c['s'] for c in b)%10

    # 3. 카드 연출 (실제 바카라 룰)
    await context.bot.send_message(chat_id, "<b>[Player Card]</b>", parse_mode="HTML")
    for c in p: await context.bot.send_sticker(chat_id, c['id'])
    
    await asyncio.sleep(1)
    await context.bot.send_message(chat_id, "<b>[Banker Card]</b>", parse_mode="HTML")
    for c in b: await context.bot.send_sticker(chat_id, c['id'])

    # [바카라 공식 서드 카드 룰 적용]
    # 플레이어 합 0~5인 경우 한 장 더
    if ps <= 5:
        await asyncio.sleep(1)
        tc = deck.pop(); p.append(tc); ps = sum(c['s'] for c in p)%10
        await context.bot.send_message(chat_id, "🃏 플레이어 추가 카드(Third Card)!")
        await context.bot.send_sticker(chat_id, tc['id'])

    # 뱅커 합 0~5인 경우 한 장 더 (간략화된 룰 적용, 실제로는 플레이어 3번째 카드에 따라 다름)
    if bs <= 5:
        await asyncio.sleep(1)
        tc = deck.pop(); b.append(tc); bs = sum(c['s'] for c in b)%10
        await context.bot.send_message(chat_id, "🃏 뱅커 추가 카드(Third Card)!")
        await context.bot.send_sticker(chat_id, tc['id'])

    # 4. 결과 계산 및 정산
    win = "P" if ps > bs else "B" if bs > ps else "T"
    admin_user = users.get(ADMIN_ID)
    
    res_msg = f"<b>🏆 제 {round_no}회차 결과 발표 🏆</b>\n\n"
    res_msg += f"P({ps}) : B({bs})\n"
    res_msg += f"승리팀: {'플레이어 🔵' if win=='P' else '뱅커 🔴' if win=='B' else '타이 🟢'}\n\n"
    res_msg += "<b>[당첨 내역]</b>\n"

    winners_exist = False
    for bet in game_room["bets"]:
        u = users[bet['uid']]
        rate = 8 if win=="T" else (1.95 if win=="B" else 2)
        if (bet['side']=="P" and win=="P") or (bet['side']=="B" and win=="B") or (bet['side']=="T" and win=="T"):
            w_amt = int(bet['amount'] * rate)
            u["money"] += w_amt
            if admin_user: admin_user["money"] -= w_amt
            res_msg += f"✨ {u['name']}: +{w_amt:,} G\n"
            winners_exist = True
        else:
            res_msg += f"💀 {u['name']}: 낙첨\n"
    
    if not winners_exist: res_msg += "당첨자가 없습니다.\n"
    
    await context.bot.send_message(chat_id, res_msg, parse_mode="HTML")
    
    # 방 초기화 및 회차 증가
    game_room["is_open"] = False
    game_room["bets"] = []
    game_room["round_no"] += 1
    save_db()

async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_room
    if not update.message or not update.message.text: return
    text, uid, chat_id = update.message.text.strip(), update.effective_user.id, update.message.chat_id
    user = get_u(uid, update.effective_user.first_name, update.effective_user.username)

    if text.startswith((".플", ".뱅", ".타")):
        try:
            side = "P" if ".플" in text else "B" if ".뱅" in text else "T"
            amount = int(text.split()[1])
            if user["money"] < amount: return await update.message.reply_text("❌ 잔액이 부족합니다.")

            if not game_room["is_open"]:
                game_room["is_open"] = True
                game_room["end_time"] = time.time() + 30
                # 30초 카운트다운 시작
                asyncio.create_task(timer_and_process(context, chat_id))
                await update.message.reply_html(f"<b>🎰 [제 {game_room['round_no']}회차] 베팅 시작!</b>\n30초 후 마감됩니다. (현재 참여 가능)")

            user["money"] -= amount
            # 관리자 계정에 낙첨금 예치
            admin = get_u(ADMIN_ID, "관리자", "admin")
            admin["money"] += amount
            
            game_room["bets"].append({"uid": uid, "side": side, "amount": amount})
            save_db()
            await update.message.reply_text(f"✅ {side}에 {amount:,}G 베팅 완료!")
        except: pass

async def timer_and_process(context, chat_id):
    await asyncio.sleep(30)
    await process_baccarat(context, chat_id)

# --- [이하 main 함수 동일] ---
