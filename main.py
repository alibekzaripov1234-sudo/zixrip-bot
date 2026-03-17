import logging
import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8790787712:AAGWAo0Eghq9by6CQrhhe2bFpzVnqBu9sds"

logging.basicConfig(level=logging.INFO)

def detect_platform(url):
    if "youtube.com" in url or "youtu.be" in url:
        return "YouTube"
    elif "instagram.com" in url:
        return "Instagram"
    elif "tiktok.com" in url:
        return "TikTok"
    return None

def download_video(url):
    output_path = "/tmp/video.mp4"
    ydl_opts = {
        "outtmpl": output_path,
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "noplaylist": True,
        "max_filesize": 50 * 1024 * 1024,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я скачиваю видео из:\n"
        "▶️ YouTube\n"
        "📸 Instagram\n"
        "🎵 TikTok\n\n"
        "Просто отправь мне ссылку на видео!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    platform = detect_platform(url)
    if not platform:
        await update.message.reply_text("❌ Не распознал ссылку.")
        return
    msg = await update.message.reply_text(f"⏳ Скачиваю видео с {platform}...")
    try:
        file_path = download_video(url)
        await msg.edit_text("📤 Отправляю видео...")
        with open(file_path, "rb") as video_file:
            await update.message.reply_video(video=video_file, supports_streaming=True)
        os.remove(file_path)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {str(e)}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
print("Бот запущен!")
app.run_polling()
