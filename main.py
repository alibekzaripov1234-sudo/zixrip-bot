import logging
import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = "8790787712:AAGWAo0Eghq9by6CQrhhe2bFpzVnqBu9sds"
CHANNEL = "@Zixrip_bot"  # замени на свой канал

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
    output_path = "/tmp/media.%(ext)s"
    if audio_only:
        ydl_opts = {
            "outtmpl": "/tmp/audio.%(ext)s",
            "format": "bestaudio/best",
            "quiet": True,
            "noplaylist": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
            }],
        }
    else:
        if quality == "high":
            fmt = "best[height<=1080][ext=mp4]/best[ext=mp4]/best"
        elif quality == "medium":
            fmt = "best[height<=480][ext=mp4]/best[ext=mp4]/best"
        else:
            fmt = "best[height<=360][ext=mp4]/best[ext=mp4]/best"
        ydl_opts = {
            "outtmpl": output_path,
            "format": fmt,
            "quiet": True,
            "noplaylist": True,
            "max_filesize": 50 * 1024 * 1024,
        }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if audio_only:
            return "/tmp/audio.mp3"
        ext = info.get("ext", "mp4")
        return f"/tmp/media.{ext}"

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

    context.user_data["url"] = url
    context.user_data["platform"] = platform

    keyboard = [
        [
            InlineKeyboardButton("🎵 MP3", callback_data="audio"),
            InlineKeyboardButton("📱 360p", callback_data="low"),
        ],
        [
            InlineKeyboardButton("📺 480p", callback_data="medium"),
            InlineKeyboardButton("🎬 1080p", callback_data="high"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"✅ Ссылка с {platform} получена!\nВыбери формат:",
        reply_markup=reply_markup
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = context.user_data.get("url")
    platform = context.user_data.get("platform")
    choice = query.data

    if not url:
        await query.edit_message_text("❌ Отправь ссылку заново.")
        return

    audio_only = choice == "audio"
    quality = choice if not audio_only else "best"

    msg = await query.edit_message_text(f"⏳ Скачиваю с {platform}...")

    try:
        file_path = download_video(url, quality=quality, audio_only=audio_only)
        await msg.edit_text("📤 Отправляю...")

        with open(file_path, "rb") as f:
            if audio_only:
                await query.message.reply_audio(audio=f)
            else:
                await query.message.reply_video(video=f, supports_streaming=True)

        os.remove(file_path)
        await msg.delete()

        await query.message.reply_text(
            f"✅ Готово! Подпишись на наш канал 👉 {CHANNEL}"
        )

    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {str(e)}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_callback))
print("Бот запущен!")
app.run_polling()
