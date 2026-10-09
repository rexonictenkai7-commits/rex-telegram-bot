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
