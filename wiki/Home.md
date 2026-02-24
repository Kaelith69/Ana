# Ana Wiki — Home

Welcome to the Ana documentation wiki. You've found the place where we explain the bot in more detail than anyone asked for.

---

## What is Ana?

Ana is a **Discord bot** built in Python. She does three things well:

1. **Talks back** — Detect trigger words in messages and generate AI-powered replies using a triple-redundant AI pipeline (Groq Llama-4 → Gemini Gen1 → Gemini Gen2 → static fallback)
2. **Tells jokes** — Randomly drops dad jokes fetched live from `icanhazdadjoke.com`, with configurable probability, cooldown, and daily cap
3. **Stays alive** — Runs a Flask HTTP server on port 8080 for uptime monitoring

She's approximately 250 lines of Python across 5 source files. She is not trying to replace a full-featured bot framework. She is trying to make your Discord server a little more entertaining.

---

## Quick Navigation

| Page | What's in it |
|---|---|
| [Architecture](Architecture) | How the pieces fit together, module breakdown |
| [Installation](Installation) | Step-by-step setup, environment config |
| [Usage](Usage) | Commands, trigger words, how AI replies work |
| [Privacy](Privacy) | What data Ana touches and what she doesn't |
| [Troubleshooting](Troubleshooting) | Common problems and how to fix them |
| [Roadmap](Roadmap) | What's planned, what's being considered |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Discord integration | discord.py |
| Primary AI | Groq — Llama-4 Scout 17B |
| Fallback AI (Gen1) | Google Gemini Flash Lite |
| Fallback AI (Gen2) | Google Gemini 2.5 Flash Lite |
| Dad jokes | icanhazdadjoke.com API |
| Keepalive | Flask 3.x |
| Config | python-dotenv |

---

## Repository Structure

```
Ana/
├── main.py          # Discord events, commands, startup
├── nlp.py           # AI pipeline: Groq + Gemini fallbacks
├── jokes.py         # Dad joke fetching, rate limiting
├── config.py        # Env vars, settings, trigger words
└── keepalive.py     # Flask HTTP health endpoint
```

---

## Version

Current stable version: **2.0.0**

See [CHANGELOG](https://github.com/Kaelith69/Ana/blob/main/CHANGELOG.md) for what changed.
