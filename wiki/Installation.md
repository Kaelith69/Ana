# Installation

Getting Ana running locally takes about 10 minutes if you already have Python and API keys.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.10+ | Check with `python --version` |
| pip | Comes with Python |
| Discord bot token | From [Discord Developer Portal](https://discord.com/developers/applications) |
| Groq API key | From [console.groq.com](https://console.groq.com) — free tier available |
| Gemini API keys | From [aistudio.google.com](https://aistudio.google.com) — optional but recommended for fallbacks |

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/Kaelith69/Ana.git
cd Ana
```

---

## Step 2: Create a Virtual Environment and Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate   # Linux / macOS / Raspberry Pi
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

This installs 5 packages: `discord.py`, `flask`, `python-dotenv`, `requests`, `groq`.

---

## Step 3: Create a Discord Bot

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. Click **New Application**, give it a name
3. Go to **Bot** tab → click **Add Bot**
4. Under **Token**, click **Reset Token** and copy it — this is your `DISCORD_TOKEN`
5. Under **Privileged Gateway Intents**, enable **Message Content Intent** — Ana needs this to read message text
6. Go to **OAuth2 → URL Generator**:
   - Scopes: `bot`
   - Bot Permissions: `Send Messages`, `Read Message History`, `Add Reactions`
7. Open the generated URL and add the bot to your server

---

## Step 4: Configure Environment Variables

Copy the provided template:

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```env
# Required
DISCORD_TOKEN=your_discord_bot_token_here
GROQ_API_KEY=your_groq_api_key_here

# Optional — Gemini fallbacks (highly recommended)
# GEN1_API_KEY: used as first AI fallback after Groq waterfall
# GEN2_API_KEY: used as second AI fallback + profile extraction + reminder parsing/wishes
GEN1_API_KEY=your_gemini_gen1_api_key_here
GEN2_API_KEY=your_gemini_gen2_api_key_here

# Optional — tune behaviour
JOKE_CHANCE=0.15          # 0.0–1.0 probability per untriggered message
JOKE_COOLDOWN=60          # Seconds between jokes in the same channel
JOKE_FETCH_TIMEOUT=8      # HTTP timeout for icanhazdadjoke.com

# Optional — override Ana's entire personality
# SYSTEM_PROMPT=you are ana, a ...
```

> **Never commit `.env` to git.** It's already in `.gitignore`. The `.env.example` file (no real keys) is safe to commit and is included in the repo as a reference.

> **Note:** Ana automatically creates `data/profiles/` and `data/reminders/` directories on first use. No manual directory setup is required. See the [Privacy](Privacy) page for what's stored there.

---

## Step 5: Run Ana

```bash
python main.py
```

You should see:
```
✅ Logged in as Ana#1234
```

If you see `⚠️ Warning: Missing GROQ_API_KEY`, the bot will still run but fall through to Gemini or the static fallback for AI replies.

---

## Raspberry Pi Autostart

To have Ana start automatically on every reboot, run the included setup script **once**:

```bash
chmod +x setup_autostart.sh && ./setup_autostart.sh
```

The script:
- Creates a `.venv/` virtualenv and installs dependencies
- Writes a systemd service file at `/etc/systemd/system/ana-bot.service`
- Configures `After=network-online.target` — waits for internet before starting
- Enables the service to start on every boot
- Starts it immediately

**Useful commands after setup:**

```bash
journalctl -u ana-bot -f           # live logs
journalctl -u ana-bot -n 100       # last 100 log lines
sudo systemctl restart ana-bot     # after pulling code changes
sudo systemctl stop ana-bot        # take her offline
sudo systemctl disable ana-bot     # remove from autostart
sudo rm /etc/systemd/system/ana-bot.service && sudo systemctl daemon-reload  # full removal
```

> **Requirements:** Raspberry Pi OS (Bullseye or later), Python 3.10+, `.env` file present in the repo directory with your keys.

---

## Cloud Deployment

Ana's keepalive server on `:8080` satisfies health-check requirements for all major free-tier platforms.

### Railway
1. Push to GitHub
2. Connect repo in Railway dashboard
3. Add environment variables in the Railway UI (do not upload `.env`)

### Render
1. Create a new Web Service, connect your GitHub repo
2. Set Build Command: `pip install -r requirements.txt`
3. Set Start Command: `python main.py`
4. Add environment variables in the Render dashboard

### Replit
1. Import from GitHub
2. Add secrets in the Replit Secrets panel
3. Set the run command to `python main.py`
4. Use an uptime monitor to ping the `:8080` endpoint so Replit doesn't sleep the repl

4. Railway detects Python and runs `python main.py` automatically

### Render

1. Create a new Web Service (yes, even though it's a bot — the Flask server handles health checks)
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `python main.py`
4. Add environment variables

### Replit

1. Import the repo
2. Add secrets in the Replit Secrets panel
3. Run — Replit's "Always On" feature keeps it alive

The Flask keepalive server on port 8080 is specifically designed to keep the bot alive on platforms that sleep idle processes.

---

## Verification

After starting, confirm everything works:

1. Send `hello` in any channel the bot can see — it should reply
2. Send `!joke` — it should fetch a dad joke
3. Check the terminal — you should see Groq/AI output logged

If Ana isn't responding, check [Troubleshooting](Troubleshooting).
