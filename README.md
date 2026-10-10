# Telegram Music Edit & Download Bot — Railway build

This is a single-file deployment build: `bot.py` contains the bot and helper code, so the `locales` and `utils` folders are not required.

## Deploy from a phone

1. Download and extract this ZIP on your phone.
2. In GitHub, open your repository and upload the **contents** of the extracted folder (not the ZIP file itself). The repository root should contain `bot.py`, `requirements.txt`, `Dockerfile`, `Procfile`, and `.env.example`.
3. In Railway, open the service connected to that GitHub repository, then open **Variables**.
4. Add a variable with name `BOT_TOKEN` and value equal to the full token from `@BotFather`. Save/check the variable.
5. Apply/deploy the staged changes or redeploy the latest deployment.
6. Open the latest deployment logs. If it starts successfully, open your bot in Telegram and send `/start`.

## Secret safety

- Do **not** paste the actual token into `bot.py`, `.env.example`, README, or any GitHub file.
- Do **not** send the token in chat or screenshots.
- Keep the real token only in Railway Variables (or a local untracked `.env` file).
- If a token was ever published publicly, revoke it with `@BotFather` and generate a replacement.

## Runtime

The Dockerfile installs FFmpeg and Python dependencies. Railway can also use the included `Procfile` (`worker: python bot.py`).
