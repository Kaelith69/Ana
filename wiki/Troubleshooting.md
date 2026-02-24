# Troubleshooting

Something's broken. Let's fix it. No judgment — we've all been there.

---

## Ana isn't responding to anything

**Check 1: Is the bot online?**

Look for Ana in your server's member list. If she's showing as offline, the process isn't running or crashed on startup.

**Check 2: Did she log in successfully?**

Check your terminal/logs for:
```
✅ Logged in as Ana#1234
```

If you don't see this, the bot failed to connect.

**Check 3: Did you enable Message Content Intent?**

Go to Discord Developer Portal → Your App → Bot → Privileged Gateway Intents.

Enable **Message Content Intent**. Without this, the bot can see messages exist but can't read their text. Ana is effectively blind.

**Check 4: Does the bot have permission to send messages in that channel?**

Check channel permissions. Ana needs: `View Channel`, `Send Messages`, `Read Message History`.

---

## Bot starts but doesn't respond to trigger words

**Check 1: Are you using trigger words correctly?**

Trigger words are detected anywhere in the message, case-insensitively. Test with something unambiguous:

```
ana
```

Just the word. Nothing else.

**Check 2: Check your AI API keys**

Without `GROQ_API_KEY`, Ana falls through to Gemini. Without Gemini keys either, she hits the static fallback — which should still respond.

If she's responding with "Cool story, bro." or "Interesting..." — the static fallback is working but all AI APIs are failing. Check your keys and API console for errors.

**Check 3: Check the terminal output**

Ana logs AI pipeline output. Look for:
```
GROQ Output:
[response text]
```

Or error messages like:
```
GROQ primary failed: ...
Gen1 backup failed: ...
Gen2 backup2 failed: ...
```

---

## "DISCORD_TOKEN is missing" on startup

You haven't set `DISCORD_TOKEN` in your `.env` file.

```bash
# In .env:
DISCORD_TOKEN=your_actual_token_here
```

If you're on a hosting platform (Railway, Render, Replit), set it in their environment variables UI — `.env` files often aren't used there.

---

## `!joke` returns "My humor banks are empty 😢"

The joke API (`icanhazdadjoke.com`) returned nothing — likely a timeout or rate limit.

Try again in a moment. If it's consistently failing, check if the API is reachable from your host:

```bash
curl -H "Accept: application/json" https://icanhazdadjoke.com/
```

If that times out, your hosting provider may be blocking outbound HTTP on port 443.

---

## Groq API errors

Common Groq errors and what they mean:

| Error | Cause | Fix |
|---|---|---|
| `AuthenticationError` | Invalid or missing API key | Check `GROQ_API_KEY` in `.env` |
| `RateLimitError` | Too many requests | Groq free tier has limits; wait or upgrade |
| `APIConnectionError` | Network issue | Check internet connectivity from your host |
| `APITimeoutError` | Groq is slow | Ana falls back to Gemini automatically |

---

## Gemini API errors

Gemini uses HTTP directly (not the official SDK). Check for status codes in logs:

```
Gen1 Error: 403
```

| Status | Cause | Fix |
|---|---|---|
| 401 | Invalid API key | Check `GEN1_API_KEY` / `GEN2_API_KEY` |
| 403 | API not enabled or key restricted | Check Google AI Studio key settings |
| 429 | Rate limit hit | Free tier quota; wait or use a different key |
| 503 | Gemini service down | Nothing you can do; static fallback kicks in |

---

## Ana is sending jokes way too often / not enough

This is configuration. Adjust in `.env`:

```env
# More jokes (30% chance, 30s cooldown)
JOKE_CHANCE=0.30
JOKE_COOLDOWN=30

# Fewer jokes (5% chance, 10min cooldown)
JOKE_CHANCE=0.05
JOKE_COOLDOWN=600
```

Restart after changing `.env`.

Note: the daily maximum is hardcoded at 3 in `jokes.py`. If you want to change it, edit `self.max_jokes_per_day = 3` in the `DadJokeService.__init__` method.

---

## `!shutdown` isn't working

`!shutdown` is restricted to the **bot owner** — the Discord account that owns the bot application. This is checked via discord.py's `@commands.is_owner()`.

If you're the owner and it's still not working, try DMing the bot: `!shutdown` (some servers block certain commands).

---

## Ana is running but the keepalive endpoint doesn't respond

The Flask server runs on port `8080`. Test it:

```bash
curl http://localhost:8080/
# Expected: Bot is alive!
```

If this fails, the Flask thread may have crashed silently. Check if there's another process using port 8080:

```bash
lsof -i :8080   # Linux/macOS
netstat -ano | findstr :8080  # Windows
```

---

## Still stuck?

Open an [issue on GitHub](https://github.com/Kaelith69/Ana/issues) with:
- What you expected to happen
- What actually happened
- Relevant terminal output (redact your API keys)
- Your hosting environment (local, Railway, Render, Replit, etc.)
