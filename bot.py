import logging
import os
import asyncio
from dotenv import load_dotenv
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import google.generativeai as genai
from PIL import Image
import pytesseract
# from google.cloud import speech # Optional: for voice messages

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Optional: for voice messages
# GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") 

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# --- Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# In-memory storage for user's translation mode
user_translation_mode = {}
DEFAULT_MODE = "en_to_ku"

# --- Helper Functions ---
async def translate_text(text: str, target_lang: str) -> str:
    """Translates text using the Gemini 2.5 Pro model."""
    if target_lang == "en_to_ku":
        prompt = f"You are an expert translator. Translate this into Kurdish Badini dialect naturally and fluently: {text}"
    else: # ku_to_en
        prompt = f"You are an expert translator. Translate this Kurdish Badini text into fluent English: {text}"

    try:
        model = genai.GenerativeModel('gemini-2.5-pro')
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error during translation: {e}")
        return "Sorry, I couldn't translate that. Please try again."

# --- Command Handlers ---
async def start(update: Update, context: CallbackContext) -> None:
    """Sends a welcome message with language selection buttons."""
    keyboard = [
        [InlineKeyboardButton("English → Kurdish Badini", callback_data='en_to_ku')],
        [InlineKeyboardButton("Kurdish Badini → English", callback_data='ku_to_en')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Welcome to the translator bot! Please choose your desired translation direction:',
        reply_markup=reply_markup
    )

async def button(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the translation mode."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_translation_mode[user_id] = query.data
    if query.data == "en_to_ku":
        await query.edit_message_text(text="Mode set: English → Kurdish Badini. Send me text, a photo, or a voice message to translate.")
    else:
        await query.edit_message_text(text="Mode set: Kurdish Badini → English. Send me text, a photo, or a voice message to translate.")

# --- Message Handlers ---
async def handle_text_message(update: Update, context: CallbackContext) -> None:
    """Translates a text message from the user."""
    user_id = update.message.from_user.id
    translation_mode = user_translation_mode.get(user_id, DEFAULT_MODE)
    translated_text = await translate_text(update.message.text, translation_mode)
    await update.message.reply_text(translated_text)

async def handle_photo_message(update: Update, context: CallbackContext) -> None:
    """Extracts text from a photo using OCR and translates it."""
    user_id = update.message.from_user.id
    translation_mode = user_translation_mode.get(user_id, DEFAULT_MODE)
    
    photo_file = await update.message.photo[-1].get_file()
    photo_path = f"{user_id}_photo.jpg"
    await photo_file.download_to_drive(photo_path)
    
    await update.message.reply_text("Processing image...")

    try:
        extracted_text = pytesseract.image_to_string(Image.open(photo_path))
        if extracted_text.strip():
            translated_text = await translate_text(extracted_text, translation_mode)
            await update.message.reply_text(f"Extracted Text:\n{extracted_text}\n\nTranslation:\n{translated_text}")
        else:
            await update.message.reply_text("Could not extract any text from the image.")
    except Exception as e:
        logger.error(f"Error during OCR: {e}")
        await update.message.reply_text("Sorry, I couldn't process the image.")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)

# --- Optional: Voice Message Support ---
# async def handle_voice_message(update: Update, context: CallbackContext) -> None:
#     """Transcribes a voice message and translates the text."""
#     user_id = update.message.from_user.id
#     translation_mode = user_translation_mode.get(user_id, DEFAULT_MODE)
#
#     voice_file = await update.message.voice.get_file()
#     voice_path = f"{user_id}_voice.ogg"
#     await voice_file.download_to_drive(voice_path)
#
#     await update.message.reply_text("Transcribing voice message...")
#
#     try:
#         client = speech.SpeechAsyncClient()
#         with open(voice_path, "rb") as audio_file:
#             content = audio_file.read()
#
#         audio = speech.RecognitionAudio(content=content)
#         config = speech.RecognitionConfig(
#             encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
#             sample_rate_hertz=48000,
#             language_code="en-US" if translation_mode == "en_to_ku" else "ku-IQ", # Adjust language codes as needed
#         )
#
#         response = await client.recognize(config=config, audio=audio)
#
#         if response.results:
#             transcript = response.results[0].alternatives[0].transcript
#             translated_text = await translate_text(transcript, translation_mode)
#             await update.message.reply_text(f"Transcript:\n{transcript}\n\nTranslation:\n{translated_text}")
#         else:
#             await update.message.reply_text("Could not transcribe the voice message.")
#     except Exception as e:
#         logger.error(f"Error during voice transcription: {e}")
#         await update.message.reply_text("Sorry, I couldn't process the voice message.")
#     finally:
#         if os.path.exists(voice_path):
#             os.remove(voice_path)

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    # Message Handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))
    
    # Optional: Voice Message Handler
    # application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))

    # Run the bot until you press Ctrl-C
    application.run_polling()

if __name__ == '__main__':
    main()
