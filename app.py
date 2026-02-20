import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from groq import Groq

# 1. إعداد المفاتيح (تأكد أن الأسماء في Render متطابقة)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
client = Groq(api_key=GROQ_API_KEY)

# 2. سيرفر صغير لإبقاء Render سعيداً
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ASOAP Engine is Running")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    httpd = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    httpd.serve_forever()

# 3. معالجة الرسائل والرد باستخدام موديل حديث
async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    try:
        # استخدمنا هنا موديل llama-3.1-8b-instant لأنه سريع ومجاني ومتاح حالياً
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": update.message.text}],
            model="llama-3.1-8b-instant",
        )
        await update.message.reply_text(chat_completion.choices[0].message.content)
    except Exception as e:
        print(f"Groq Error: {e}")

# 4. تشغيل المحرك
async def run_bot():
    # تنظيف أي اتصالات سابقة
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    
    # بناء التطبيق
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), respond))
    
    async with app:
        await app.initialize()
        await app.start()
        print("Success! Bot is now listening for messages...")
        await app.updater.start_polling()
        while True: await asyncio.sleep(10)

if __name__ == '__main__':
    # تشغيل السيرفر في الخلفية
    threading.Thread(target=run_server, daemon=True).start()
    
    # تشغيل البوت
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        pass
