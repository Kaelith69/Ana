# Changelog

All notable changes to Ana are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and we use [Semantic Versioning](https://semver.org/).

Translation: `MAJOR.MINOR.PATCH` — breaking.feature.bugfix. Simple.

---

## [8.0.0] - 2026-03-10

### Added
- **Member profile memory** — new `profiles.py` module. After every reply, a background `asyncio.create_task` calls Gemini to silently extract personal details the user explicitly revealed (nickname, age, location, favorites, interests, family, facts). Stored as individual JSON files in `data/profiles/{name}.json`. Injected into the system prompt so Ana remembers things about each person across sessions.
- **`ProfileStore` class** — thread-safe, atomic-write profile store. `get()` / `update()` / `format_for_context()` / `list_pending()` / `cancel()`. Lazy directory scan on first access; ID-based lookup with collision-safe filename generation.
- **`extract_profile_info()`** — calls `gemini-flash-latest` to extract JSON-structured personal details from a message. Handles markdown-fenced responses, strips empty fields, coerces `age` to `int`, normalises `interests`/`facts` to lists.
- **`_sanitize_for_prompt()`** — strips `\r\n\t[]\\` from all dynamic profile values before injection into the system prompt, preventing prompt injection via stored profile data.
- **Smart reminder system** — new `reminders.py` module backed by `data/reminders/reminders.json`.
  - `!remindme <natural language>` — Gemini parses free-form text into a structured reminder (`datetime_ist`, `occasion`, `occasion_type`, `notes`). Relative dates resolved against current IST. Warns immediately if the parsed date is already in the past.
  - `!myreminders` — lists all pending reminders with short IDs and formatted IST datetimes.
  - `!cancelreminder <id>` — cancels a pending reminder by its 8-char ID prefix.
  - `_check_reminders` background task fires every 60 seconds, calls Gemini to generate an Ana-style AI wish/reminder message (tone varies by `occasion_type`: birthday / anniversary / wedding / exam / meeting / custom), and sends an @mention to the correct channel.
- **Profile extraction logging** — `_update_profile_bg()` now prints to `stderr` on every outcome: key missing, no info found, successful update, or exception. Replaces previously silent `except: pass`.
- **Gemini extraction HTTP error logging** — `extract_profile_info()` now prints the HTTP status + first 200 chars of the error body when Gemini returns non-200.

### Fixed
- **IST timezone bug in `_build_context_layer()`** — previously used `datetime.now(utc) + timedelta(hours=5, minutes=30)` which shifts the internal timestamp but leaves `.hour` and `.weekday()` reading from the UTC offset, giving wrong time-of-day and day-of-week values. Replaced with `datetime.now(_IST)` (proper `timezone` object) — same pattern already used in `main.py`.
- **Wrong Gemini model names** — `GEN2_MODEL` in `nlp.py` and `_EXTRACTION_MODEL` in `profiles.py` were set to `gemini-2.5-flash-lite` which does not exist on the v1beta API (returns HTTP 404 silently). Both corrected to `gemini-flash-latest`.

### Security
- **Prompt injection via profile data (S1)** — all dynamic profile values (nickname, location, favorites, facts, etc.) now passed through `_sanitize_for_prompt()` before being injected into the system prompt. Strips newlines, tabs, square brackets, and backslashes — the primary vectors for injecting fake `[System: ...]` directives.
- **Unbounded string growth (S2)** — string scalars in `_deep_merge()` are now capped at 120 chars. Prevents a long sequence of messages with crafted text from inflating every subsequent system prompt.
- **HTTP security headers (S3)** — `keepalive.py` Flask endpoint now sends `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Cache-Control: no-store` on every response via an `@app.after_request` hook.
- **Log data exposure (S4)** — LLM raw output printed to stdout in `nlp.py` is now truncated to 200 chars, preventing full user message content (injected via profile context) from appearing in logs.

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
