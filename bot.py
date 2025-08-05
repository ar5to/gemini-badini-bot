import os
import logging
import tempfile
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from PIL import Image
import pytesseract
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

user_modes = {}

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_modes[update.effective_user.id] = "en_to_ku"
    keyboard = [
        [
            InlineKeyboardButton("English → Kurdish Badini", callback_data="en_to_ku"),
            InlineKeyboardButton("Kurdish Badini → English", callback_data="ku_to_en"),
        ]
    ]
    await update.message.reply_text(
        "👋 Send me any text or photo to translate.\n"
        "Use buttons below to switch translation direction.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def change_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mode = query.data
    user_modes[query.from_user.id] = mode
    await query.edit_message_text(
        f"✅ Translation mode set to: {'English → Kurdish Badini' if mode == 'en_to_ku' else 'Kurdish Badini → English'}"
    )


async def translate_text(text: str, mode: str):
    if mode == "en_to_ku":
        prompt = (
            "You are an expert translator fluent in Kurdish Badini dialect. "
            "Translate the following text into high-quality, natural Kurdish Badini:\n\n"
            f"{text}"
        )
    else:
        prompt = (
            "You are an expert translator fluent in Kurdish Badini dialect. "
            "Translate the following Kurdish Badini text into clear, natural English:\n\n"
            f"{text}"
        )

    response = await model.agenerate_text(prompt)
    return response.text.strip()


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = user_modes.get(update.effective_user.id, "en_to_ku")
    translated = await translate_text(update.message.text, mode)
    await update.message.reply_text(translated)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    with tempfile.NamedTemporaryFile(suffix=".jpg") as tf:
        await file.download_to_drive(tf.name)
        text = pytesseract.image_to_string(Image.open(tf.name))

    if not text.strip():
        await update.message.reply_text("❌ Could not extract text from the image.")
        return

    mode = user_modes.get(update.effective_user.id, "en_to_ku")
    translated = await translate_text(text, mode)
    await update.message.reply_text(translated)


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(change_mode))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logging.info("Bot started.")
    app.run_polling()


if __name__ == "__main__":
    main()
