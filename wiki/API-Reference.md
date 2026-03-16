# API Reference

## Discord command surface

- !joke (handler: main.py joke): fetches and sends a live dad joke.
- !shutdown (handler: main.py shutdown): owner-only graceful shutdown sequence.

## Event handlers

- on_ready in main.py: starts periodic cleanup and logs identity.
- on_message in main.py: trigger detection, cooldown logic, NLP dispatch, follow-up behavior.

## Keepalive HTTP API

- Method: GET
- Path: /
- Response: Bot is alive!
- Source: keepalive.py

## Internal callable interfaces

- process_with_nlp in nlp.py: main response generation function.
- call_groq in nlp.py: Groq waterfall execution.
- call_gemini in nlp.py: Gemini fallback call.
- normalize_response in nlp.py: normalize mixed model output forms.
- post_process in nlp.py: strip AI-text artifacts before send.
- extract_profile_info in profiles.py: extract user facts from message text.
- ProfileStore.update in profiles.py: persist merged profile facts.
- DadJokeService.maybe_send_joke in jokes.py: random joke send path.

## Configuration API

Configuration is environment-variable based. See README configuration table and .env.example for canonical variable names and defaults.
