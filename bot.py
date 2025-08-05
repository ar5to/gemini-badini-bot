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

# Load API keys
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")

# Per-user language direction: { user_id: "en_to_ku" or "ku_to_en" }
user_lang = {}

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_lang[user_id] = "en_to_ku"  # Default setting
    await update.message.reply_text(
        "👋 Welcome to Gemini Kurdish Bot!\n\n"
        "I will translate English → Kurdish Badini (Arabic script).\n"
        "Use /setlang en or /setlang ku to change direction."
    )

# /setlang command
async def setlang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    if not args or args[0].lower() not in ["en", "ku"]:
        await update.message.reply_text("❗ Usage: /setlang en or /setlang ku")
        return

    lang = args[0].lower()
    if lang == "en":
        user_lang[user_id] = "ku_to_en"
        await update.message.reply_text("✅ Translation set: Kurdish → English")
    else:
        user_lang[user_id] = "en_to_ku"
        await update.message.reply_text("✅ Translation set: English → Kurdish Badini")

# Handle text messages
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text.strip()

    if not user_input:
        await update.message.reply_text("❗ Please send a message to translate.")
        return

    lang_pref = user_lang.get(user_id, "en_to_ku")

    if lang_pref == "en_to_ku":
        prompt = f"""
        Translate the following English text into Kurdish Badini using Arabic script.
        Make it fluent and natural:

        {user_input}
        """
    else:
        prompt = f"""
        Translate the following Kurdish Badini (Arabic script) into natural and fluent English:

        {user_input}
        """

    try:
        response = model.generate_content(prompt)
        translated = response.text.strip()
        await update.message.reply_text(translated)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# Run the bot
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setlang", setlang))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 Gemini Badini Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
