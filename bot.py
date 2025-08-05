import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import google.generativeai as genai

# Load keys
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Setup Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 سڵاو! نوسیاری بنێرە بۆ وەرگێڕان بۆ کوردیی بادینی (بە نووسینی عەرەبی).")

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    prompt = f"""
    Translate the following text into **Kurdish Badini** using the **Arabic script**.
    Make it sound **natural and fluent**, like a native speaker would say it:

    ---
    {user_input}
    ---
    """
    try:
        response = model.generate_content(prompt)
        await update.message.reply_text(response.text.strip())
    except Exception as e:
        await update.message.reply_text(f"❌ هەڵە ڕوویدا:\n{str(e)}")

# Main bot runner
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Gemini Badini Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
