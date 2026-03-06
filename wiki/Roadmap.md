# Roadmap

What's been built, what's coming, and what's probably not happening.

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
Proportional typing delays, 4% typo+correction, 12% emoji-only reactions, 3 follow-up pools with different probabilities, low-signal skip.

### Raspberry Pi Autostart
`setup_autostart.sh` — one command installs a systemd service that survives reboots, waits for network, and auto-restarts on crash.

### `.env.example` Template
Documented env var template committed to the repo — no more guessing what keys are needed.

---

## Shipped (v2.0.0)

- Triple AI fallback chain (Groq → Gemini Gen1 → Gemini Gen2 → static)
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
