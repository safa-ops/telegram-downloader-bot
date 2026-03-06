import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# يفضل وضع التوكن في Variables المنصة
TOKEN = os.getenv("BOT_TOKEN", 8625967612:AAEM2vy2b7PTupjfIaZgLmarjJQZccHBEdI)
links = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل أي رابط (Instagram / TikTok / YouTube)")

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.message.chat_id
    links[chat_id] = url
    keyboard = [[InlineKeyboardButton("🎥 Video", callback_data="video"),
                 InlineKeyboardButton("🎵 Audio", callback_data="audio")]]
    await update.message.reply_text("اختر الصيغة:", reply_markup=InlineKeyboardMarkup(keyboard))

async def choose_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    url = links.get(chat_id)

    # استخراج المعلومات بدون تحميل
    with yt_dlp.YoutubeDL({}) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get("title", "No Title")
        thumbnail = info.get("thumbnail")
        size = info.get("filesize") or info.get("filesize_approx")
        size_mb = round(size / (1024*1024), 2) if size else "Unknown"

    text = f"العنوان: {title}\nالحجم: {size_mb} MB"
    if thumbnail:
        await query.message.reply_photo(photo=thumbnail, caption=text)
    else:
        await query.message.reply_text(text)

    if query.data == "audio":
        await download_audio(query, url)
    else:
        keyboard = [[InlineKeyboardButton("720p", callback_data="720"),
                     InlineKeyboardButton("480p", callback_data="480")]]
        await query.message.reply_text("اختر الدقة:", reply_markup=InlineKeyboardMarkup(keyboard))

async def choose_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    quality = query.data
    url = links.get(query.message.chat_id)
    await download_video(query, url, quality)

async def download_video(query, url, quality):
    await query.message.reply_text("جاري تحميل الفيديو...")
    ydl_opts = {
        'format': f'bestvideo[height<={quality}]+bestaudio/best',
        'outtmpl': 'video.%(ext)s',
        'merge_output_format': 'mp4',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    # البحث عن الملف الفعلي (لان الامتداد قد يختلف)
    filename = "video.mp4"
    await query.message.reply_video(video=open(filename, 'rb'))
    os.remove(filename)

async def download_audio(query, url):
    await query.message.reply_text("جاري تحميل الصوت...")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    filename = "audio.mp3"
    await query.message.reply_audio(audio=open(filename, 'rb'))
    os.remove(filename)

if name == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_link))
    app.add_handler(CallbackQueryHandler(choose_format, pattern="video|audio"))
    app.add_handler(CallbackQueryHandler(choose_quality, pattern="720|480"))
    app.run_polling()
