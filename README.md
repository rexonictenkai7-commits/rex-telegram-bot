# 🎵 Telegram Music Edit & Download Bot

Python Telegram bot with:

- Link download (yt-dlp) → format / quality buttons
- File size check + basic progress + Cancel button
- Single-track link handling (playlists are disabled to reduce accidental bulk downloads)
- Hindi / English interface (`/lang hi` or `/lang en`)
- Song upload or link
- Vocal remove / instrumental (basic FFmpeg karaoke + optional high-quality Demucs)
- Auto Funk Edit
- Bass, pitch, speed, volume, reverse, nightcore, vaporwave & more effects
- `/edit` preset buttons
- `/analyze` basic song info
- Commands: `/start` `/help` `/edit` `/funk` `/vocalremove` `/analyze` `/lang`
- Inline buttons
- FFmpeg-based processing

> **Note:** Full “150+ effects” and perfect AI vocal separation need extra heavy models (Demucs + PyTorch).  
> This package gives you a **working core** that is easy to extend. Real-time progress bars and perfect playlist UX can be improved further.

## Requirements

- Python 3.10+
- FFmpeg & FFprobe installed and in `PATH`
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### Install system packages

**Ubuntu / Debian:**
```bash
sudo apt update
sudo apt install -y ffmpeg python3-pip python3-venv
```

**Windows:**  
Download FFmpeg from https://ffmpeg.org and add to PATH.

## Quick Start

```bash
# 1. Unzip and enter folder
cd telegram_music_bot

# 2. Create virtual environment (recommended)
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Edit .env and put your BOT_TOKEN=...

# 5. Run
python bot.py
```

## Docker deployment

The included `Dockerfile` installs FFmpeg and Python dependencies. Set `BOT_TOKEN` as an environment variable in your hosting dashboard; do not commit `.env` or your token. The included `Procfile` is for platforms that support worker processes.

## Optional: High-quality Vocal Removal (Demucs)

```bash
pip install demucs torch torchaudio
# First run will download ~80-300 MB models
```

Then `/vocalremove` will automatically prefer Demucs when available.

## Optional: Better Analysis (BPM etc.)

```bash
pip install librosa soundfile numpy
```

Then you can extend `analyze_cmd` in `bot.py` with librosa.beat.beat_track.

## How to use

1. Start the bot → `/start`
2. Send a YouTube / SoundCloud / supported link  
   → Bot shows format buttons  
   → Choose quality  
   → File is downloaded & sent (size checked)
3. Or upload an audio / voice file
4. Then use:
   - `/vocalremove` – instrumental / karaoke style
   - `/funk` – auto funky edit
   - `/edit` – choose from presets (bass, pitch, speed…)
   - `/analyze` – duration & size
5. Switch language: `/lang hi` or `/lang en`

## Project structure

```
telegram_music_bot/
├── bot.py                 # Main bot
├── config.py
├── requirements.txt
├── .env.example
├── locales/               # English + Hindi texts
├── utils/
│   ├── downloader.py      # yt-dlp wrapper
│   └── ffmpeg_tools.py    # All FFmpeg effects
└── temp/                  # Created automatically (downloads & processed files)
```

## Extending to 150+ effects

Look at `utils/ffmpeg_tools.py` → `EFFECT_PRESETS`.  
Add more FFmpeg filter chains (echo, reverb, chorus, compressor, EQ bands, distortion, etc.) and register them in the dict.  
The `/edit` buttons are generated automatically.

## Limitations & Notes

- Telegram Bot API free limit ≈ 50 MB. For larger files you need a local Bot API server.
- Progress updates are basic (can be improved with a background task + queue).
- Playlist of 100+ songs will take long and may hit rate limits / disk space.
- Center-channel vocal remove works best on stereo mixes where vocals are centered. Demucs is much better.
- Always respect copyright and platform Terms of Service. This bot is for personal / educational use.

## License

MIT – do whatever you want, just don’t blame the author.

Enjoy editing! 🎧
