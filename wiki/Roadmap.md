# Roadmap

What's been built, what's coming, and what's probably not happening.

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
Ana is intentionally stateless beyond in-memory conversation history. Adding a persistent database would increase complexity and privacy surface area without much benefit for the core use case.

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
