# Architecture

Ana is a small bot with a deliberately simple architecture. No microservices, no message queues, no infrastructure overhead. Just Python, a few APIs, and a healthy appreciation for fallback chains.

---

## High-Level Overview

```
Discord Server
      │
      ▼  (discord.py gateway)
   main.py
   ├── on_message() ──────────────────────────────────────────────┐
   │     ├── trigger word check                                    │
   │     │     ├── YES → asyncio.to_thread(process_with_nlp)      │
   │     │     │              └── nlp.py (AI pipeline)            │
   │     │     └── NO  → maybe_send_joke()                        │
   │     │                    └── jokes.py (DadJokeService)       │
   │     └── bot.process_commands()                               │
   │                                                               │
   ├── !joke ─→ joke_service.random_joke()                        │
   └── !shutdown ─→ dramatic farewell → bot.close()              │
                                                                   │
config.py  ◄────── .env (API keys, settings, trigger words) ──────┘
keepalive.py ─→ Flask on :8080 (GET / → "Bot is alive!")
```

---

## Module Breakdown

### `main.py` — The Entry Point

This is the Discord-facing layer. It:

- Initializes the `commands.Bot` instance with the required intents (`messages`, `message_content`)
- Registers two commands: `!joke` and `!shutdown`
- Handles `on_ready` (logs successful login) and `on_message` (the main event loop)
- Runs `start_keepalive()` before connecting to Discord

The `on_message` handler is the critical path:
1. Ignore messages from the bot itself (infinite loop prevention 101)
2. Lowercase the content and check for any trigger word match
3. If triggered: run `process_with_nlp` via `asyncio.to_thread` (blocking I/O off the event loop), send result
4. If not triggered: call `maybe_send_joke` — this may or may not fire depending on probability/cooldown

**Why `asyncio.to_thread`?**
The AI API calls are synchronous HTTP requests. Calling them directly on the async event loop would block the entire bot. `asyncio.to_thread` offloads them to a thread pool, keeping the event loop responsive.

---

### `nlp.py` — The AI Pipeline

The NLP module is basically a try/except ladder with three AI services. It's not fancy. It works.

```
process_with_nlp(text)
    │
    ├── call_groq(text)
    │     └── Groq client → llama-4-scout-17b-16e-instruct
    │           └── max 1000 chars input, 400 tokens output
    │
    ├── (if Groq fails) call_gemini(GEN1_MODEL, GEN1_API_KEY, text)
    │     └── gemini-flash-lite-latest via streamGenerateContent API
    │
    ├── (if Gen1 fails) call_gemini(GEN2_MODEL, GEN2_API_KEY, text)
    │     └── gemini-2.5-flash-lite via streamGenerateContent API
    │
    └── (if everything fails) random.choice(FALLBACK_RESPONSES)
          └── "Cool story, bro." and friends
```

**Key design decisions:**
- The Groq client is instantiated **once at module load** — not per request. This avoids connection overhead.
- `normalize_response()` handles cases where models return JSON instead of plain text (they do this more often than you'd think).
- Input is truncated to 1000 characters before sending to any API — basic prompt injection mitigation and cost control.
- Streaming is used for Gemini calls (the API requires it for these models), but the full response is buffered before returning.

---

### `jokes.py` — The Dad Joke Service

`DadJokeService` is a stateful service class that manages joke delivery with three constraints:

| Constraint | Default | Config key |
|---|---|---|
| Random chance per message | 15% | `JOKE_CHANCE` |
| Cooldown between jokes | 60 seconds | `JOKE_COOLDOWN` |
| Daily maximum | 3 jokes | hardcoded in class |

`random_joke()` fetches live from `icanhazdadjoke.com` with a timeout. If the API is down, it returns `None` and no joke is sent. No fallback joke list — if the API is dead, your server gets a moment of peace.

`maybe_send_joke()` is async (awaited in `on_message`) and checks all three constraints before fetching and sending. Daily count resets automatically when the day rolls over.

---

### `config.py` — Config and Constants

Loads all configuration from environment variables with sensible defaults. Key exports:

- `DISCORD_TOKEN` — required for the bot to start
- `GROQ_API_KEY`, `GEN1_API_KEY`, `GEN2_API_KEY` — optional but needed for AI functionality
- `JOKE_SETTINGS` — a frozen `JokeSettings` dataclass with all joke parameters
- `TRIGGER_WORDS` — a tuple of 70+ strings that trigger AI replies

Missing required vars print warnings at startup rather than crashing — this lets you see exactly what's missing before the bot fails to connect.

---

### `keepalive.py` — The Flask Heartbeat

A minimal Flask app running in a daemon thread. Responds to `GET /` with `"Bot is alive!"`.

Purpose: services like UptimeRobot, BetterStack, or Railway's health checks can ping this endpoint to confirm the process is running. Without it, free-tier hosting platforms that sleep idle processes would shut down Ana within minutes.

Port: `8080` (standard non-privileged port for cloud hosting).

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
