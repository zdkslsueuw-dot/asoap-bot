import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from groq import Groq
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# جلب المفاتيح من إعدادات Render
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
client = Groq(api_key=GROQ_API_KEY)

# سيرفر بسيط لإرضاء Render
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ASOAP Bot is Running")

def run_health_check_server():
    server = HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 8080))), SimpleHandler)
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

if __name__ == '__main__':
    threading.Thread(target=run_health_check_server, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("Bot is starting...")
    app.run_polling()
