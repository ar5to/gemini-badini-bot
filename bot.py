import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import google.generativeai as genai

# Load secrets
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")

# Language map per user
user_lang = {}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang[update.effective_user.id] = "en_to_ku"
    await update.message.reply_text(
        "👋 Welcome to Gemini Kurdish Bot!\n"
        "I will translate English → Kurdish Badini (Arabic script).\n"
        "Use /setlang en or /setlang ku to change direction."
    )

# /setlang
async def setlang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    if not args or args[0].lower() not in ["en", "ku"]:
        await update.message.reply_text("❗ Usage: /setlang en or /setlang ku")
        return

    lang = args[0].lower()
    user_lang[user_id] = "ku_to_en" if lang == "en" else "en_to_ku"
    await update.message.reply_text("✅ Language updated.")

# Handle messages
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text.strip()

    lang_pref = user_lang.get(user_id, "en_to_ku")

    if lang_pref == "en_to_ku":
        prompt = f"Translate the following English sentence into Kurdish Badini using Arabic script only:\n\n{user_input}\n\nJust return the translation only with no extra words."
    else:
        prompt = f"Translate this Kurdish Badini sentence into natural English:\n\n{user_input}\n\nReturn only the translation."

    try:
        response = model.generate_content(prompt)
        translated = response.text.strip()
        # Clean redundant formatting
        if translated.startswith("**") and translated.endswith("**"):
            translated = translated.strip("*")
        await update.message.reply_text(translated)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# Run bot
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setlang", setlang))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
