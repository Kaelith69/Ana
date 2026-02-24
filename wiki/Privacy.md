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

**Nothing.** Ana has no database, no log files, no persistent storage of messages.

- No message content is written to disk
- No user IDs are stored beyond runtime in-memory state
- The joke service stores only timestamps and a count (no user data) in memory
- Process restart clears all runtime state

---

## External Services

When Ana responds to a trigger word, the message content is sent to the AI API. Here's who gets what:

| Service | What's sent | Their Privacy Policy |
|---|---|---|
| Groq | Message content (≤1000 chars) | [groq.com/privacy](https://groq.com/privacy) |
| Google Gemini | Message content (≤1000 chars) | [policies.google.com/privacy](https://policies.google.com/privacy) |
| icanhazdadjoke.com | Nothing — it's a GET request with no user data | [icanhazdadjoke.com](https://icanhazdadjoke.com) |

**Important:** Groq and Google process this data according to their own privacy policies and terms of service. If this is a concern for your server, review those policies before deploying Ana.

---

## What Ana Doesn't Do

- ❌ No message logging to files or databases
- ❌ No user profile tracking
- ❌ No DMs initiated by the bot
- ❌ No data sold, shared, or exported
- ❌ No analytics collection

---

## For Server Admins

If you're deploying Ana on a server where members haven't consented to AI message processing, you should:

1. Inform members that the bot uses AI APIs when trigger words are detected
2. Consider the message content privacy implications for your server's use case
3. Review Groq's and Google's API terms for your jurisdiction's privacy regulations

Ana does not provide built-in consent management or per-user opt-out functionality. If you need that, you'll need to implement it.

---

## API Keys

Your API keys live in `.env` and are never:
- Sent to Discord
- Logged to stdout in any readable form
- Committed to git (`.gitignore` handles this)

Keep your `.env` file private. Don't paste it in Discord. (You'd be surprised.)
