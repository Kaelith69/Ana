# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 2.x | ✅ Yes |
| 1.x | ❌ No — upgrade, seriously |

---

## Reporting a Vulnerability

Found a security issue? Please **do not** open a public GitHub issue. That's roughly equivalent to announcing a bank vault combination on Twitter.

Instead:

1. **Email** the maintainer directly — check the GitHub profile for contact info, or use GitHub's private vulnerability reporting feature (Security tab → "Report a vulnerability")
2. Include a clear description of the vulnerability
3. Include steps to reproduce if applicable
4. Give us a reasonable timeframe to respond (we aim for 48 hours on initial acknowledgment)

We'll work with you to understand the scope, patch it, and credit you in the changelog if you'd like.

---

## What Counts as a Vulnerability

Definitely report:
- API key exposure via logs, error messages, or responses
- Prompt injection allowing Ana to exfiltrate data or execute unintended actions
- Privilege escalation (non-owner triggering `!shutdown`)
- Dependency vulnerabilities with known CVEs

Probably not a security issue (but feel free to open a regular issue):
- "Ana said something weird" — that's just AI being AI
- The bot responding to trigger words in ways you don't like
- Dad jokes being objectively terrible

---

## Security Practices

Ana is designed with these security principles:

- **No secret storage** — API keys live in `.env`, which is gitignored. They're never logged or exposed via Discord messages.
- **Input truncation** — User messages sent to AI APIs are truncated to 1000 characters to limit prompt injection surface area.
- **Minimal permissions** — The bot requests only the Discord intents it needs (`messages`, `message_content`).
- **No persistence** — No database, no user data stored, no message logging.
- **Owner-gated shutdown** — `!shutdown` uses `@commands.is_owner()` — only the bot application owner can trigger it.

---

## Dependency Security

Ana's dependencies are minimal (5 packages). Keep them up to date:

```bash
pip install --upgrade discord.py flask python-dotenv requests groq
```

Check for known vulnerabilities with:

```bash
pip audit
```

---

*Security is serious. The tone of this document isn't. Both things can be true.*
