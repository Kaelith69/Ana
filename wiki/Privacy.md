# Privacy

This page reflects current implementation behavior.

## What is stored

| Data | Stored? | Location |
|---|---|---|
| Channel history context | yes, in memory only | main.py _history |
| Cooldown maps | yes, in memory only | main.py dictionaries |
| User profile facts | yes, persisted | data/profiles/*.json |
| Full message logs database | no | not implemented |

## External processing

When NLP is called, message content can be sent to:
- Groq models
- Gemini fallback models

Profile extraction uses GEN2 API in profiles.py and updates per-user JSON.

## Credentials

- Keys are read from .env via dotenv with override enabled in config.py.
- .env should remain uncommitted.

## Operational implication

Ana is not a zero-storage bot because per-user profile facts are persisted on disk.
