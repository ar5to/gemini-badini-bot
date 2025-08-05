import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import google.generativeai as genai

# Load env vars
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini setup
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")

# Store user language preferences
user_languages = {}  # user_id: "en_to_ku" or "ku_to_en"

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_languages[user_id] = "en_to_ku"  # default
    await update.message.reply_text(
        "👋 Welcome!\n"
        "Send me a message and I’ll translate it.\n"
        "Default: English → Kurdish Badini\n"
        "Use /setlang to switch translation direction."
    )

# /setlang command
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = update.message.text.strip().lower()

    if "ku" in msg:
        user_languages[user_id] = "en_to_ku"
        await update.message.reply_text("✅ Set to English → Kurdish Badini")
    elif "en" in msg:
        user_languages[user_id] = "ku_to_en"
        await update.message.reply_text("✅ Set to Kurdish Badini → English")
    else:
        await update.message.reply_text("❗ Usage: /setlang en OR /setlang ku")

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    user_id = update.effective_user.id
    lang_pref = user_languages.get(user_id, "en_to_ku")

    if not user_input:
        await update.message.reply_text("❗ Please enter a message to translate.")
        return

    # Build prompt based on language direction
    if lang_pref == "en_to_ku":
        prompt = f"""
        Translate the following English text into Kurdish Badini using Arabic script.
        Make it fluent and natural:

        ---
        {user_input}
        ---
        """
    else:
        prompt = f"""
        Translate the following Kurdish Badini text (written in Arabic script) into natural, fluent English:

        ---
        {user_input}
        ---
        """

    try:
        response = model.generate_content(prompt)
        await update.message.reply_text(response.text.strip())
    except Exception as e:
        await update.message.reply_text(f"❌ هەڵە ڕوویدا:\n{str(e)}")

# Main bot launcher
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setlang", set_language))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Gemini Badini Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
