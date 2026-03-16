# Troubleshooting

## Bot starts but no replies

1. Confirm startup log includes logged-in message.
2. Confirm Message Content intent is enabled in Discord developer settings.
3. Confirm channel permissions include sending messages and reactions.

## API key confusion

If keys look valid but runtime still fails, verify env precedence:
- config.py loads dotenv with override=True.
- Restart process after editing .env.
- Run smoke_test.py.

## Groq and fallback diagnostics

- Run python smoke_test.py to validate both GROQ_API_KEY and GROQ_BACKUP_API_KEY.
- Check terminal logs for model-specific failure lines.

## Common behavior misunderstandings

- Roast bypasses cooldowns.
- Normal triggers can be skipped by low-signal or ghost-typing probability.
- There is no emoji-only reply branch.

## Keepalive endpoint

- GET http://localhost:8080/ should return Bot is alive!
- If unavailable, check for port conflicts on 8080.
