import logging
import os
import yt_dlp
import time
import uuid

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

BOT_TOKEN = "8790787712:AAGWAo0Eghq9by6CQrhhe2bFpzVnqBu9sds"
CHANNEL = "@Zixrip_bot"

logging.basicConfig(level=logging.INFO)


def detect_platform(url):
    if "youtube.com" in url or "youtu.be" in url:
        return "YouTube"
    elif "instagram.com" in url:
        return "Instagram"
    elif "tiktok.com" in url:
        return "TikTok"
    return None


def download_video(url, quality="best", audio_only=False):
    file_id = str(uuid.uuid4())

    if audio_only:
        out = f"/tmp/{file_id}.%(ext)s"
        ydl_opts = {
            "outtmpl": out,
            "format": "bestaudio/best",
            "quiet": True,
            "noplaylist": True,
            "retries": 5,
            "nocheckcertificate": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                }
            ],
        }
    else:
        if quality == "high":
            fmt = "bestvideo[height<=1080]+bestaudio/best"
        elif quality == "medium":
            fmt = "bestvideo[height<=480]+bestaudio/best"
        elif quality == "low":
            fmt = "bestvideo[height<=360]+bestaudio/best"
        else:
            fmt = "bestvideo+bestaudio/best"

        out = f"/tmp/{file_id}.%(ext)s"
        ydl_opts = {
            "outtmpl": out,
            "format": fmt,
            "quiet": True,
            "noplaylist": True,
            "retries": 5,
            "nocheckcertificate": True,
            "merge_output_format": "mp4",
            "http_headers": {
                "User-Agent": "Mozilla/5.0"
            },
        }

    for i in range(3):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)

                if audio_only:
                    file_path = file_path.replace(".webm", ".mp3").replace(".m4a", ".mp3")

                return file_path
        except Exception as e:
            print(f"Ошибка попытка {i+1}:", e)
            time.sleep(2)

    raise Exception("Не удалось скачать")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я скачиваю видео из:\n"
        "▶️ YouTube\n"
        "📸 Instagram\n"
        "🎵 TikTok\n\n"
        "Отправь ссылку!"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    platform = detect_platform(url)

    if not platform:
        await update.message.reply_text("❌ Не распознал ссылку")
        return

    context.user_data["url"] = url
    context.user_data["platform"] = platform

    if platform == "YouTube":
        keyboard = [
            [
                InlineKeyboardButton("🎵 MP3", callback_data="audio"),
                InlineKeyboardButton("📱 360p", callback_data="low"),
            ],
            [
                InlineKeyboardButton("📺 480p", callback_data="medium"),
                InlineKeyboardButton("🎬 1080p", callback_data="high"),
            ],
        ]
        await update.message.reply_text(
            "Выбери качество:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        msg = await update.message.reply_text(f"⏳ Скачиваю с {platform}...")
        try:
            file_path = download_video(url)
            await msg.edit_text("📤 Отправляю...")
            with open(file_path, "rb") as f:
                await update.message.reply_video(video=f, supports_streaming=True)
            os.remove(file_path)
            await msg.delete()
        except Exception as e:
            await msg.edit_text(f"❌ Ошибка: {e}")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = context.user_data.get("url")
    choice = query.data

    msg = await query.edit_message_text("⏳ Скачиваю...")

    try:
        file_path = download_video(
            url,
            quality=choice,
            audio_only=(choice == "audio"),
        )

        await msg.edit_text("📤 Отправляю...")

        with open(file_path, "rb") as f:
            if choice == "audio":
                await query.message.reply_audio(audio=f)
            else:
                await query.message.reply_video(video=f, supports_streaming=True)

        os.remove(file_path)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {e}")


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_callback))

print("Бот запущен!")
app.run_polling()
