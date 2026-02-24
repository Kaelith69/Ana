# Roadmap

Planned features, ideas under consideration, and things we've thought about but probably won't do.

---

## Current State (v2.0.0)

Ana works. She's in production. She tells jokes, replies to trigger words with AI, and hasn't crashed in a while. That's the baseline.

---

## Planned (Likely to Happen)

### Slash Commands
Replace `!joke` and `!shutdown` with proper Discord slash commands (`/joke`, `/shutdown`).

Slash commands show up in Discord's UI, have autocomplete, and are the direction Discord is pushing. The `!` prefix still works but is increasingly old-school.

**Impact:** `main.py` refactor, discord.py `app_commands` integration.

---

### Per-User Rate Limiting
Currently there's no limit on how many times one user can trigger Ana. In theory, one person could spam trigger words and generate constant AI API calls.

Adding a per-user cooldown (e.g., max 1 AI reply per user per 30 seconds) would control costs and prevent abuse.

**Impact:** `main.py` `on_message` handler, new in-memory rate limit tracker.

---

## Under Consideration (Maybe)

### Conversation Memory
Right now every AI reply is stateless — Ana doesn't remember what was said 10 seconds ago. Adding a short-term context window (last N messages from a user) would make conversations feel more natural.

Trade-offs: more complex, stores message content in memory (privacy consideration), increases API token usage.

**Impact:** `nlp.py` refactor, new memory store in `main.py`.

---

### Custom Trigger Words Per Server
Let server admins add their own trigger words via a command, stored per-guild.

Would require some form of persistence (a JSON file, SQLite, or similar). Currently Ana is completely stateless — this would change that.

**Impact:** New persistence layer, `config.py` refactor, new admin commands.

---

### Per-Server Personality Config
Let admins tune Ana's personality — more formal, more chaotic, topic-focused (only responds to tech talk, etc.).

Would likely be implemented as per-server system prompt customization passed to the AI models.

---

### Async Joke Pre-fetching
Currently `!joke` makes a live HTTP request and you wait. Pre-fetching a small cache in the background would make joke delivery instant.

The `JOKE_FETCH_BATCH` and `JOKE_FETCH_INTERVAL` config keys are already reserved for this feature.

---

## Probably Not

### Database Integration
Ana is intentionally stateless. Adding a database would add complexity, a new dependency, and potential privacy concerns without much benefit for the core use case.

Unless conversation memory or per-server config gets traction, a database isn't planned.

---

### Voice Channel Support
Ana speaking actual audio in a voice channel is out of scope. This would require TTS integration, voice connection management, and significant complexity. Cool? Sure. Happening? Unlikely.

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
