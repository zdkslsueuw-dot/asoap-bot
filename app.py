import os
import json
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# الإعدادات
TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
URL = "https://asoap-bot.onrender.com" # تأكد أن هذا رابطك في Render

# تهيئة الأدوات
app = Flask(__name__)
groq_client = Groq(api_key=GROQ_API_KEY)
tg_application = Application.builder().token(TOKEN).build()

async def get_groq_response(text):
    completion = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": text}],
        model="llama3-8b-8192",
    )
    return completion.choices[0].message.content

@app.route(f'/{TOKEN}', methods=['POST'])
async def webhook(update: Update):
    """معالجة التحديثات القادمة من تليجرام"""
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), tg_application.bot)
        
        if update.message and update.message.text:
            user_text = update.message.text
            response_text = await get_groq_response(user_text)
            await update.message.reply_text(response_text)
            
        return "ok", 200

@app.route('/')
def index():
    return "ASOAP Engine is Running!", 200

async def setup_webhook():
    """إخبار تليجرام بمكان السيرفر"""
    bot = Bot(token=TOKEN)
    await bot.set_webhook(url=f"{URL}/{TOKEN}")
    print(f"Webhook set to: {URL}/{TOKEN}")

if __name__ == '__main__':
    # تشغيل تهيئة الـ Webhook في الخلفية
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_webhook())
    
    # تشغيل سيرفر Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
