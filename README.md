# Ana

Ana is a Discord chatbot built with Python. It uses a multi-model AI fallback pipeline, per-channel conversation context, personality prompts, and lightweight human-behavior simulation.

## Repository map

- main.py: Discord event loop, trigger detection, cooldowns, command handlers.
- nlp.py: Groq waterfall, Gemini fallbacks, response normalization.
- profiles.py: per-user JSON profile storage and fact extraction merge.
- jokes.py: random dad-joke delivery with cooldown and daily cap.
- config.py: env loading, defaults, trigger words, model settings.
- keepalive.py: Flask health endpoint on port 8080.
- setup_autostart.sh: Raspberry Pi systemd setup.

## Runtime flow

1. on_message receives Discord events in main.py.
2. Mode resolves to roast, flirt, normal trigger, or no-trigger.
3. Cooldown and behavior simulation logic runs.
4. NLP generation is executed with asyncio.to_thread.
5. nlp.py attempts Groq models, then Gemini Gen1, then Gemini Gen2, then static fallback.
6. Reply is normalized and sent, optional follow-up may be sent.
7. Profile extraction runs in background and updates data/profiles files.

## Implemented behavior values

- Per-user cooldown: 25 seconds.
- Per-channel cooldown: 7 seconds.
- Low-signal silent skip: 5 percent.
- Ghost typing then no message: 6 percent.
- Reaction overlay with text reply: 10 percent.
- Typo injection: 4 percent.
- Typo correction follow-up: 70 percent when typo happens.
- Roast follow-up: 25 percent.
- Flirt follow-up: 20 percent.
- Normal follow-up: 8 percent.

Notes:

- Emoji-only reply branch is not present.
- Roast mode bypasses cooldown gating.

## AI routing

Default Groq waterfall from config.py:

- moonshotai/kimi-k2-instruct
- llama-3.1-8b-instant
- llama-3.1-8b-instant (duplicate entry deduped at runtime)
- qwen/qwen3-32b

Fallback chain in nlp.py:

- gemini-1.5-flash-latest
- gemini-2.5-flash-lite
- static fallback responses

Key split behavior:

- GROQ_API_KEY is used for primary chat generation path.
- GROQ_BACKUP_API_KEY is reserved for profile-access classification path.

## Installation

1. Clone: git clone https://github.com/Kaelith69/Ana.git and cd Ana.
2. Create venv and install requirements.
3. Copy .env.example to .env and fill values.
4. Start with python main.py.

## Configuration guide

- DISCORD_TOKEN: required Discord token.
- GROQ_API_KEY: primary Groq key.
- GROQ_BACKUP_API_KEY: classifier Groq key.
- GEN1_API_KEY and GEN2_API_KEY: Gemini fallbacks and profile extraction.
- SYSTEM_PROMPT: optional inline prompt override.
- CHARACTER_PROFILE_PATH: optional prompt file path override.
- JOKE_CHANCE, JOKE_COOLDOWN, JOKE_FETCH_TIMEOUT, JOKE_API_URL: joke behavior controls.
- GROQ_MODEL_PRIMARY and GROQ_MODEL_BACKUP1 to 3: waterfall model overrides.

## API reference

- Discord command !joke in main.py.
- Discord command !shutdown in main.py.
- on_message event pipeline in main.py.
- HTTP GET / keepalive endpoint in keepalive.py.

## Module explanations

- main.py orchestrates the full runtime behavior.
- nlp.py handles model calls and output cleanup.
- profiles.py persists user facts in JSON and formats context.
- jokes.py controls random joke dispatch behavior.
- config.py centralizes env-driven configuration.
- keepalive.py provides health-check endpoint.

## Developer guide

Recommended checks after edits:

- python -m compileall .
- python smoke_test.py
- python -c "import config, jokes, profiles, nlp, keepalive, main; print('imports-ok')"

Notes:

- config.py loads .env with override=True.
- Long-run Discord behavior needs live-session verification.

## Wiki pages

- wiki/Home.md
- wiki/Architecture.md
- wiki/Installation.md
- wiki/Usage.md
- wiki/API-Reference.md
- wiki/Developer-Guide.md
- wiki/Privacy.md
- wiki/Troubleshooting.md
- wiki/Roadmap.md
