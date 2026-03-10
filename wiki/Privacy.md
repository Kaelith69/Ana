# Privacy

Ana is a Discord bot. Discord bots by nature receive messages. Here's exactly what Ana does (and doesn't do) with those messages.

---

## What Ana Reads

Ana receives all messages in channels where she has access — this is how Discord bots work. However, she only **acts** on messages that contain a trigger word.

From Discord's perspective, Ana has the following intents enabled:
- `messages` — receive message events
- `message_content` — read the actual text content of messages

---

## What Ana Does With Messages

### Messages containing a trigger word

1. The message content is passed to `process_with_nlp()`
2. It's lowercased for the trigger check, then the **original content** (truncated to 1000 characters) is sent to the primary AI API (Groq)
3. The message is not stored anywhere — it exists in memory only for the duration of the API call
4. The AI-generated reply is sent back to Discord

### Messages NOT containing a trigger word

1. The message is checked against the trigger word list and discarded
2. `maybe_send_joke()` is called — this doesn't use the message content at all, it just checks probability/cooldown/daily limit
3. No content from the message goes anywhere external

---

## What Data Is Stored

### Profile data

After every message Ana replies to, a background task sends that message to Gemini to extract personal details the user **explicitly stated** (name, age, location, favourites, interests, family mentions, facts). Anything extracted is deep-merged into a per-user JSON file:

```
data/profiles/{display-name}.json
```

This file persists on the host's disk across restarts. Fields that may be populated: `nickname`, `age`, `location`, `favorites` (game, show, food, music, other), `interests`, `family`, `facts`.

**What is NOT stored:** inferred information, message content verbatim, or anything not directly and explicitly stated by the user.

**To remove a profile:** delete the relevant `.json` file from `data/profiles/` on the host.

### Reminder data

When a user runs `!remindme`, the following is stored in `data/reminders/reminders.json`:

- Discord user ID
- Discord username
- Discord channel ID
- Target date/time (IST)
- Occasion text and inferred occasion type
- Any notes Gemini extracted
- A UUID4 reminder ID
- A `done` boolean flag

Fired reminders remain in the file with `done: true` (for audit). The file is on the host's local disk and persists across restarts.

### In-memory only (not written to disk)

- Conversation history (last 10 messages per channel)
- Per-user and per-channel cooldown timestamps
- Joke daily count and last-sent timestamps

All in-memory state is cleared on process restart.

---

## External Services

When Ana responds to a trigger word, the message content is sent to the AI API. Here's who gets what:

| Service | What's sent | Their Privacy Policy |
|---|---|---|
| Groq | Message content (≤1000 chars) for AI replies | [groq.com/privacy](https://groq.com/privacy) |
| Google Gemini (Gen1 — GEN1_API_KEY) | Message content (≤1000 chars) as AI reply fallback | [policies.google.com/privacy](https://policies.google.com/privacy) |
| Google Gemini (Gen2 — GEN2_API_KEY) | Message content for profile extraction (background); message content as AI reply fallback; reminder text for parsing; reminder record for wish generation | [policies.google.com/privacy](https://policies.google.com/privacy) |
| icanhazdadjoke.com | Nothing — it's a GET request with no user data | [icanhazdadjoke.com](https://icanhazdadjoke.com) |

**Important:** Groq and Google process this data according to their own privacy policies and terms of service. If this is a concern for your server, review those policies before deploying Ana.

---

## What Ana Doesn't Do

- ❌ No message content stored verbatim (only explicitly mentioned personal facts)
- ❌ No DMs initiated by the bot
- ❌ No data sold, shared, or exported
- ❌ No analytics collection

---

## For Server Admins

If you're deploying Ana on a server where members haven't consented to AI message processing, you should:

1. Inform members that the bot uses AI APIs when trigger words are detected
2. Inform members that personal details they explicitly mention **will be extracted and stored** by the AI in per-user profile files
3. Inform members that reminders they set are stored including their Discord user ID and channel
4. Consider the message content privacy implications for your server's use case
5. Review Groq's and Google's API terms for your jurisdiction's privacy regulations

Ana does not provide built-in consent management or per-user opt-out functionality. If you need that, you'll need to implement it. Profile files can be deleted manually from `data/profiles/`.

---

## API Keys

Your API keys live in `.env` and are never:
- Sent to Discord
- Logged to stdout in any readable form
- Committed to git (`.gitignore` handles this)

Keep your `.env` file private. Don't paste it in Discord. (You'd be surprised.)
