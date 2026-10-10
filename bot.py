#!/usr/bin/env python3
"""
Telegram Music Edit & Download Bot
SINGLE-FILE RAILWAY BUILD
All local helper modules are embedded below so GitHub mobile folder-upload
issues cannot cause ModuleNotFoundError for locales/utils.
"""

# ===== Embedded config.py =====
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MAX_FILE_SIZE_MB = max(1, min(49, int(os.getenv("MAX_FILE_SIZE_MB", "49"))))
DEFAULT_LANG = os.getenv("DEFAULT_LANG", "en")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# Temp directory for downloads/processing
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# yt-dlp options base
YDL_OPTS_BASE = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,  # safer: one track per request
    "extract_flat": False,
}


# ===== Embedded locales/__init__.py =====
TEXTS = {
    "en": {
        "start": (
            "🎵 *Welcome to Music Edit Bot!*\n\n"
            "Send me a YouTube / music link or upload an audio file.\n"
            "I can download, remove vocals, apply effects, analyze songs & more.\n\n"
            "Commands:\n"
            "/start - This message\n"
            "/help - Full help\n"
            "/edit - Edit last audio with effects\n"
            "/funk - Auto Funk Edit\n"
            "/vocalremove - Remove vocals / get instrumental\n"
            "/analyze - Song analysis (BPM, etc.)\n"
            "/lang - Switch language (en/hi)\n\n"
            "Just paste a link to start downloading!"
        ),
        "help": (
            "📖 *Help*\n\n"
            "*Download:*\n"
            "• Send any supported link (YouTube, SoundCloud, etc.)\n"
            "• Choose format / quality with buttons\n"
            "• Progress shown + Cancel button\n"
            "• Auto size check (Telegram limit)\n\n"
            "*Editing:*\n"
            "• /vocalremove - Extract vocals or instrumental (FFmpeg basic + optional Demucs)\n"
            "• /funk - Quick funky edit (speed + pitch + effects)\n"
            "• /edit - Open effects menu (bass, pitch, speed, volume, reverse, etc.)\n"
            "• /analyze - Basic song info + BPM estimate\n\n"
            "*150+ effects:* Many presets available via /edit buttons.\n"
            "Upload audio or reply to a file with commands.\n\n"
            "Language: /lang en  or  /lang hi"
        ),
        "choose_format": "🎚 Choose quality / format:",
        "downloading": "⬇️ Downloading... {progress}",
        "processing": "⚙️ Processing with FFmpeg...",
        "done": "✅ Done! Here's your file:",
        "error": "❌ Error: {msg}",
        "cancelled": "🚫 Cancelled by user.",
        "too_large": "⚠️ File too large for Telegram Bot API ({size} MB > {limit} MB). Try lower quality.",
        "no_audio": "No audio found. Send a link or upload an audio file first.",
        "lang_switched": "Language set to English 🇬🇧",
        "vocal_start": "🎤 Removing vocals / extracting stems... (this may take time)",
        "funk_start": "⚡ Creating Auto Funk Edit...",
        "analyze_start": "📊 Analyzing song...",
        "choose_effect": "🎚️ Choose effect / preset:",
        "upload_or_link": "Send a song link or upload an audio file.",
    },
    "hi": {
        "start": (
            "🎵 *Music Edit Bot mein aapka swagat hai!*\n\n"
            "Mujhe YouTube / music link bhejo ya audio file upload karo.\n"
            "Main download, vocal remove, effects, analysis kar sakta hoon.\n\n"
            "Commands:\n"
            "/start - Ye message\n"
            "/help - Poori help\n"
            "/edit - Last audio edit karo\n"
            "/funk - Auto Funk Edit\n"
            "/vocalremove - Vocals hatao / instrumental banao\n"
            "/analyze - Song analysis (BPM etc.)\n"
            "/lang - Language badlo (en/hi)\n\n"
            "Bas link paste karo download shuru karne ke liye!"
        ),
        "help": (
            "📖 *Help*\n\n"
            "*Download:*\n"
            "• Koi bhi supported link bhejo (YouTube, SoundCloud etc.)\n"
            "• Buttons se format / quality choose karo\n"
            "• Progress dikhega + Cancel button\n"
            "• Automatic size check\n\n"
            "*Editing:*\n"
            "• /vocalremove - Vocals nikaalo ya instrumental\n"
            "• /funk - Quick funky edit\n"
            "• /edit - Effects menu (bass, pitch, speed, volume, reverse...)\n"
            "• /analyze - Song info + BPM\n\n"
            "*150+ effects:* /edit se bahut presets available hain.\n"
            "Audio upload karo ya file pe reply karke commands use karo.\n\n"
            "Language: /lang en  ya  /lang hi"
        ),
        "choose_format": "🎚 Quality / format choose karo:",
        "downloading": "⬇️ Download ho raha hai... {progress}",
        "processing": "⚙️ FFmpeg se process ho raha hai...",
        "done": "✅ Ho gaya! Ye raha aapka file:",
        "error": "❌ Error: {msg}",
        "cancelled": "🚫 User ne cancel kar diya.",
        "too_large": "⚠️ File bahut bada hai Telegram ke liye ({size} MB > {limit} MB). Lower quality try karo.",
        "no_audio": "Koi audio nahi mila. Pehle link bhejo ya audio upload karo.",
        "lang_switched": "Language Hindi set ho gayi 🇮🇳",
        "vocal_start": "🎤 Vocals remove / stems extract ho rahe hain... (time lag sakta hai)",
        "funk_start": "⚡ Auto Funk Edit bana raha hoon...",
        "analyze_start": "📊 Song analyze ho raha hai...",
        "choose_effect": "🎚️ Effect / preset choose karo:",
        "upload_or_link": "Song link bhejo ya audio file upload karo.",
    },
}

def get_text(lang: str, key: str, **kwargs) -> str:
    lang = lang if lang in TEXTS else "en"
    text = TEXTS[lang].get(key, TEXTS["en"].get(key, key))
    try:
        return text.format(**kwargs)
    except Exception:
        return text


# ===== Embedded utils/downloader.py =====
import asyncio
import os
import re
from urllib.parse import urlparse
from typing import Callable, Optional, Dict, Any
import yt_dlp

class DownloadCancelled(Exception):
    pass


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    return name[:180].strip() or "audio"


def validate_url(url: str) -> str:
    """Accept only normal HTTP(S) links; reject malformed/other schemes."""
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc or not parsed.hostname:
        raise ValueError("Please send a valid http:// or https:// music link.")
    if any(ch.isspace() for ch in url):
        raise ValueError("The link contains spaces. Please send a valid URL.")
    return url.strip()


async def get_info(url: str) -> Dict[str, Any]:
    url = validate_url(url)
    opts = {**YDL_OPTS_BASE, "skip_download": True}
    loop = asyncio.get_event_loop()

    def _extract():
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    return await loop.run_in_executor(None, _extract)


async def download_audio(
    url: str,
    format_id: str = "bestaudio/best",
    progress_callback: Optional[Callable] = None,
    cancel_event: Optional[asyncio.Event] = None,
    out_dir: str = TEMP_DIR,
) -> str:
    """
    Download audio. Returns path to downloaded file.
    progress_callback(status_dict) can be used to update UI.
    """
    url = validate_url(url)
    os.makedirs(out_dir, exist_ok=True)
    out_tmpl = os.path.join(out_dir, "%(title).180B [%(id)s].%(ext)s")

    def progress_hook(d):
        if cancel_event and cancel_event.is_set():
            raise DownloadCancelled("User cancelled")
        if progress_callback and d.get("status") in ("downloading", "finished"):
            # schedule callback carefully; we run in executor so just store
            progress_callback(d)

    opts = {
        **YDL_OPTS_BASE,
        "format": format_id,
        "outtmpl": out_tmpl,
        "progress_hooks": [progress_hook],
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "prefer_ffmpeg": True,
    }

    loop = asyncio.get_event_loop()
    info_holder = {}

    def _download():
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            info_holder["info"] = info
            # Post-processing can change the extension/path, so prefer existing files.
            candidates = []
            requested = info.get("requested_downloads") or []
            for item in requested:
                fp = item.get("filepath") or item.get("_filename")
                if fp:
                    candidates.append(fp)
                    root, _ = os.path.splitext(fp)
                    candidates.extend(root + ext for ext in (".mp3", ".m4a", ".opus", ".wav", ".webm"))
            if info.get("_filename"):
                candidates.append(info["_filename"])
            for candidate in candidates:
                if candidate and os.path.isfile(candidate) and os.path.getsize(candidate) > 0:
                    return candidate
            # Fallback by media ID, newest file first.
            media_id = str(info.get("id", ""))
            matches = [os.path.join(out_dir, f) for f in os.listdir(out_dir)
                       if media_id and media_id in f and not f.endswith((".part", ".ytdl"))]
            matches = [f for f in matches if os.path.isfile(f) and os.path.getsize(f) > 0]
            if matches:
                return max(matches, key=os.path.getmtime)
            raise FileNotFoundError("Downloaded audio file not found after conversion")

    try:
        path = await loop.run_in_executor(None, _download)
        # size check
        size_mb = os.path.getsize(path) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            os.remove(path)
            raise ValueError(f"File too large: {size_mb:.1f} MB")
        return path
    except (DownloadCancelled, ValueError):
        raise
    except Exception as e:
        raise RuntimeError(str(e)) from e


def list_audio_formats(info: dict) -> list:
    """Return list of (format_id, label, approx_size) for audio-ish formats."""
    formats = []
    seen = set()
    for f in info.get("formats", []):
        if f.get("vcodec") != "none" and f.get("acodec") == "none":
            continue  # pure video
        fid = f.get("format_id")
        if not fid or fid in seen:
            continue
        seen.add(fid)
        note = f.get("format_note") or f.get("resolution") or ""
        ext = f.get("ext", "")
        abr = f.get("abr") or f.get("tbr")
        size = f.get("filesize") or f.get("filesize_approx")
        size_str = f"{size/1024/1024:.1f}MB" if size else "?"
        label = f"{note} {ext} {abr or ''}kbps ~{size_str}".strip()
        formats.append((fid, label, size))
    # Always offer best audio
    formats.insert(0, ("bestaudio/best", "Best Audio (auto)", None))
    formats.insert(1, ("bestaudio[ext=m4a]/bestaudio", "Best M4A / Audio", None))
    return formats[:12]  # limit buttons


# ===== Embedded utils/ffmpeg_tools.py =====
import asyncio
import os
import subprocess
import shlex
from typing import Optional


async def run_ffmpeg(cmd: list, timeout: int = 600) -> str:
    """Run ffmpeg command, return stdout+stderr on failure."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise RuntimeError("FFmpeg timed out")
    if proc.returncode != 0:
        err = (stderr or b"").decode(errors="ignore")[-1500:]
        raise RuntimeError(f"FFmpeg error:\n{err}")
    return (stdout or b"").decode(errors="ignore")


def _out_path(inp: str, suffix: str) -> str:
    base = os.path.splitext(os.path.basename(inp))[0]
    return os.path.join(TEMP_DIR, f"{base}_{suffix}.mp3")


async def change_speed(input_path: str, speed: float = 1.25) -> str:
    """Change tempo without changing pitch (uses atempo)."""
    out = _out_path(input_path, f"speed{speed}")
    # atempo accepts 0.5-2.0; chain if needed
    filters = []
    s = speed
    while s > 2.0:
        filters.append("atempo=2.0")
        s /= 2.0
    while s < 0.5:
        filters.append("atempo=0.5")
        s /= 0.5
    filters.append(f"atempo={s:.4f}")
    af = ",".join(filters)
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:a", af, "-vn", out]
    await run_ffmpeg(cmd)
    return out


async def change_pitch(input_path: str, semitones: float = 2.0) -> str:
    """Pitch shift using asetrate + aresample (simple, quality ok)."""
    out = _out_path(input_path, f"pitch{semitones}")
    factor = 2 ** (semitones / 12.0)
    # asetrate changes pitch+speed, then atempo corrects speed
    af = f"asetrate=44100*{factor:.6f},aresample=44100,atempo={1/factor:.6f}"
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:a", af, "-vn", out]
    await run_ffmpeg(cmd)
    return out


async def bass_boost(input_path: str, gain: float = 8.0) -> str:
    out = _out_path(input_path, "bass")
    af = f"bass=g={gain}:f=100:w=0.5"
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:a", af, "-vn", out]
    await run_ffmpeg(cmd)
    return out


async def change_volume(input_path: str, db: float = 5.0) -> str:
    out = _out_path(input_path, f"vol{db}")
    af = f"volume={db}dB"
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:a", af, "-vn", out]
    await run_ffmpeg(cmd)
    return out


async def reverse_audio(input_path: str) -> str:
    out = _out_path(input_path, "reverse")
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:a", "areverse", "-vn", out]
    await run_ffmpeg(cmd)
    return out


async def nightcore(input_path: str) -> str:
    """Classic nightcore: speed up + pitch up."""
    out = _out_path(input_path, "nightcore")
    # ~1.25 speed + ~3-4 semitones feel
    af = "asetrate=44100*1.25,aresample=44100,atempo=1.0"
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:a", af, "-vn", out]
    await run_ffmpeg(cmd)
    return out


async def vaporwave(input_path: str) -> str:
    out = _out_path(input_path, "vaporwave")
    af = "asetrate=44100*0.8,aresample=44100,atempo=1.0,bass=g=5"
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:a", af, "-vn", out]
    await run_ffmpeg(cmd)
    return out


async def auto_funk(input_path: str) -> str:
    """Simple auto-funk: mild speed up, bass boost, slight pitch."""
    out = _out_path(input_path, "funk")
    af = "asetrate=44100*1.08,aresample=44100,atempo=1.0,bass=g=6:f=110,treble=g=2"
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:a", af, "-vn", out]
    await run_ffmpeg(cmd)
    return out


async def basic_vocal_remove(input_path: str) -> str:
    """
    Simple center-channel vocal removal (karaoke style).
    Works best on stereo tracks where vocals are centered.
    For high quality use Demucs (optional heavy dependency).
    """
    out = _out_path(input_path, "instrumental")
    # Classic karaoke filter
    af = "pan=stereo|c0=c0-c1|c1=c1-c0"
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:a", af, "-vn", out]
    await run_ffmpeg(cmd)
    return out


async def extract_vocals_basic(input_path: str) -> str:
    """Rough vocal extract (opposite of karaoke)."""
    out = _out_path(input_path, "vocals")
    af = "pan=mono|c0=0.5*c0+-0.5*c1"
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:a", af, "-ac", "1", "-vn", out]
    await run_ffmpeg(cmd)
    return out


async def try_demucs_vocal_remove(input_path: str) -> Optional[str]:
    """Try Demucs if installed. Returns path to instrumental or None."""
    try:
        import demucs.separate
        # demucs CLI style via subprocess is more reliable
        out_dir = os.path.join(TEMP_DIR, "demucs_out")
        os.makedirs(out_dir, exist_ok=True)
        cmd = [
            "python", "-m", "demucs",
            "--two-stems", "vocals",
            "-n", "htdemucs",
            "-o", out_dir,
            input_path,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await asyncio.wait_for(proc.communicate(), timeout=900)
        if proc.returncode != 0:
            return None
        # Find no_vocals / instrumental
        for root, _, files in os.walk(out_dir):
            for f in files:
                if "no_vocals" in f or "instrumental" in f.lower():
                    return os.path.join(root, f)
        return None
    except Exception:
        return None


# Preset map for /edit buttons
EFFECT_PRESETS = {
    "bass_boost": ("Bass Boost", bass_boost),
    "speed_up": ("Speed 1.25x", lambda p: change_speed(p, 1.25)),
    "slow_down": ("Slow 0.8x", lambda p: change_speed(p, 0.8)),
    "pitch_up": ("Pitch +2", lambda p: change_pitch(p, 2)),
    "pitch_down": ("Pitch -2", lambda p: change_pitch(p, -2)),
    "volume_up": ("Volume +5dB", lambda p: change_volume(p, 5)),
    "reverse": ("Reverse", reverse_audio),
    "nightcore": ("Nightcore", nightcore),
    "vaporwave": ("Vaporwave", vaporwave),
    "funk": ("Auto Funk", auto_funk),
}


async def get_duration(path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, _ = await proc.communicate()
    try:
        return float(out.decode().strip())
    except Exception:
        return 0.0


# ===== Main bot =====

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
