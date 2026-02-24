# Installation

Getting Ana running locally takes about 10 minutes if you already have Python and API keys. Let's not waste those 10 minutes.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.10+ | Check with `python --version` |
| pip | Should come with Python |
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

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs 5 packages:
- `discord.py` — Discord gateway integration
- `flask>=3.0.0` — Keepalive web server
- `python-dotenv>=1.0.0` — `.env` file loading
- `requests>=2.32.0` — HTTP calls to joke and Gemini APIs
- `groq>=1.0.0` — Groq Python client

Using a virtual environment is recommended but not required:

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

---

## Step 3: Create a Discord Bot

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. Click **New Application**, give it a name
3. Go to **Bot** tab → click **Add Bot**
4. Under **Token**, click **Reset Token** and copy it — this is your `DISCORD_TOKEN`
5. Under **Privileged Gateway Intents**, enable:
   - **Message Content Intent** — Ana needs to read messages to detect trigger words
6. Go to **OAuth2 → URL Generator**
   - Scopes: `bot`
   - Bot Permissions: `Send Messages`, `Read Message History`
7. Open the generated URL and add the bot to your server

---

## Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
touch .env
```

Fill it in:

```env
# Required
DISCORD_TOKEN=your_discord_bot_token_here
GROQ_API_KEY=your_groq_api_key_here

# Optional — Gemini fallbacks (highly recommended)
GEN1_API_KEY=your_gemini_gen1_api_key_here
GEN2_API_KEY=your_gemini_gen2_api_key_here

# Optional — tune joke behavior
JOKE_CHANCE=0.15
JOKE_COOLDOWN=60
JOKE_FETCH_TIMEOUT=8
```

**Important:** Never commit `.env` to git. It's already in `.gitignore` — don't accidentally remove that.

---

## Step 5: Run Ana

```bash
python main.py
```

You should see:

```
✅ Logged in as Ana#1234
```

If you see warnings like `⚠️ Warning: Missing GROQ_API_KEY`, that's expected if you haven't set those optional keys. The bot will still run with reduced functionality.

---

## Cloud Deployment

Ana is designed to run on always-on hosting. Popular options:

### Railway

1. Push to GitHub
2. Connect repo in Railway dashboard
3. Add environment variables in the Railway UI
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
