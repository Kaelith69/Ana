# Architecture

Ana is a small bot with a deliberately simple architecture. No microservices, no message queues, no infrastructure overhead. Just Python, a few APIs, and a healthy appreciation for fallback chains.

---

## High-Level Overview

```
Discord Server
      │
      ▼  (discord.py gateway)
   main.py
   ├── on_message()
   │     ├── detect is_roast / is_flirt / is_trigger
   │     │
   │     ├── ROAST ──► bypass cooldowns → asyncio.to_thread(process_with_nlp, roast=True)
   │     │                                   └── nlp.py  → post_process() → fast reply
   │     │                                   └── 25% _ROAST_FOLLOWUPS
   │     │
   │     ├── FLIRT ──► cooldowns → asyncio.to_thread(process_with_nlp, flirt=True)
   │     │                          └── nlp.py → post_process() → normal reply
   │     │                          └── 20% _FLIRT_FOLLOWUPS
   │     │
   │     ├── TRIGGER ► cooldowns → 12% emoji-only reaction
   │     │                       → asyncio.to_thread(process_with_nlp)
   │     │                            └── nlp.py → post_process() → proportional delay
   │     │                            └── 4% typo+correction  8% _FOLLOWUPS
   │     │
   │     └── NO TRIGGER → maybe_send_joke() → jokes.py
   │
   ├── !joke ─→ joke_service.random_joke()
   └── !shutdown ─→ casual farewell → bot.close()

config.py  ◄────── .env (tokens, API keys, SYSTEM_PROMPT override)
keepalive.py ─→ Flask on :8080 (GET / → "Bot is alive!")
```

---

## Module Breakdown

### `main.py` — The Discord Layer

Owns the `commands.Bot` instance and all event handling. Key responsibilities:

- **Trigger detection** — `TRIGGER_PATTERN`, `ROAST_PATTERN`, `FLIRT_PATTERN` are pre-compiled regexes at module load. `is_roast` and `is_flirt` are detected *before* any cooldown checks so roasts are never silently swallowed.
- **Cooldown system** — Per-user 25s cooldown (`_user_last_reply` dict) and per-channel 7s cooldown (`_channel_last_reply` dict), both bypassed for roasts. A background `tasks.loop(hours=1)` prunes stale entries to bound memory.
- **Behaviour simulation** — 12% emoji-only reaction chance, 10% extra reaction overlay on top of replies, 20% low-signal skip, `_maybe_typo()` for 4% typo+correction (correction sent ~~70%~~ roughly 70% of the time), 6% ghost-typing, proportional typing delay.
- **Reply pipeline** — Calls `process_with_nlp` via `asyncio.to_thread` (keeps event loop non-blocking), then splits long replies with `_split_reply()` and sends parts with 1.2s gaps.
- **Follow-up system** — Three distinct follow-up pools: `_ROAST_FOLLOWUPS` (25% chance), `_FLIRT_FOLLOWUPS` (20% chance), `_FOLLOWUPS` (8% chance).
- **Conversation history** — `_history: dict[int, deque]` stores last 10 messages per channel and passes them to every AI call.

**Why `asyncio.to_thread`?** The AI API calls are synchronous HTTP. Calling them on the event loop directly would block all Discord I/O. `asyncio.to_thread` offloads to the default thread pool executor.

---

### `nlp.py` — The AI Pipeline

Three-backend try/except ladder with per-mode prompts and output normalisation.

```
process_with_nlp(text, history, author_name, roast, flirt)
    │
    ├── call_groq()
    │     └── Groq → llama-4-scout-17b-16e-instruct
    │           temperature: 1.1 normal / 1.3 roast
    │           max_completion_tokens: 200
    │
    ├── (Groq fails) call_gemini(GEN1_MODEL, GEN1_API_KEY)
    │     └── gemini-1.5-flash-latest
    │           temperature: 1.2 normal / 1.4 roast
    │           maxOutputTokens: 200
    │
    ├── (Gen1 fails) call_gemini(GEN2_MODEL, GEN2_API_KEY)
    │     └── gemini-2.5-flash-lite  (same settings as Gen1)
    │
    └── (all fail) random.choice(FALLBACK_RESPONSES)
          └── 15 human-sounding short phrases

    Every reply path ──► normalize_response() ──► post_process()
```

**Prompts:**
- `SYSTEM_PROMPT` — loaded from `.env` (SYSTEM_PROMPT key) or the hardcoded default. Defines Ana's casual texting style, banned phrases, reply-length distribution, and personality quirks. Appended with the author's display name for personalisation.
- `ROAST_PROMPT` — seven specific rules: mirror energy, use their words, be specific, favour wordplay over raw swearing, escalate, never soften, one skull max.
- `FLIRT_PROMPT` — rules for original improvised pickup lines: personalised, NSFW-capable, varying styles, no cliché formats.

**`post_process(text)`** — deterministic artefact stripper applied to every reply:
1. Strip markdown (`**bold**`, `*italic*`, `` `code` ``, `__underline__`, `_italic_`)
2. Strip AI opener phrases (`Sure,`, `Of course,`, `Certainly,`, `Happy to help,`, `Great question,` etc.)
3. Remove trailing period (unless `...`)
4. Lowercase the first letter

**`normalize_response(raw)`** — handles models returning JSON `{"message": "..."}` instead of plain text, recursively finds first usable string, then calls `post_process()`.

**Key design decisions:**
- Groq client instantiated **once at module load** — avoids per-request connection overhead
- Input truncated to 1000 characters — prompt injection mitigation and cost control
- Author name sanitised (strips `\r\n\t`, max 50 chars) — prevents injection via crafted display names
- Temperature varies by mode — higher for roasts to get more creative, unpredictable comebacks

---

### `jokes.py` — The Dad Joke Service

`DadJokeService` is a stateful class managing joke delivery with three constraints:

| Constraint | Default | Config key |
|---|---|---|
| Random chance per message | 15% | `JOKE_CHANCE` |
| Cooldown between jokes | 60 seconds | `JOKE_COOLDOWN` |
| Daily maximum per channel | 3 | hardcoded |

`random_joke()` does a live GET to `icanhazdadjoke.com` with a configurable timeout. Returns `None` on failure — no fallback joke list. `maybe_send_joke()` is async, checks all three constraints before fetching and sending. Daily count resets automatically when the day rolls over.

---

### `config.py` — Config and Word Lists

Loads all configuration from environment variables with typed defaults. Key exports:

- `DISCORD_TOKEN` — required; missing value causes `sys.exit(1)` at startup
- `GROQ_API_KEY`, `GEN1_API_KEY`, `GEN2_API_KEY` — optional but needed for AI
- `SYSTEM_PROMPT` — full bot personality, overridable via `.env`
- `JOKE_SETTINGS` — frozen `JokeSettings` dataclass
- `TRIGGER_WORDS` — tuple of 70+ strings for general trigger detection
- `ROAST_WORDS` — frozenset of 60+ insult/dismissal words
- `FLIRT_WORDS` — frozenset of flirt/compliment words

---

### `keepalive.py` — The Flask Heartbeat

Minimal Flask app in a daemon thread. Responds to `GET /` with `"Bot is alive!"`.

Purpose: uptime monitors (UptimeRobot, BetterStack, Railway health checks) can ping this endpoint. Without it, free-tier hosting platforms sleep idle processes within minutes.

Port: `8080`. Werkzeug logs suppressed to `ERROR` level to avoid noise in systemd journal.

---

### `setup_autostart.sh` — Raspberry Pi Setup

A one-shot bash script that:
1. Creates `.venv/` virtualenv in the repo directory
2. Installs dependencies into the venv
3. Writes `/etc/systemd/system/ana-bot.service` (with `After=network-online.target`, `Restart=on-failure`, `EnvironmentFile=.env`)
4. Enables and starts the service immediately

After running once, Ana starts automatically on every reboot, waits for network connectivity, and restarts within 10s of any crash.

---

## Threading Model

Ana runs two threads:

1. **Main thread** — Discord's `bot.run()` which runs the asyncio event loop
2. **Keepalive thread** — Flask's development server (daemon=True, dies when main thread dies)

AI calls within the event loop are dispatched via `asyncio.to_thread()` to the default thread pool executor, so they don't block Discord event processing.

---

## External Dependencies

| Service | Used for | Required? |
|---|---|---|
| Discord API | Bot gateway, message events, replies | Yes |
| Groq API | Primary AI replies (Llama-4) | Recommended |
| Google Gemini Gen1 | First AI fallback | Optional |
| Google Gemini Gen2 | Second AI fallback | Optional |
| icanhazdadjoke.com | Live dad joke fetching | Optional (no jokes if down) |
