# Troubleshooting

Something's broken. Let's fix it.

---

## Ana isn't responding to anything

**Check 1: Is the bot online?**

Look for Ana in your server's member list. If she's offline, the process isn't running or crashed on startup.

**Check 2: Did she log in successfully?**

Check your terminal/logs for:
```
✅ Logged in as Ana#1234
```

**Check 3: Did you enable Message Content Intent?**

Discord Developer Portal → Your App → Bot → Privileged Gateway Intents → enable **Message Content Intent**. Without this, Ana is effectively blind — she sees message events but can't read the text.

**Check 4: Does the bot have permission to send messages?**

Ana needs `View Channel`, `Send Messages`, `Read Message History`, and `Add Reactions` in the channel.

---

## Bot starts but doesn't respond to trigger words

**Check 1: Are you using trigger words correctly?**

Trigger words are detected anywhere in the message, case-insensitively. Test with just:
```
ana
```

**Check 2: She responds but the reply sounds very generic**

If you're getting responses like `"idk what to say lol"` or `"wait what"` on every message, all AI APIs are failing and she's hitting the static fallback. Check your API keys and look at the terminal for:
```
GROQ primary failed: ...
Gen1 backup failed: ...
Gen2 backup2 failed: ...
```

**Check 3: Check the terminal for the model output**

Ana prints every AI reply to stdout:
```
GROQ Output:
[response text]
```

---

## She's not firing back at insults / roast mode not triggering

The roast word list is in `ROAST_WORDS` in `config.py`. Try a word that's definitely in there:
```
stupid
```

Note that roast detection uses `re.search` with `\b` word boundaries — `"stupidity"` won't trigger `"stupid"`. The exact word, or a phrase like `"nobody asked"`, must appear in the message.

Also check: if the channel just had a non-roast message from her within 7 seconds, she waits on non-roast triggers — but roast always goes through.

---

## "DISCORD_TOKEN is missing" on startup

You haven't set `DISCORD_TOKEN` in your `.env` file. The bot exits immediately.

```bash
# In .env:
DISCORD_TOKEN=your_actual_token_here
```

On Railway/Render/Replit, set it in their environment variables UI instead.

---

## Bot looks like it's ignoring me completely

If she sometimes starts typing and then stops, or just reacts with an emoji and doesn't send text, that's intentional. Ana silently ignores about 20% of "low‑signal" messages (`lmao`, `omg`, `wow`, `bruh`, etc.) and has a ~6% chance of ghost‑typing when she decides not to reply. This is normal behaviour designed to make her feel human. If you want her to reply every time, remove words from `TRIGGER_WORDS` or adjust the probability constants in `main.py`.

---

## `!joke` gives a non-human response / "idk any rn"

The joke API (`icanhazdadjoke.com`) returned nothing — timeout or rate limit. Try again in a moment. Check reachability:

```bash
curl -H "Accept: application/json" https://icanhazdadjoke.com/
```

If it times out, your host may be blocking outbound HTTP/HTTPS.

---

## Groq API errors

Common Groq errors:

| Error | Cause | Fix |
|---|---|---|
| `401 Unauthorized` | Invalid API key | Re-copy key from console.groq.com |
| `429 Too Many Requests` | Rate limit hit | Wait — free tier has per-minute limits |
| `connection timeout` | Network issue | Check connectivity; bot will fall through to Gemini |

---

## Gemini API errors

| Error | Cause | Fix |
|---|---|---|
| `403 Forbidden` | Invalid or missing key | Re-copy from aistudio.google.com |
| `400 Bad Request` | Malformed request | Check `GEN1_MODEL` / `GEN2_MODEL` values in `nlp.py` match current Gemini model names (`gemini-1.5-flash-latest` / `gemini-flash-latest`) |
| `429 Too Many Requests` | Quota exceeded | Free tier has daily limits; wait or upgrade |

---

## On Raspberry Pi: bot doesn't start after reboot

**Check service status:**
```bash
sudo systemctl status ana-bot
journalctl -u ana-bot -n 50 --no-pager
```

**Common causes:**
- `.env` file missing — the script uses `EnvironmentFile=.env` which requires the file to exist
- Network not ready — the service waits for `network-online.target` but on some Pi configs this resolves before WiFi is fully up. Add a `ExecStartPre=/bin/sleep 5` to the service file as a workaround.
- Wrong working directory — ensure you ran `setup_autostart.sh` from the repo directory

**Re-run setup if needed:**
```bash
./setup_autostart.sh
```

The script is idempotent — safe to run again.

---

## Ana replies sound too much like an AI

`post_process()` in `nlp.py` strips most AI artefacts automatically (markdown, opener phrases, trailing periods, capital first letter). If you're still getting them:

1. Check the raw model output in the terminal — is it coming in already stripped?
2. Try overriding `SYSTEM_PROMPT` in `.env` with a stricter persona
3. The system prompt hard-bans: `Sure,` `Of course,` `Certainly,` `Absolutely,` `Great,` `Happy to,` `I understand,` `That makes sense,` — if the model is using something else, add it to `_RE_AI_OPENER` in `nlp.py`

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

## Profile not updating

Ana extracts profile info in the background after every reply using `GEN2_API_KEY`. If profiles aren't being populated or updated:

**Check 1: Is `GEN2_API_KEY` set?**

Profile extraction uses `GEN2_API_KEY`. If it's missing or invalid, extraction silently skips. Check `.env`:
```
GEN2_API_KEY=your_gemini_api_key_here
```

**Check 2: Check stderr output**

Ana prints extraction outcomes to `stderr`. Look for lines like:
```
[profile] No GEM2_API_KEY set, skipping extraction
[profile] No profile info extracted from message
[profile] Updated Kælith profile: age, location
[profile] Extraction failed for Kælith: 403
```
If you see `403`, the API key is invalid or not enabled. If you see `No profile info extracted`, the message was probably too short or contained no personal details.

**Check 3: Message too short**

Extraction only runs on messages over ~15 characters. Very short messages like `"ana lol"` are skipped.

**Check 4: Profile file location**

Profile files live in `data/profiles/{display-name}.json`. If the `data/profiles/` directory doesn't exist, Python creates it automatically on first write. Check the directory exists and you have write permissions.

---

## Reminder didn't fire / fired at wrong time

**Check 1: `!myreminders` to inspect**

Run `!myreminders` to see if the reminder was actually saved and what time it's set for. All times are IST.

**Check 2: Is the bot running continuously?**

The reminder check loop runs every 60 seconds. If the bot restarted after you set a reminder, the loop restarts and will catch due reminders on the next minute tick.

**Check 3: Is `GEN2_API_KEY` set?**

Reminder wish generation uses `GEN2_API_KEY`. If the key is missing, the bot can't generate the wish message and the reminder won't fire correctly. Check stderr for errors.

**Check 4: Was the channel deleted?**

Reminders fire to the channel where they were set. If that channel no longer exists, the reminder silently fails. You'll see a `discord.NotFound` in stderr.

**Check 5: Parsing a weird date**

Gemini resolves relative dates based on the current IST time at parse time. If you set a reminder for `"tomorrow 9am"` at 11 PM IST on March 19, it would resolve to March 20 at 9:00 AM IST. Confirm the resolved time with `!myreminders` immediately after setting.

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
