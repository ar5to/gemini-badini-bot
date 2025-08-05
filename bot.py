import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from google.generativeai import GenerativeModel, configure

load_dotenv()

# Gemini setup
configure(api_key=os.getenv("GEMINI_API_KEY"))
model = GenerativeModel("gemini-pro")

# Telegram setup
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Track user translation direction (default: English → Kurdish Badini)
user_lang = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Gemini Kurdish Bot!\n"
        "I will translate English → Kurdish Badini.\n"
        "Use /setlang en or /setlang ku to change direction."
    )

async def setlang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    if not args or args[0] not in ["en", "ku"]:
        await update.message.reply_text("❌ Usage: /setlang en or /setlang ku")
        return

    direction = "en_to_ku" if args[0] == "en" else "ku_to_en"
    user_lang[user_id] = direction
    await update.message.reply_text(f"✅ Translation direction set to: {args[0]}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text.strip()
    direction = user_lang.get(user_id, "en_to_ku")

    # Clean translation prompt
    if direction == "en_to_ku":
        prompt = f"Translate the following sentence from English to Kurdish Badini:\n\n{user_input}"
    else:
        prompt = f"Translate the following sentence from Kurdish Badini to English:\n\n{user_input}"

    try:
        response = model.generate_content(prompt, stream=True)
        translated = "".join(chunk.text for chunk in response).strip()
        translated = translated.replace("**", "").strip()

        await update.message.reply_text(translated)

    except Exception as e:
        await update.message.reply_text("⚠️ An error occurred. Please try again.")
        print(f"Translation error: {e}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setlang", setlang))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
