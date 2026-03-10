# Roadmap

What's been built, what's coming, and what's probably not happening.

---

## Shipped (v8.0.0)

### Smart Reminder System
Full reminder pipeline with `!remindme <natural language>`, `!myreminders`, and `!cancelreminder <id>` commands. Gemini parses free-form text into a structured reminder (resolves relative dates, infers occasion type). A `tasks.loop(minutes=1)` background task fires due reminders with an AI-generated, Ana-voice wish @mentioning the user. Persisted in `data/reminders/reminders.json`.

### Per-User Profile Memory
Ana silently extracts personal details from every message she replies to (name, age, location, favourites, interests, etc.) via a background `asyncio.create_task`. Profiles are deep-merged into per-user JSON files in `data/profiles/`. On every reply, the profile is injected as a compact one-line context string, letting Ana remember things across sessions.

### IST Timezone Fix
`_build_context_layer()` in `nlp.py` was computing IST by adding a `timedelta` to a UTC `datetime` — giving correct clock arithmetic but wrong `.hour` and `.weekday()` values. Fixed by defining `_IST = datetime.timezone(timedelta(hours=5, minutes=30))` and using `datetime.now(_IST)`.

### Gemini Model Name Fixes
`_EXTRACTION_MODEL` in `profiles.py` and `GEN2_MODEL` in `nlp.py` were set to the non-existent `gemini-2.5-flash-lite`. Corrected to `gemini-flash-latest`.

### Security Hardening
Flask keepalive now sends `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Cache-Control: no-store` headers. Profile values sanitised via `_sanitize_for_prompt()` before prompt injection. `_deep_merge()` caps string scalars at 120 chars.

### Extraction Error Logging
`_update_profile_bg()` and `extract_profile_info()` now log all outcomes to stderr instead of silently swallowing exceptions.

---

## Shipped (v5.0.0)

### Multi-User Group Chat Awareness
Ana now knows who is talking to her in a group channel. `<@USER_ID>` mentions are resolved to real display names before any AI call. Discord reply-threads inject the referenced message as context (`[replying to @Name: "..."]`). Per-speaker history attribution: every history entry carries the speaker's name so the model always knows who said what.

### Reading Delay
Before showing the typing indicator, Ana pauses to "read" the message: 0.2–0.7s for roasts, 0.5–3s (proportional to message length) for normal messages. Makes her feel like she actually read the message before responding.

### Stage Direction & Artefact Stripping
Three new `post_process()` passes: `_RE_CONTEXT_LEAK` strips any `[replying to @…]` prefix the model echoes back; `_RE_NAME_PREFIX_ECHO` strips `[Name]:` emission from Gemini; `_RE_PAREN_ACTION` strips `(laughs)`, `(sighs)`, `(rolls eyes)` etc.

### Group Chat System Prompt
Dedicated `GROUP CHAT` section in `SYSTEM_PROMPT` instructs the model to respond to the person, not the room; reference others by name when natural; stay out of conversations not addressed to her; never address "everyone" or "the group".

### Expanded Behaviour Pools
`_REACTIONS` expanded with 8 new emojis; `_FOLLOWUPS` and `_FLIRT_FOLLOWUPS` each expanded with 6 new lines.

---

## Shipped (v4.0.0)

### 4-Model Groq Waterfall
Groq primary backend upgraded from a single model to a prioritised 4-model waterfall: `moonshotai/kimi-k2-instruct` (primary) → `meta-llama/llama-3.3-70b-versatile` → `meta-llama/llama-4-scout-17b-16e-instruct` → `qwen/qwen3-32b`. Each model has its own temperature, top_p, max_tokens, and response patch in `MODEL_SETTINGS`.

### Per-Model Settings
`MODEL_SETTINGS` dict in `config.py` — each Groq model independently configured. Per-model `patch` allows normalising quirks in model output (e.g. Qwen 3 thinking tokens).

---

## Shipped (v3.0.0)

### Roast Mode
Dedicated roast/comeback pipeline with its own prompt, higher AI temperature, cooldown bypass, faster typing, and follow-up pool. Ana always fires back when insulted — no exceptions.

### Flirt Mode
Improvised, original pick-up lines via a dedicated `FLIRT_PROMPT`. NSFW-capable. Includes a separate `_FLIRT_FOLLOWUPS` pool.

### Per-User Rate Limiting
Per-user 25s cooldown and per-channel 7s cooldown prevent spam. Roasts always bypass both. "Seen" reaction behaviour during cooldown.

### Conversation History / Short-term Memory
Per-channel sliding window of last 10 messages (5 exchanges) passed as context on every AI call. Ana knows what was just said.

### AI Artefact Stripping (`post_process`)
Deterministic post-processing on every reply: strips markdown, AI opener phrases, trailing periods, capitalises away from sentence-case.

### Human-sounding Behavioural Simulation
Proportional typing delays, 4% typo+correction, 70% chance correction appears, 12% emoji-only reactions, 3 follow-up pools with different probabilities, 20% low-signal skip, 6% ghost-typing.

### Raspberry Pi Autostart
`setup_autostart.sh` — one command installs a systemd service that survives reboots, waits for network, and auto-restarts on crash.

### `.env.example` Template
Documented env var template committed to the repo — no more guessing what keys are needed.

---

## Shipped (v2.0.0)

- AI fallback chain (Groq → Gemini Gen1 → Gemini Gen2 → static)
- 70+ trigger word list with multilingual greetings and cultural events
- Dad joke system with configurable probability, cooldown, and daily cap
- Flask keepalive on `:8080`
- `!joke` and `!shutdown` commands

---

## Planned (Likely to Happen)

### Slash Commands
Replace `!joke` and `!shutdown` with proper Discord slash commands (`/joke`, `/shutdown`). Slash commands show in Discord's UI, have autocomplete, and are the direction Discord is pushing.

**Impact:** `main.py` refactor, `discord.py` `app_commands` integration.

---

### Custom Trigger Words Per Server
Let server admins add their own trigger words via a command, stored per-guild. Would require a simple persistence layer (JSON or SQLite).

**Impact:** New persistence layer, new admin commands.

---

## Under Consideration (Maybe)

### Per-Server Personality Config
Let admins tune Ana's personality — more formal, more chaotic, topic-focused. Likely implemented as per-server system prompt customisation.

---

### Async Joke Pre-fetching
Pre-fetch a small joke cache in the background so `!joke` delivery is instant. `JOKE_FETCH_BATCH` and `JOKE_FETCH_INTERVAL` config keys are already reserved.

---

## Probably Not

### Database Integration
Ana now uses lightweight JSON file persistence for profiles (`data/profiles/`) and reminders (`data/reminders/`). A full SQL or NoSQL database remains out of scope — the JSON approach covers current needs without the operational overhead.

### Voice Channel Support
TTS + voice connection management is out of scope. Cool in theory. Not happening.

---

### Web Dashboard
A web interface for monitoring Ana's activity, configuring settings, etc. Sounds useful. Also sounds like a whole separate project.

---

## Contributing Ideas

Have a feature idea? Open an issue on GitHub with the `enhancement` label. Describe what it does, why it's useful, and ideally a rough sketch of how it'd work.

Ideas that are:
- Small and focused
- Don't require a database for simple use cases
- Consistent with Ana's casual, conversational personality
- Privacy-respecting

...are much more likely to get implemented than sweeping architectural overhauls.

---

*This roadmap reflects current thinking and will change. "Under Consideration" means exactly that — not a promise, not a rejection.*
