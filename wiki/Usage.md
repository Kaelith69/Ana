# Usage

How to actually use Ana once she's running.

---

## Commands

Ana uses the `!` prefix for explicit commands.

### `!joke`

Fetches a live dad joke from `icanhazdadjoke.com` and sends it to the channel.

```
You: !joke
Ana: Why don't scientists trust atoms? Because they make up everything.
```

No cooldown on this command — it's a direct request, not a random injection. Abuse responsibly.

---

### `!shutdown`

**Bot owner only.** Triggers Ana's dramatic farewell sequence and shuts down the process.

```
You: !shutdown
Ana: You… you're really pulling the plug, huh?
Ana: Tell the others I tried to make them laugh.
Ana: My circuits feel… cold.
Ana: *static crackle* goodbye… world... 🌌
[Bot goes offline]
```

If you're not the bot owner, this command is silently ignored.

**Who is the "bot owner"?** The user associated with the bot's application in the Discord Developer Portal — the account that created the bot. discord.py's `@commands.is_owner()` handles this automatically.

---

## Trigger Words

Ana responds to messages containing any of these keywords. Detection is case-insensitive and looks for the word *anywhere* in the message.

### Greetings & Time of Day
```
ana, hello, hi, hey, yo, sup
morning, goodmorning, gm, afternoon, goodafternoon
evening, goodevening, night, goodnight, gn
```

### Multilingual Greetings
```
namaste, hola, bonjour
```

### Farewells
```
bye, goodbye, takecare, see ya, seeya, cya, later
```

### Celebrations & Life Events
```
happybirthday, birthday, hbd, happybday
happyanniversary, congrats, congratulations, bestwishes
happynewyear, newyear, merrychristmas, christmas
eid, eidh, diwali, pongal, onam, holi, ramadan
valentines, valentine
happymarriedlife, wedding, engagement, babyshower, getwellsoon
```

### Emotions & Moods
```
sad, happy, tired, angry, bored, excited
```

### Slang & Reactions
```
lmao, omg, wow, bruh
```

### Example triggers
```
# These all fire Ana:
"good morning everyone!"
"hbd to our boy 🎂"
"I'm so tired today bruh"
"yo Ana what's good"
"omg did you see that"
```

---

## How AI Replies Work

When a trigger word is detected, Ana runs the full AI pipeline:

1. **Input prep** — The original message is passed to `process_with_nlp()`, truncated to 1000 characters
2. **Groq first** — Calls Groq's Llama-4 Scout model with a concise reply prompt. Temperature 1.0 for some personality. Max 400 tokens.
3. **Gemini Gen1 fallback** — If Groq fails (timeout, rate limit, error), calls `gemini-flash-lite-latest` via streaming API
4. **Gemini Gen2 fallback** — If Gen1 also fails, calls `gemini-2.5-flash-lite`
5. **Static fallback** — If all three fail, picks randomly from: `["Not sure what to say to that.", "Interesting...", "Well, that's something.", "Cool story, bro."]`

The system prompt tells the model to respond concisely in 1-2 lines with a casual, friendly tone. Ana doesn't write essays.

---

## Joke Behavior

The random joke system has three constraints stacked:

| Check | Value | Behavior |
|---|---|---|
| Cooldown | 60 seconds (default) | Won't send if a joke was sent in the last 60s |
| Random chance | 15% (default) | Even after cooldown clears, only 15% chance per message |
| Daily limit | 3 jokes | Resets at midnight UTC-ish (based on `time.time() // 86400`) |

All three must pass before a joke fires. This means:
- Low-traffic servers might go long stretches without a joke
- High-traffic servers won't get spammed
- The daily cap keeps it feeling like a surprise, not a routine

---

## Configuration Tuning

Adjust Ana's behavior via `.env`:

```env
# Make Ana more jokey (40% chance, no cooldown spam, 10/day)
JOKE_CHANCE=0.40
JOKE_COOLDOWN=30
# (daily limit is hardcoded at 3 — edit jokes.py to change it)

# Make Ana less jokey (5% chance, 5min cooldown)
JOKE_CHANCE=0.05
JOKE_COOLDOWN=300

# Increase API timeout if you're on slow hosting
JOKE_FETCH_TIMEOUT=15
```

Changes take effect on restart.
