# Installation

## Prerequisites

- Python 3.10+
- Discord bot token
- At least one Groq API key
- Optional Gemini API keys for fallback and profile extraction

## Setup

1. Clone repository:
   - git clone https://github.com/Kaelith69/Ana.git
   - cd Ana
2. Create virtual environment and install dependencies:
   - python -m venv .venv
   - Windows: .venv\\Scripts\\activate
   - Linux/macOS: source .venv/bin/activate
   - pip install -r requirements.txt
3. Create .env:
   - copy .env.example to .env
4. Fill required values:
   - DISCORD_TOKEN
   - GROQ_API_KEY
5. Start bot:
   - python main.py

## Optional keys and behavior

- GROQ_BACKUP_API_KEY: used for classifier path in nlp.py
- GEN1_API_KEY and GEN2_API_KEY: Gemini fallbacks
- JOKE_CHANCE, JOKE_COOLDOWN, JOKE_FETCH_TIMEOUT, JOKE_API_URL

## Raspberry Pi autostart

Run setup_autostart.sh once from repository root. It creates .venv, installs dependencies, writes a systemd service, enables autostart, and starts the bot.
