import logging
import os
import yt_dlp
import time
import uuid
import requests

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

logging.basicConfig(level=logging.INFO)


# ✅ только YouTube
def is_youtube(url):
    return "youtube.com" in url or "youtu.be" in url


# ☁️ облако
def upload_to_gofile(file_path):
    for _ in range(2):
        try:
            res = requests.get("https://api.gofile.io/getServer")
            if res.status_code != 200:
                continue

            server = res.json()["data"]["server"]

            with open(file_path, "rb") as f:
                upload = requests.post(
                    f"https://{server}.gofile.io/uploadFile",
                    files={"file": f}
                )

            return upload.json()["data"]["downloadPage"]

        except:
            time.sleep(2)

    return None


# 🔥 стабильный YouTube
def download_video(url, quality="best", audio_only=False):
    file_id = str(uuid.uuid4())

    if audio_only:
        fmt = "bestaudio/best"
    else:
        if quality == "high":
            fmt = "best[height<=720]"
        elif quality == "medium":
            fmt = "best[height<=480]"
        elif quality == "low":
            fmt = "best[height<=360]"
        else:
            fmt = "best[height<=720]"

    ydl_opts = {
        "outtmpl": f"/tmp/{file_id}.%(ext)s",
        "format": fmt,
        "quiet": True,
        "noplaylist": True,
        "retries": 10,
        "fragment_retries": 10,
        "nocheckcertificate": True,
        "merge_output_format": "mp4",
        "http_headers": {
            "User-Agent": "Mozilla/5.0",
        },
    }

    for i in range(5):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)
        except Exception as e:
            print(f"Ошибка попытка {i+1}:", e)
            time.sleep(3)

    raise Exception("Ошибка скачивания")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет!\n"
        "Я скачиваю видео только с YouTube 🎬\n\n"
        "Отправь ссылку!"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not is_youtube(url):
        await update.message.reply_text("❌ Поддерживается только YouTube")
        return

    context.user_data["url"] = url

    keyboard = [
        [
            InlineKeyboardButton("🎵 MP3", callback_data="audio"),
            InlineKeyboardButton("📱 360p", callback_data="low"),
        ],
        [
            InlineKeyboardButton("📺 480p", callback_data="medium"),
            InlineKeyboardButton("🎬 720p", callback_data="high"),
        ],
    ]

    await update.message.reply_text(
        "Выбери качество:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


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

        file_size = os.path.getsize(file_path) / (1024 * 1024)

        if file_size > 1900:
            await msg.edit_text("☁️ Загружаю в облако...")
            link = upload_to_gofile(file_path)
            os.remove(file_path)

            if not link:
                await query.message.reply_text(
                    "⚠️ Видео большое. Вот ссылка:\n" + url
                )
            else:
                await query.message.reply_text(
                    f"📦 Видео ({round(file_size)} MB)\n🔗 {link}"
                )
        else:
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
