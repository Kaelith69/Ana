# Developer Guide

## Local development loop

1. Install dependencies.
2. Configure .env.
3. Run python main.py.
4. Validate with smoke_test.py and compile checks.

## Recommended checks

- python -m compileall .
- python smoke_test.py
- python -c "import config, jokes, profiles, nlp, keepalive, main; print('imports-ok')"

## Codebase conventions

- Async boundaries: use asyncio.to_thread for blocking model and network work.
- Error tolerance: keep external-call failures non-fatal where possible.
- Fallback order: preserve Groq, then Gemini Gen1, then Gemini Gen2, then static fallback.
- Prompt behavior: keep roast and flirt prompts mode-specific.
- Data safety: never log secrets.

## High-risk files

- main.py: central control flow and probabilities.
- nlp.py: prompting, model routing, output sanitization.
- config.py: environment loading and defaults.
- profiles.py: persistent user-data behavior.

## Editing behavior probabilities

- Update docs in README and wiki/Usage.md in the same change.
- Re-run compile and smoke tests.
- Ensure no branch causes empty or emoji-only responses unless intentionally designed.

## Deployment notes

- setup_autostart.sh installs a systemd service on Raspberry Pi.
- keepalive endpoint is bound to port 8080 in current implementation.
