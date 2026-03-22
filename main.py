import logging
import os
import yt_dlp
import time
import uuid

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8790787712:AAGWAo0Eghq9by6CQrhhe2bFpzVnqBu9sds"

# 🔥 ТВОЙ ПРОКСИ УЖЕ ВСТАВЛЕН
PROXY = "http://tjmkzqpt:175bx0de6sl7@31.59.20.176:6754"

logging.basicConfig(level=logging.INFO)


def detect_platform(url):
    if "instagram.com" in url:
        return "Instagram"
    elif "tiktok.com" in url:
        return "TikTok"
    elif "pinterest.com" in url:
        return "Pinterest"
    return None


def download_video(url):
    file_id = str(uuid.uuid4())

    ydl_opts = {
        "outtmpl": f"/tmp/{file_id}.mp4",
        "format": "best",
        "quiet": True,
        "noplaylist": True,
        "retries": 10,
        "fragment_retries": 10,
        "concurrent_fragment_downloads": 1,
        "http_chunk_size": 1048576,
        "nocheckcertificate": True,

        # 🔥 ПРОКСИ
        "proxy": PROXY,

        "http_headers": {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    for i in range(5):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)
        except Exception as e:
            print(f"Ошибка {i+1}:", e)
            time.sleep(2)

    raise Exception("Ошибка скачивания")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📥 Отправь ссылку:\n\n"
        "📸 Instagram\n"
        "🎵 TikTok\n"
        "📌 Pinterest"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    platform = detect_platform(url)

    if not platform:
        await update.message.reply_text("❌ Поддерживается только Instagram / TikTok / Pinterest")
        return

    msg = await update.message.reply_text(f"⏳ Скачиваю с {platform}...")

    try:
        file_path = download_video(url)

        size = os.path.getsize(file_path) / (1024 * 1024)

        if size > 45:
            await msg.edit_text("⚠️ Видео слишком большое (>50MB)")
        else:
            await msg.edit_text("📤 Отправляю...")
            with open(file_path, "rb") as f:
                await update.message.reply_video(video=f)

        os.remove(file_path)

    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {e}")


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Бот запущен!")
app.run_polling()
