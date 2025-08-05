import os
import logging
import tempfile
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from google.cloud import speech_v1p1beta1 as speech
from PIL import Image
import pytesseract
import google.generativeai as genai
from dotenv import load_dotenv
import aiohttp
import base64

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

logging.basicConfig(level=logging.INFO)

# MODE: 'en_to_ku' or 'ku_to_en'
user_modes = {}

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_modes[update.effective_user.id] = "en_to_ku"
    keyboard = [
        [InlineKeyboardButton("🌐 EN → KU", callback_data="en_to_ku"),
         InlineKeyboardButton("🌐 KU → EN", callback_data="ku_to_en")]
    ]
    await update.message.reply_text(
        "👋 Send any text, image, or voice to translate into Kurdish Badini.\n\nYou can also switch translation direction.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def change_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    mode = query.data
    user_modes[query.from_user.id] = mode
    await query.answer()
    await query.edit_message_text(f"✅ Translation mode set to: {'EN → KU' if mode == 'en_to_ku' else 'KU → EN'}")

async def translate_text(text, mode="en_to_ku"):
    prompt = f"Translate this into {'Kurdish Badini' if mode == 'en_to_ku' else 'English'}:\n\n{text}"
    response = model.generate_content(prompt)
    return response.text.strip()

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = user_modes.get(update.effective_user.id, "en_to_ku")
    translated = await translate_text(update.message.text, mode)
    await update.message.reply_text(translated)

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    with tempfile.NamedTemporaryFile(suffix=".jpg") as tf:
        await file.download_to_drive(tf.name)
        text = pytesseract.image_to_string(Image.open(tf.name))
    if text.strip():
        mode = user_modes.get(update.effective_user.id, "en_to_ku")
        translated = await translate_text(text, mode)
        await update.message.reply_text(translated)
    else:
        await update.message.reply_text("❌ Couldn't extract text from the image.")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    with tempfile.NamedTemporaryFile(suffix=".ogg") as tf:
        await file.download_to_drive(tf.name)

        import subprocess
        wav_file = tf.name.replace(".ogg", ".wav")
        subprocess.run(["ffmpeg", "-i", tf.name, wav_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        client = speech.SpeechClient()
        with open(wav_file, "rb") as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code="en-US"
        )
        response = client.recognize(config=config, audio=audio)

        if not response.results:
            await update.message.reply_text("❌ Couldn't understand the voice.")
            return

        transcript = response.results[0].alternatives[0].transcript
        mode = user_modes.get(update.effective_user.id, "en_to_ku")
        translated = await translate_text(transcript, mode)
        await update.message.reply_text(f"🗣 {transcript}\n\n🌐 {translated}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(change_mode))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
