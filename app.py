import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from groq import Groq
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# جلب المفاتيح
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
client = Groq(api_key=GROQ_API_KEY)

# سيرفر بسيط لإرضاء Render
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Live!")

def run_health_check():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": update.message.text}],
            model="llama3-8b-8192",
        )
        await update.message.reply_text(completion.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")

async def main():
    # تشغيل السيرفر في خيط منفصل
    threading.Thread(target=run_health_check, daemon=True).start()
    
    # بناء وتشغيل البوت
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot is starting...")
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        # إبقاء البوت يعمل للأبد
        while True:
            await asyncio.sleep(100)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
