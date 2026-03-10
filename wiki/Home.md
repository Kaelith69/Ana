# Ana Wiki — Home

Welcome to the Ana documentation wiki.

---

## What is Ana?

Ana is a **Discord bot** built in Python, designed to be indistinguishable from a real server member. She does several things well:

1. **Talks back** — scans messages for 100+ trigger words and generates AI replies via a cascading AI waterfall (Kimi K2 → Llama 3.3 70B → Llama 4 Scout → Qwen 3 32B via Groq, then Gemini Gen1, then Gemini Gen2, then human-sounding static fallback)
2. **Claps back** — dedicated roast mode with savage comebacks, faster typing, higher AI temperature, bypasses all cooldowns
3. **Flirts** — improvised pick-up lines and flirty replies with NSFW capability
4. **Acts human** — reading delay before typing, proportional typing delays, typo+correction, emoji reactions, unprompted follow-up messages, conversation history with per-speaker attribution
5. **Knows the room** — resolves Discord mentions to real names, injects reply-thread context, tracks who said what across the whole channel history
6. **Tells jokes** — randomly drops live-fetched dad jokes with configurable probability, cooldown, and daily cap
7. **Stays alive** — Flask HTTP server on port 8080 for uptime monitoring; `setup_autostart.sh` for Raspberry Pi

---

## Quick Navigation

| Page | What's in it |
|---|---|
| [Architecture](Architecture) | Module breakdown, data flow, design decisions |
| [Installation](Installation) | Step-by-step setup, `.env` config, Raspberry Pi |
| [Usage](Usage) | Commands, trigger words, roast/flirt mode, behaviour nuances |
| [Privacy](Privacy) | What data Ana touches and what she doesn't |
| [Troubleshooting](Troubleshooting) | Common problems and how to fix them |
| [Roadmap](Roadmap) | What's done, what's planned, what's not happening |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Discord integration | discord.py |
| Primary AI | Groq — Kimi K2 (primary) · Llama 3.3 70B · Llama 4 Scout 17B · Qwen 3 32B (waterfall) |
| Fallback AI (Gen1) | Google Gemini 1.5 Flash |
| Fallback AI (Gen2) | Google Gemini 2.5 Flash Lite |
| Dad jokes | icanhazdadjoke.com API |
| Keepalive | Flask 3.x |
| Config | python-dotenv |

---

## Repository Structure

```
Ana/
├── main.py             # Discord events, commands, human-behaviour simulation
├── nlp.py              # AI pipeline: Groq + Gemini fallbacks + post_process()
├── jokes.py            # Dad joke fetching, rate limiting
├── config.py           # Env vars, SYSTEM_PROMPT, trigger/roast/flirt word lists
├── keepalive.py        # Flask HTTP health endpoint
├── .env.example        # Template for .env — copy and fill in your keys
└── setup_autostart.sh  # Raspberry Pi systemd autostart setup
```

---

## Version

Current stable version: **5.0.0**

See [CHANGELOG](https://github.com/Kaelith69/Ana/blob/main/CHANGELOG.md) for what changed.
