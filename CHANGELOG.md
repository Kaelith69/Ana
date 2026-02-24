# Changelog

All notable changes to Ana are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and we use [Semantic Versioning](https://semver.org/).

Translation: `MAJOR.MINOR.PATCH` — breaking.feature.bugfix. Simple.

---

## [2.0.0] - 2025

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
