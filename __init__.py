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
