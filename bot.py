#!/usr/bin/env python3
"""
Telegram Music Edit & Download Bot
Features: link download with format buttons, progress, cancel,
vocal remove (basic + optional Demucs), funk edit, effects, analyze,
Hindi/English UI, FFmpeg based processing.
"""

import asyncio
import logging
import os
import time
from typing import Dict, Optional

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode

from config import BOT_TOKEN, TEMP_DIR, MAX_FILE_SIZE_MB, DEFAULT_LANG
from locales import get_text
from utils.downloader import get_info, download_audio, list_audio_formats, DownloadCancelled
from utils.ffmpeg_tools import (
    EFFECT_PRESETS,
    auto_funk,
    basic_vocal_remove,
    extract_vocals_basic,
    try_demucs_vocal_remove,
    get_duration,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Per-user state: last audio path, language, cancel events
user_data: Dict[int, dict] = {}


def get_user(uid: int) -> dict:
    if uid not in user_data:
        user_data[uid] = {
            "lang": DEFAULT_LANG,
            "last_audio": None,
            "cancel": None,
            "msg_id": None,
        }
    return user_data[uid]


def t(uid: int, key: str, **kwargs) -> str:
    return get_text(get_user(uid)["lang"], key, **kwargs)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("🎵 Music Download", callback_data="menu|download"),
         InlineKeyboardButton("🎚️ Audio Effects", callback_data="menu|edit")],
        [InlineKeyboardButton("🎤 Vocal Remove", callback_data="menu|vocalremove"),
         InlineKeyboardButton("⚡ Auto Funk", callback_data="menu|funk")],
        [InlineKeyboardButton("📊 Song Analysis", callback_data="menu|analyze"),
         InlineKeyboardButton("📖 Help / How to Use", callback_data="menu|help")],
        [InlineKeyboardButton("🌐 Hindi", callback_data="menu|lang_hi"),
         InlineKeyboardButton("🇬🇧 English", callback_data="menu|lang_en")],
    ]
    await update.message.reply_text(
        t(uid, "start"), parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    choice = query.data.split("|", 1)[1]
    if choice == "lang_hi":
        get_user(uid)["lang"] = "hi"
        await query.edit_message_text(t(uid, "start"), parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎵 Music Download", callback_data="menu|download"), InlineKeyboardButton("🎚️ Audio Effects", callback_data="menu|edit")],
                [InlineKeyboardButton("🎤 Vocal Remove", callback_data="menu|vocalremove"), InlineKeyboardButton("⚡ Auto Funk", callback_data="menu|funk")],
                [InlineKeyboardButton("📊 Song Analysis", callback_data="menu|analyze"), InlineKeyboardButton("📖 Help / How to Use", callback_data="menu|help")],
                [InlineKeyboardButton("🌐 Hindi", callback_data="menu|lang_hi"), InlineKeyboardButton("🇬🇧 English", callback_data="menu|lang_en")],
            ]))
        return
    if choice == "lang_en":
        get_user(uid)["lang"] = "en"
        await query.edit_message_text(t(uid, "start"), parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎵 Music Download", callback_data="menu|download"), InlineKeyboardButton("🎚️ Audio Effects", callback_data="menu|edit")],
                [InlineKeyboardButton("🎤 Vocal Remove", callback_data="menu|vocalremove"), InlineKeyboardButton("⚡ Auto Funk", callback_data="menu|funk")],
                [InlineKeyboardButton("📊 Song Analysis", callback_data="menu|analyze"), InlineKeyboardButton("📖 Help / How to Use", callback_data="menu|help")],
                [InlineKeyboardButton("🌐 Hindi", callback_data="menu|lang_hi"), InlineKeyboardButton("🇬🇧 English", callback_data="menu|lang_en")],
            ]))
        return
    messages = {
        "download": "🎵 Send a supported music URL in this chat. Then choose a format/quality button. Playlists are disabled.",
        "edit": "🎚️ First send a music link or upload an audio file, then send /edit to open effect presets.",
        "vocalremove": "🎤 First send/upload audio, then send /vocalremove to create a vocal-reduced/instrumental version.",
        "funk": "⚡ First send/upload audio, then send /funk to create an Auto Funk edit.",
        "analyze": "📊 First send/upload audio, then send /analyze for basic file/song information.",
        "help": t(uid, "help"),
    }
    await query.message.reply_text(messages.get(choice, t(uid, "help")), parse_mode=ParseMode.MARKDOWN)


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    choice = query.data.split("|", 1)[1]
    if choice == "lang_hi":
        get_user(uid)["lang"] = "hi"
        await query.edit_message_text(t(uid, "start"), parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎵 Music Download", callback_data="menu|download"), InlineKeyboardButton("🎚️ Audio Effects", callback_data="menu|edit")],
                [InlineKeyboardButton("🎤 Vocal Remove", callback_data="menu|vocalremove"), InlineKeyboardButton("⚡ Auto Funk", callback_data="menu|funk")],
                [InlineKeyboardButton("📊 Song Analysis", callback_data="menu|analyze"), InlineKeyboardButton("📖 Help / How to Use", callback_data="menu|help")],
                [InlineKeyboardButton("🌐 Hindi", callback_data="menu|lang_hi"), InlineKeyboardButton("🇬🇧 English", callback_data="menu|lang_en")],
            ]))
        return
    if choice == "lang_en":
        get_user(uid)["lang"] = "en"
        await query.edit_message_text(t(uid, "start"), parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎵 Music Download", callback_data="menu|download"), InlineKeyboardButton("🎚️ Audio Effects", callback_data="menu|edit")],
                [InlineKeyboardButton("🎤 Vocal Remove", callback_data="menu|vocalremove"), InlineKeyboardButton("⚡ Auto Funk", callback_data="menu|funk")],
                [InlineKeyboardButton("📊 Song Analysis", callback_data="menu|analyze"), InlineKeyboardButton("📖 Help / How to Use", callback_data="menu|help")],
                [InlineKeyboardButton("🌐 Hindi", callback_data="menu|lang_hi"), InlineKeyboardButton("🇬🇧 English", callback_data="menu|lang_en")],
            ]))
        return
    messages = {
        "download": "🎵 Send a supported music URL in this chat. Then choose a format/quality button. Playlists are disabled.",
        "edit": "🎚️ First send a music link or upload an audio file, then send /edit to open effect presets.",
        "vocalremove": "🎤 First send/upload audio, then send /vocalremove to create a vocal-reduced/instrumental version.",
        "funk": "⚡ First send/upload audio, then send /funk to create an Auto Funk edit.",
        "analyze": "📊 First send/upload audio, then send /analyze for basic file/song information.",
        "help": t(uid, "help"),
    }
    await query.message.reply_text(messages.get(choice, t(uid, "help")), parse_mode=ParseMode.MARKDOWN)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(
        t(uid, "help"), parse_mode=ParseMode.MARKDOWN
    )


async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    args = context.args
    if args and args[0].lower() in ("en", "hi"):
        get_user(uid)["lang"] = args[0].lower()
        await update.message.reply_text(t(uid, "lang_switched"))
    else:
        await update.message.reply_text("Usage: /lang en   or   /lang hi")


async def handle_link_or_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text links or audio/document uploads."""
    uid = update.effective_user.id
    msg = update.message

    # Uploaded audio / voice / document
    file_obj = None
    if msg.audio:
        file_obj = msg.audio
    elif msg.voice:
        file_obj = msg.voice
    elif msg.document and msg.document.mime_type and "audio" in msg.document.mime_type:
        file_obj = msg.document

    if file_obj:
        status = await msg.reply_text(t(uid, "processing"))
        try:
            tg_file = await file_obj.get_file()
            ext = "mp3"
            if file_obj.mime_type:
                if "ogg" in file_obj.mime_type:
                    ext = "ogg"
                elif "mpeg" in file_obj.mime_type or "mp3" in file_obj.mime_type:
                    ext = "mp3"
            path = os.path.join(TEMP_DIR, f"upload_{uid}_{int(time.time())}.{ext}")
            await tg_file.download_to_drive(path)
            get_user(uid)["last_audio"] = path
            await status.edit_text(t(uid, "done") + "\nUse /edit /funk /vocalremove /analyze")
        except Exception as e:
            await status.edit_text(t(uid, "error", msg=str(e)[:200]))
        return

    # Text link
    text = (msg.text or "").strip()
    if not text.startswith(("https://", "http://")):
        return  # ignore other text
    if len(text) > 2048:
        await msg.reply_text("❌ Link is too long.")
        return

    status = await msg.reply_text("🔍 Checking link...")
    try:
        info = await get_info(text)
        title = info.get("title", "Unknown")[:60]
        formats = list_audio_formats(info)
        keyboard = []
        row = []
        for i, (fid, label, _) in enumerate(formats):
            # callback: dl|format_id|url_hash or store url in context
            # Store url in user_data temporarily
            get_user(uid)["pending_url"] = text
            get_user(uid)["pending_info"] = info
            cb = f"fmt|{fid}"
            row.append(InlineKeyboardButton(label[:40], callback_data=cb))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_download")])
        await status.edit_text(
            f"🎵 *{title}*\n\n{t(uid, 'choose_format')}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except Exception as e:
        await status.edit_text(t(uid, "error", msg=str(e)[:300]))


async def format_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data

    if data == "cancel_download":
        u = get_user(uid)
        if u.get("cancel"):
            u["cancel"].set()
        await query.edit_message_text(t(uid, "cancelled"))
        return

    if not data.startswith("fmt|"):
        return

    format_id = data.split("|", 1)[1]
    url = get_user(uid).get("pending_url")
    if not url:
        await query.edit_message_text(t(uid, "error", msg="No pending URL"))
        return

    cancel_event = asyncio.Event()
    get_user(uid)["cancel"] = cancel_event

    progress_msg = await query.edit_message_text(t(uid, "downloading", progress="0%"))

    last_update = 0

    def progress_cb(d):
        nonlocal last_update
        now = time.time()
        if now - last_update < 2:
            return
        last_update = now
        # We cannot easily edit from thread; just log for now.
        # Real progress update would need a queue + background task.
        p = d.get("_percent_str", "?")
        logger.info(f"Progress: {p}")

    try:
        path = await download_audio(
            url,
            format_id=format_id,
            progress_callback=progress_cb,
            cancel_event=cancel_event,
        )
        get_user(uid)["last_audio"] = path
        size_mb = os.path.getsize(path) / (1024 * 1024)
        caption = f"{t(uid, 'done')}\nSize: {size_mb:.1f} MB"
        with open(path, "rb") as f:
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=f,
                caption=caption,
                title=os.path.basename(path)[:60],
            )
        await progress_msg.edit_text(t(uid, "done") + " Use /edit /funk /vocalremove")
    except DownloadCancelled:
        await progress_msg.edit_text(t(uid, "cancelled"))
    except ValueError as e:
        if "too large" in str(e).lower():
            await progress_msg.edit_text(
                t(uid, "too_large", size=str(e).split(":")[-1].strip(), limit=MAX_FILE_SIZE_MB)
            )
        else:
            await progress_msg.edit_text(t(uid, "error", msg=str(e)[:200]))
    except Exception as e:
        logger.exception("Download failed")
        await progress_msg.edit_text(t(uid, "error", msg=str(e)[:300]))
    finally:
        get_user(uid)["cancel"] = None


async def vocalremove_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    path = get_user(uid).get("last_audio")
    if not path or not os.path.exists(path):
        await update.message.reply_text(t(uid, "no_audio"))
        return

    status = await update.message.reply_text(t(uid, "vocal_start"))
    try:
        # Prefer Demucs if available
        result = await try_demucs_vocal_remove(path)
        if not result:
            result = await basic_vocal_remove(path)
            note = " (basic FFmpeg karaoke filter)"
        else:
            note = " (Demucs high quality)"

        get_user(uid)["last_audio"] = result
        with open(result, "rb") as f:
            await context.bot.send_audio(
                chat_id=update.effective_chat.id,
                audio=f,
                caption=t(uid, "done") + note,
            )
        await status.edit_text(t(uid, "done") + note)
    except Exception as e:
        await status.edit_text(t(uid, "error", msg=str(e)[:250]))


async def funk_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    path = get_user(uid).get("last_audio")
    if not path or not os.path.exists(path):
        await update.message.reply_text(t(uid, "no_audio"))
        return

    status = await update.message.reply_text(t(uid, "funk_start"))
    try:
        result = await auto_funk(path)
        get_user(uid)["last_audio"] = result
        with open(result, "rb") as f:
            await context.bot.send_audio(
                chat_id=update.effective_chat.id,
                audio=f,
                caption="⚡ Auto Funk Edit ready!",
            )
        await status.edit_text(t(uid, "done"))
    except Exception as e:
        await status.edit_text(t(uid, "error", msg=str(e)[:250]))


async def edit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    path = get_user(uid).get("last_audio")
    if not path or not os.path.exists(path):
        await update.message.reply_text(t(uid, "no_audio"))
        return

    keyboard = []
    row = []
    for key, (label, _) in EFFECT_PRESETS.items():
        row.append(InlineKeyboardButton(label, callback_data=f"fx|{key}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_effect")])

    await update.message.reply_text(
        t(uid, "choose_effect"),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def effect_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data

    if data == "cancel_effect":
        await query.edit_message_text(t(uid, "cancelled"))
        return

    if not data.startswith("fx|"):
        return

    key = data.split("|", 1)[1]
    if key not in EFFECT_PRESETS:
        await query.edit_message_text(t(uid, "error", msg="Unknown effect"))
        return

    path = get_user(uid).get("last_audio")
    if not path or not os.path.exists(path):
        await query.edit_message_text(t(uid, "no_audio"))
        return

    label, func = EFFECT_PRESETS[key]
    await query.edit_message_text(t(uid, "processing") + f"\n{label}")

    try:
        result = await func(path)
        get_user(uid)["last_audio"] = result
        with open(result, "rb") as f:
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=f,
                caption=f"✅ {label}",
            )
        await query.edit_message_text(t(uid, "done") + f" {label}")
    except Exception as e:
        await query.edit_message_text(t(uid, "error", msg=str(e)[:250]))


async def analyze_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    path = get_user(uid).get("last_audio")
    if not path or not os.path.exists(path):
        await update.message.reply_text(t(uid, "no_audio"))
        return

    status = await update.message.reply_text(t(uid, "analyze_start"))
    try:
        duration = await get_duration(path)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        # Basic analysis without librosa (to keep deps light)
        text = (
            f"📊 *Song Analysis*\n\n"
            f"• Duration: `{duration:.1f}` sec ({duration/60:.1f} min)\n"
            f"• Size: `{size_mb:.2f}` MB\n"
            f"• Path: `{os.path.basename(path)}`\n\n"
            f"_For advanced BPM / key detection install librosa and extend this command._"
        )
        await status.edit_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await status.edit_text(t(uid, "error", msg=str(e)[:200]))


def main():
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here_from_BotFather":
        raise SystemExit("ERROR: Set a valid BOT_TOKEN in .env (get it from @BotFather).")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern=r"^menu\|"))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("lang", lang_cmd))
    app.add_handler(CommandHandler("vocalremove", vocalremove_cmd))
    app.add_handler(CommandHandler("funk", funk_cmd))
    app.add_handler(CommandHandler("edit", edit_cmd))
    app.add_handler(CommandHandler("analyze", analyze_cmd))

    app.add_handler(CallbackQueryHandler(format_callback, pattern=r"^(fmt\||cancel_download)$"))
    app.add_handler(CallbackQueryHandler(effect_callback, pattern=r"^(fx\||cancel_effect)$"))

    app.add_handler(
        MessageHandler(
            (filters.TEXT & ~filters.COMMAND)
            | filters.AUDIO
            | filters.VOICE
            | filters.Document.AUDIO,
            handle_link_or_file,
        )
    )

    print("Bot starting... Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
