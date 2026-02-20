import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from groq import Groq

# 1. جلب المفاتيح
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
client = Groq(api_key=GROQ_API_KEY)

# 2. سيرفر بسيط لإرضاء Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    httpd = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    httpd.serve_forever()

# 3. معالجة الرسائل
async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": update.message.text}],
            model="llama3-8b-8192",
        )
        await update.message.reply_text(chat_completion.choices[0].message.content)
    except Exception as e:
        print(f"Groq Error: {e}")

# 4. المحرك الرئيسي
if __name__ == '__main__':
    # تشغيل السيرفر في خيط منفصل فوراً
    threading.Thread(target=run_server, daemon=True).start()
    
    # بناء البوت بنظام الـ Polling البسيط
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), respond))
    
    print("ASOAP Bot Started...")
    app.run_polling()
