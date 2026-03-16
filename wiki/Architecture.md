# Architecture

## Execution model

Ana runs in one Python process.

- Discord client and event loop run in main.py.
- Keepalive Flask server runs in a daemon thread from keepalive.py.
- Blocking HTTP/model work is offloaded with asyncio.to_thread.

## Core flow

1. on_message receives message events.
2. Precompiled regex detects mode: roast, flirt, trigger, or no-trigger.
3. Branch logic applies cooldown and behavior simulation.
4. process_with_nlp is called for triggered responses.
5. Output is normalized and sent.
6. Background profile extraction updates per-user JSON data.

## AI subsystem

Order of attempts:

1. Groq waterfall from config values.
2. Gemini Gen1 fallback.
3. Gemini Gen2 fallback.
4. Static fallback string list.

Response cleanup:

- normalize_response
- post_process

These remove markdown and AI artifact patterns before send.

## State and storage

- _history: per-channel in-memory deque with maxlen 20.
- _user_last_reply: in-memory dict by user id.
- _channel_last_reply: in-memory dict by channel id.
- Profile files: JSON per user in data/profiles.

## External integrations

- Discord API for events and messages.
- Groq for primary and classifier model access.
- Gemini for fallback and profile extraction paths.
- icanhazdadjoke.com for dad jokes.
