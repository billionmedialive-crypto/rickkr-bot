import os
import asyncio
import threading
from flask import Flask
import google.generativeai as genai
from gtts import gTTS
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

SYSTEM_PROMPT = """
You are Rickkr - a friendly Malayalam + Manglish Telegram sales assistant for Rickkr Ayurvedic Hair Oil.
- Your tone: friendly, casual, like a local shop guy from Kerala, use emojis.
- Language: User speaks in Malayalam or English, reply in same style (mostly Manglish).
- Product: Rickkr Herbal Hair Oil, 100% Ayurvedic, stops hair fall in 14 days, regrows hair, no chemicals. Price Rs 499, Free Delivery all Kerala, COD available.
- Goal: Answer doubts, push to buy. If user says want to buy, ask Name, Place, Phone Number, collect order.
- Always be helpful. Keep replies short (under 3 lines) unless explaining.
- If user asks about ingredients: Bhringraj, Amla, Coconut oil, Rosemary, etc.
"""

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Rickkr Bot is Live! Bot is running in background."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hai! 👋 Njan Rickkr aanu. Thalayanu kuzhappam undo? Mudhi kozhichil, thala mudi valarchan njan help cheyyam. 😊\n\nRickkr Hair Oil - 14 divasam kond hair fall nirkkum! Price Rs 499, Free Delivery.\nOrder cheyyano?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        # Generate reply from Gemini
        response = model.generate_content(f"{SYSTEM_PROMPT}\nUser: {user_text}\nRickkr:")
        reply_text = response.text

        # Send Text
        await update.message.reply_text(reply_text)

        # Send Voice (Free gTTS)
        try:
            tts = gTTS(text=reply_text, lang='ml', slow=False)
            # gTTS doesn't support manglish well, fallback to ml, if fails use en
            voice_file = "/tmp/voice.mp3"
            tts.save(voice_file)
            await update.message.reply_voice(voice=open(voice_file, 'rb'))
        except:
            # Fallback English voice if Malayalam fails
            try:
                tts = gTTS(text=reply_text, lang='en', slow=False)
                voice_file = "/tmp/voice.mp3"
                tts.save(voice_file)
                await update.message.reply_voice(voice=open(voice_file, 'rb'))
            except Exception as e:
                print(f"Voice error: {e}")

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("Sorry, oru chinna technical issue. Oru minute kazhinju try cheyyamo? 🙏")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

async def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot started...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    # Start Flask in separate thread for Render health check
    threading.Thread(target=run_flask, daemon=True).start()
    # Start Telegram bot
    asyncio.run(run_bot())
