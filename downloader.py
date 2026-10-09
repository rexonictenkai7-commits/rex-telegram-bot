import asyncio
import os
import re
from urllib.parse import urlparse
from typing import Callable, Optional, Dict, Any
import yt_dlp
from config import TEMP_DIR, YDL_OPTS_BASE, MAX_FILE_SIZE_MB


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
