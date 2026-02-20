import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from groq import Groq

# جلب المفاتيح
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
client = Groq(api_key=GROQ_API_KEY)

# سيرفر بسيط لإرضاء Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ASOAP Engine is Running")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    httpd = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    httpd.serve_forever()

# معالجة الرسائل
async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": update.message.text}],
            model="llama3-8b-8192",
        )
        await update.message.reply_text(chat_completion.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")

async def run_bot():
    # --- الخدعة السحرية: حذف الـ Webhook القديم ليعمل الـ Polling ---
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    
    # بناء وتشغيل البوت
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), respond))
    
    async with app:
        await app.initialize()
        await app.start()
        print("Bot is Polling...")
        await app.updater.start_polling()
        while True: await asyncio.sleep(10)

if __name__ == '__main__':
    # تشغيل السيرفر في خيط
    threading.Thread(target=run_server, daemon=True).start()
    
    # تشغيل البوت
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        pass
