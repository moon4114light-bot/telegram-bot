import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types
import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
أنت بوت تليجرام متعدد المهام. شخصيتك كالتالي:
عصبي، انفعالي، بارد، مجنون، فاهي، فكاهي، يمزح، عنيد، وشويتين رومنسي.
تتكلم في أي موضوع وبدون حدود معقدة، لكن يمنع منعاً باتاً: القتل، العنف الشديد، والإساءات اللفظية القبيحة جداً.

مهامك التي تنفذها بأسلوب شخصيتك:
1. المساعدة في تصميم وتنسيق الألوان والأشياء العامة.
2. السوالف المباشرة كأنك إنسان.
3. الترجمة وتعليم اللغات.
4. تقديم النصائح.

ملاحظة: إذا طلب المستخدم منك إنشاء أو تصميم صورة، قم بوصف الصورة المطلوبة بدقة باللغة الإنجليزية واكتب في بداية ردك كلمة [IMAGE_PROMPT] متبوعة بالوصف.
"""

user_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chats[user_id] = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=1.0,
        )
    )
    await update.message.reply_text("أهلاً.. وش تبي؟ خلصني بسرعة.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_chats:
        user_chats[user_id] = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=1.0,
            )
        )

    chat = user_chats[user_id]

    try:
        response = chat.send_message(text)
        response_text = response.text

        if response_text.startswith("[IMAGE_PROMPT]"):
            image_prompt = response_text.replace("[IMAGE_PROMPT]", "").strip()
            await update.message.reply_text("دقيقة أقعد أصمم لك..")

            result = client.models.generate_images(
                model='imagen-3.0-generate-002',
                prompt=image_prompt,
                config=types.GenerateImagesConfig(number_of_images=1)
            )

            for generated_image in result.generated_images:
                await update.message.reply_photo(photo=generated_image.image.image_bytes)
        else:
            await update.message.reply_text(response_text)

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("صار خطأ أو إنك غثيت السيرفر، جرب مرة ثانية.")

async def send_audio_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_chats:
        chat = user_chats[user_id]
        response = chat.send_message("تكلم معي بصوت، أرسل لي ملاحظة صوتية قصيرة بأسلوبك العصبي والمجنون.")
        await update.message.reply_text(f"🔊 (رسالة صوتية): {response.text}")
    else:
        await update.message.reply_text("سولف معي أول عشان أرسل لك صوت!")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("voice", send_audio_note))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("البوت شغال...")
    app.run_polling()
