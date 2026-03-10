# Changelog

All notable changes to Ana are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and we use [Semantic Versioning](https://semver.org/).

Translation: `MAJOR.MINOR.PATCH` — breaking.feature.bugfix. Simple.

---

## [5.0.0] - 2026

### Added
- **Multi-user / group chat awareness** — Ana now knows who is talking in a multi-member server. Every user message stored in history is tagged with `name` (API-safe) and `author` (display name). Groq receives the `name` field on every chat message; Gemini receives `[Name]: content` prefixes on history entries. The model can now tell Kælith and Idli kutty apart instead of treating every prior message as one anonymous user.
- **Discord mention resolution** — `<@USER_ID>` tokens are replaced with `@DisplayName` before anything reaches the AI, so the model sees human-readable names instead of raw numeric IDs.
- **Reply-thread context injection** — When a message is a Discord reply, the referenced message is prepended as `[replying to @Name: "..."]` so Ana knows who is being talked about. Reference messages are fetched from Discord's API when not in cache, with graceful fallback on `NotFound`/`HTTPException`.
- **Reading delay** — Before Ana shows the typing indicator, she now pauses proportionally to the incoming message length (0.5–3s for normal messages; 0.2–0.7s for roasts — she fires faster when she's mad). Humans read before they type.
- **`_api_safe_name()` helper in `nlp.py`** — Sanitises display names to the `[a-zA-Z0-9_]` character set required by the Groq/OpenAI `name` field, max 64 chars.
- **`_sanitize_name_for_api()` + `_resolve_mentions()` helpers in `main.py`** — Clean separation between name sanitisation and mention replacement.
- **`_RE_CONTEXT_LEAK` regex** — Strips `[replying to @...]` if the LLM accidentally echoes the injected prefix back in its output.
- **`_RE_NAME_PREFIX_ECHO` regex** — Strips `[Name]:` if Gemini's context prefix leaks into the output.
- **`_RE_PAREN_ACTION` regex** — Strips embedded parenthetical stage directions that models occasionally insert: `(laughs)`, `(sighs)`, `(rolls eyes)`, `(sarcastically)`, etc.
- **Group chat section in `SYSTEM_PROMPT`** — Explicit instructions: respond to the specific person in front of you, not the room; you know the regulars and their relationship to each other; never recap what someone else just said; never address "the whole server".
- **Group chat line in every model patch** — Each of the four Groq model patches now reinforces the group-chat rule to trace who said what via the `name` field.
- **Expanded reaction pool** — Added `😬 🤌 🤭 💯 😑 🫶 🧍 🤷` (8 new reactions).
- **Expanded `_FOLLOWUPS`** — 6 new self-interruption lines.
- **Expanded `_FLIRT_FOLLOWUPS`** — 6 new flustered post-flirt lines.

### Changed
- **Prompt injection hardening on reply-context** — `ref_author` and `ref_text` now strip `\r\n\t[]"\\` before injection into the prompt, preventing crafted display names or message content from escaping the context tag.

---

## [4.0.0] - 2025

### Added
- **4-model Groq waterfall** — `call_groq()` now cycles through Kimi K2 → Llama 3.3 70B → Llama 4 Scout → Qwen 3 32B in priority order. A rate-limited or failed model is skipped immediately rather than crashing or going silent. All four are configurable via `GROQ_MODEL_PRIMARY/BACKUP1/BACKUP2/BACKUP3` env vars.
- **`_call_single_groq_model()`** — Internal helper that wraps a single Groq model call so each waterfall stage is self-contained and independently exception-safe.
- **Per-model `MODEL_SETTINGS` dict in `config.py`** — Each model has its own `temperature`, `max_tokens`, `top_p`, `thinking`, and `patch` keys. Patches are short addenda appended to the system prompt for models that need extra instruction-following nudges.
- **`thinking: False` support for Qwen 3 32B** — Passed as `extra_body: {"thinking": false}` to prevent chain-of-thought reasoning steps from bleeding into the reply.
- **Per-model system prompt patches** — Short, model-specific instructions appended to `SYSTEM_PROMPT` in normal mode to suppress the most common per-model AI tells.
- **`_build_context_layer()`** — Generates a short IST (UTC+5:30) day-of-week + time-of-day context note appended to the system prompt in normal mode, giving Ana a realistic mood baseline.

### Changed
- Groq primary model updated from `llama-4-scout-17b-16e-instruct` to `moonshotai/kimi-k2-instruct`.
- Temperature is now per-model (0.82–0.88 normal) rather than a single global value.

---

## [3.0.0] - 2025

### Changed
- **Live joke fetching** — Replaced file-based joke loading with live API calls to `icanhazdadjoke.com`. No more stale jokes sitting in a text file aging like warm milk.
- **Unified Gemini caller** — `call_gen1` and `call_gen2` are now thin aliases over a single `call_gemini()` function. Less copy-paste, more sanity.
- **Upgraded AI model** — Primary model updated to `meta-llama/llama-4-scout-17b-16e-instruct` via Groq. Ana is now smarter. Use that information responsibly.
- **Config refactor** — `JokeSettings` dataclass introduced for structured joke configuration. Environment variable parsing now has proper type coercion with warnings.
- **NLP entry point** — `process_with_nlp()` is now the single unified entry point for all AI replies. No more calling individual model functions directly.

### Added
- `normalize_response()` — Smart response normalization that handles cases where AI models decide to return JSON instead of plain text (they do this sometimes, it's deeply annoying).
- Graceful degradation for missing API keys — warnings printed at startup, not crashes at runtime.
- `asyncio.to_thread()` for blocking AI calls — Discord's event loop stays responsive even when Groq is thinking.
- Daily joke limit (3/day) — because even chaos has HR policies.

### Removed
- File-based joke storage (`dad_jokes.txt`) — rest in peace, you flat text file
- Background joke pre-fetching — jokes are now fetched on demand
- Batch joke loading logic — not needed with live fetching

---

## [1.0.0] - 2024

### Added
- Initial release of Ana Discord bot
- Basic trigger word detection with `on_message`
- AI replies via Gemini models (Gen1 and Gen2)
- File-based dad joke service
- Flask keepalive server on port 8080
- `!joke` command for on-demand jokes
- `!shutdown` command (bot owner only, with dramatic farewell)
- `.env`-based configuration
- 70+ trigger words across multiple languages and categories

---

*If a version isn't listed here, it either didn't exist or it was too embarrassing to document.*
