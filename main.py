import random
import os
import threading
import asyncio
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, CommandHandler, filters, ContextTypes

# ======================
# 설정
# ======================
ADMIN_ID = 7476630439
BOT_TOKEN = "8484299407:AAF9Ja2dM0vlHSnsooJsZtsWIw-ayU2dyaY"
SUPPORT_URL = "https://t.me/GCOIN777_BOT"
OFFICIAL_CHANNEL_URL = "https://t.me/GCOIN7777"

# ======================
# 헬스체크
# ======================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Running")

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthCheckHandler).serve_forever()

# ======================
# 유저 데이터
# ======================
users = {}

def get_user(user_id, name, username=""):
    if user_id not in users:
        users[user_id] = {
            "name": name,
            "money": 100000
        }
    return users[user_id]

# ======================
# /start
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("봇 정상 작동!")

# ======================
# 명령어 처리
# ======================
async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == ".명령어":
        await update.message.reply_text("명령어: .명령어 /start")

# ======================
# 콜백
# ======================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

# ======================
# 실행
# ======================
async def main():
    threading.Thread(target=run_health_check, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_commands))
    app.add_handler(CallbackQueryHandler(handle_callback))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
