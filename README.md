
<div align="center">

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 180" width="700" height="180">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1a1a2e;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#16213e;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#7f5af0;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#2cb67d;stop-opacity:1" />
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <!-- Background -->
  <rect width="700" height="180" rx="18" fill="url(#bg)"/>
  <!-- Accent bar -->
  <rect x="0" y="152" width="700" height="6" rx="3" fill="url(#accent)"/>
  <!-- Bot icon circle -->
  <circle cx="80" cy="88" r="46" fill="none" stroke="url(#accent)" stroke-width="3" filter="url(#glow)"/>
  <text x="80" y="100" font-size="42" text-anchor="middle" font-family="Segoe UI Emoji,Apple Color Emoji,sans-serif" filter="url(#glow)">🤖</text>
  <!-- Title -->
  <text x="148" y="72" font-family="'Segoe UI',Arial,sans-serif" font-size="52" font-weight="800" fill="url(#accent)" filter="url(#glow)">Ana</text>
  <!-- Tagline -->
  <text x="148" y="104" font-family="'Segoe UI',Arial,sans-serif" font-size="18" fill="#fffffe" opacity="0.85">Your witty Discord companion — jokes, vibes &amp; AI replies</text>
  <!-- Version pill -->
  <rect x="148" y="116" width="82" height="24" rx="12" fill="#7f5af0" opacity="0.85"/>
  <text x="189" y="133" font-family="'Segoe UI',Arial,sans-serif" font-size="13" fill="#fffffe" text-anchor="middle">Discord Bot</text>
  <!-- MIT pill -->
  <rect x="238" y="116" width="60" height="24" rx="12" fill="#2cb67d" opacity="0.85"/>
  <text x="268" y="133" font-family="'Segoe UI',Arial,sans-serif" font-size="13" fill="#fffffe" text-anchor="middle">MIT</text>
</svg>

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-latest-5865F2?style=flat-square&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![Groq](https://img.shields.io/badge/Groq-Llama--4-FF6B35?style=flat-square&logo=llama&logoColor=white)](https://groq.com/)
[![Gemini](https://img.shields.io/badge/Gemini-Flash%20Lite-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-blue?style=flat-square)](#)

</div>

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Commands](#commands)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

| Feature | Description |
|---|---|
| 🤖 **AI Replies** | Groq Llama-4 (primary) with Gemini Flash Lite fallback chain |
| 😂 **Dad Jokes** | Live-fetched from [icanhazdadjoke.com](https://icanhazdadjoke.com/) with configurable chance & cooldown |
| 🎯 **Trigger Words** | Responds to greetings, emotions, celebrations, and slang |
| 🔄 **Fallback Chain** | Groq → Gemini Gen1 → Gemini Gen2 → static responses |
| 🌐 **Keepalive** | Flask endpoint on `:8080` for uptime monitors |
| ⚙️ **Configurable** | All tuning knobs live in `config.py` / `.env` |

---

## Architecture

```
User Message
     │
     ▼
Trigger Word? ──No──► maybe_send_joke() ──► process_commands()
     │
    Yes
     │
     ▼
process_with_nlp(text)
     │
     ├─► call_groq()          [Llama-4 via Groq]
     │       │ fail
     ├─► call_gemini(GEN1)    [Gemini Flash Lite]
     │       │ fail
     ├─► call_gemini(GEN2)    [Gemini 2.5 Flash Lite]
     │       │ fail
     └─► FALLBACK_RESPONSES   [static strings]
```

**Key design decisions:**
- **Single Groq client** — instantiated once at module load to avoid per-request overhead.
- **Shared `call_gemini()` helper** — Gen1 and Gen2 share identical streaming logic; only the model ID, API key, and log label differ.
- **No local joke cache** — jokes are fetched live from the API with a per-day cap (default 3) and cooldown (default 60 s) to prevent spam.
- **Fail-fast config** — missing `DISCORD_TOKEN` is caught in `main()` before `bot.run()` with a clear error message.

---

## Project Structure

```
Ana/
├── main.py            # Bot entry point: events, commands, routing
├── nlp.py             # AI reply chain (Groq + Gemini helpers)
├── jokes.py           # DadJokeService — live fetch, cooldown, daily cap
├── config.py          # Env-var loading, settings dataclasses
├── keepalive.py       # Flask keepalive server (port 8080)
├── requirements.txt   # Python dependencies
├── .env               # 🔒 Secrets — never commit this file
├── .gitignore
└── LICENSE
```

---

## Setup & Installation

### Prerequisites

- Python **3.10+**
- A Discord bot token with **Message Content Intent** enabled
- At least one API key: **Groq** (recommended), or a Google Gemini key

### 1 — Clone & install

```bash
git clone https://github.com/Kaelith69/Ana.git
cd Ana
pip install -r requirements.txt
```

### 2 — Create `.env`

```env
# Required
DISCORD_TOKEN=your_discord_bot_token

# AI backends (at least one recommended)
GROQ_API_KEY=your_groq_api_key
GEN1_API_KEY=your_gemini_api_key_for_gen1
GEN2_API_KEY=your_gemini_api_key_for_gen2

# Optional tuning
JOKE_CHANCE=0.15
JOKE_COOLDOWN=60
```

> ⚠️ **Never commit `.env`** — it is already in `.gitignore`.

### 3 — Run

```bash
python main.py
```

You should see:

```
✅ Logged in as Ana#1234
```

---

## Configuration

All settings can be overridden via environment variables:

| Variable | Default | Description |
|---|---|---|
| `DISCORD_TOKEN` | — | **Required.** Discord bot token |
| `GROQ_API_KEY` | — | Groq completions (Llama-4) |
| `GEN1_API_KEY` | — | Gemini Flash Lite (Gen1 fallback) |
| `GEN2_API_KEY` | — | Gemini 2.5 Flash Lite (Gen2 fallback) |
| `JOKE_CHANCE` | `0.15` | Probability of a random joke per message |
| `JOKE_COOLDOWN` | `60` | Min seconds between random jokes |
| `JOKE_FETCH_BATCH` | `25` | Batch size for joke fetching (unused in live mode) |
| `JOKE_FETCH_INTERVAL` | `3600` | Interval for background refreshes |
| `JOKE_FETCH_TIMEOUT` | `8` | HTTP timeout (s) for joke API |

---

## Usage

### Auto-replies

Send any message containing a trigger word and Ana will reply via the AI chain:

```
you: hey Ana, what's up?
Ana: Hey! Just here, vibing and ready to chat 😄
```

### Random jokes

Ana may spontaneously drop a dad joke (chance + cooldown controlled):

```
Ana: Why don't scientists trust atoms? Because they make up everything.
```

### Commands

| Command | Who | Description |
|---|---|---|
| `!joke` | Everyone | Immediately fetch and send a dad joke |
| `!shutdown` | Bot owner only | Gracefully shut down the bot |

---

> 💡 **Pro tip:** Drop a quirky GIF of a robot laughing right here to give the README some personality!
>
> *(Replace this line with your favourite reaction GIF — something like a robot doing a mic drop works great.)*

---

## Deployment

Ana is designed for always-on hosting (Railway, Render, Replit, Fly.io, etc.):

1. Set all environment variables in your platform's dashboard — **do not** use a committed `.env` file.
2. Ensure port **8080** is exposed; uptime monitors should `GET /` — response: `Bot is alive!`
3. Enable **Message Content Intent** in the [Discord Developer Portal](https://discord.com/developers/applications).

```bash
# Railway / Render start command
python main.py
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `❌ DISCORD_TOKEN is missing` | Add `DISCORD_TOKEN` to your `.env` or platform env vars |
| `⚠️ Missing GROQ_API_KEY` | Add `GROQ_API_KEY`; bot falls back to Gemini if absent |
| No AI replies | Check that at least one of `GROQ_API_KEY`, `GEN1_API_KEY`, or `GEN2_API_KEY` is set |
| No jokes appearing | Lower `JOKE_CHANCE`, reduce `JOKE_COOLDOWN`, or check network access to `icanhazdadjoke.com` |
| `ImportError: groq` | Run `pip install -r requirements.txt` — `groq` must be installed |
| Connection drops | Ensure your host keeps long-running processes alive and pings the Flask endpoint |

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

*Made with ❤️ and questionable humor*

---

> **Why do programmers prefer dark mode?**
> *Because light attracts bugs.* 🐛

</div>

