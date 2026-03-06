# Usage

How to actually use Ana once she's running.

---

## Commands

Ana uses the `!` prefix for explicit commands.

### `!joke`

Fetches a live dad joke from `icanhazdadjoke.com` and sends it to the channel. Bypasses the random chance, cooldown, and daily cap — it's a direct request.

```
You: !joke
Ana: Why don't scientists trust atoms? Because they make up everything.
```

If the joke API is unreachable:
```
Ana: idk any rn try again later lol
```

---

### `!shutdown`

**Bot owner only.** Ana says a quick casual goodbye and shuts down cleanly.

```
You: !shutdown
Ana: okay fine i'm going
Ana: don't miss me too much lol
Ana: bye i guess 💀
Ana: ...
[Bot goes offline]
```

If you're not the bot owner, the command is silently ignored.

**Who is the bot owner?** The account that created the application in the Discord Developer Portal. `discord.py`'s `@commands.is_owner()` resolves this automatically — no config needed.

---

## Trigger Words

Ana responds to messages containing any of these keywords. Detection is case-insensitive and matches anywhere in the message.

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

---

## Roast Mode

When a message contains a roast/insult word, Ana switches into comeback mode. This is a fundamentally different code path:

- **Bypasses all cooldowns** — she always fires back, even if she just replied to that person
- **Faster typing** — 0.4–1.2s (vs proportional for normal replies)
- **Higher AI temperature** — 1.3 (Groq) / 1.4 (Gemini) for more creative, unpredictable comebacks
- **Specific ROAST_PROMPT** — instructs the model to use the person's own words against them, escalate, never soften or apologise
- **25% chance of a sharp follow-up** 2.5–5s later (e.g. `"and i meant every word"`, `"stay mad"`, `"u walked into that one"`)
- **No typo-correction** on roast replies — she's not fumbling when she's mad
- **No extra emoji overlay** — no softening the blow

```
User: ur so stupid lol
Ana:  the bar was already underground and you somehow dug lower
Ana:  (4s later) that was free btw
```

### Roast trigger words (sample)
```
stupid, idiot, dumb, trash, useless, ugly, mid, cringe, loser, fake,
rat, clown, nerd, pathetic, boring, stfu, kys, cope, ratio, nobody asked,
skill issue, cooked, npc, flop, delulu, simp, touch grass, take the L,
who asked, get rekt, trash tier, delete yourself, go outside, and 30+ more
```

---

## Flirt Mode

When a message contains a flirt word (and no roast word — roast takes priority), Ana responds with a creative, improvised pick-up line or flirty tease.

- **Original lines only** — grounded in their actual message where possible, no cliché formats
- **Varies style** — confident compliment, power-move, mildly suggestive, dry/unimpressed-but-interested
- **NSFW-capable** — double meanings, innuendo, suggestive metaphors if the vibe calls for it
- **20% chance of a flustered follow-up** 3–6s later (e.g. `"i hate that i mean it"`, `"ur fault not mine"`, `"we never speak of this again"`)

```
User: ok but ur actually kinda cute
Ana:  bold of u to flirt with me like u can handle what comes next
Ana:  (5s later) ok i'm normal i promise
```

### Flirt trigger words (sample)
```
cute, pretty, beautiful, gorgeous, hot, sexy, crush, date, kiss, hug,
love you, miss you, rizz, babe, baby, darling, wanna go out, be mine,
dream girl, thicc, baddie, smooth, pickup, finesse, and more
```

---

## Behaviour Nuances (Human-sounding)

These are all the small things that make Ana feel like a real member rather than a bot:

| Behaviour | Details |
|---|---|
| **Proportional typing delay** | <60 chars → 0.8–1.8s extra; 60–180 chars → 1.8–3.5s; >180 chars → 3.0–5.0s |
| **Typo + correction** | ~4% of replies: sends with a character-swap typo, then sends `*word` 1.5–3s later |
| **Emoji-only reaction** | ~12% of non-roast triggers: adds a single emoji reaction instead of replying |
| **Low-signal skip** | ~15% chance to silently ignore messages that are only `lmao`, `omg`, `wow` etc. |
| **Follow-up afterthoughts** | 8% (normal), 25% (roast), 20% (flirt) chance of a second message sent 3–8s later |
| **Conversation history** | Last 10 messages per channel passed as context — Ana remembers what was just said |
| **Per-user cooldown** | 25s between replies to the same person (bypassed on roasts) |
| **Per-channel cooldown** | 7s between any replies in a channel (bypassed on roasts) |
| **"Seen" reaction** | During per-user cooldown: adds 👀 💀 😭 instead of replying |

---

## How AI Replies Work

When a trigger is detected, Ana runs:

1. **Input prep** — message passed to `process_with_nlp()`, truncated at 1000 chars. Author name sanitised (strips newlines, max 50 chars) to prevent prompt injection via crafted display names.
2. **Mode selection** — `ROAST_PROMPT`, `FLIRT_PROMPT`, or `SYSTEM_PROMPT` chosen based on detected mode
3. **Groq first** — Llama-4 Scout, temperature 1.1 (normal) / 1.3 (roast), max 200 tokens
4. **Gemini Gen1 fallback** — `gemini-1.5-flash-latest`, temperature 1.2 / 1.4 (roast), max 200 tokens
5. **Gemini Gen2 fallback** — `gemini-2.5-flash-lite`, same settings
6. **Static fallback** — random choice from a pool of human-sounding short phrases
7. **`post_process()`** — strips markdown, AI opener phrases, trailing periods, capitalised first letter

### Static fallback pool (sample)
```
"idk what to say lol"
"ok but like... same"
"wait what"
"girl idk"
"..."
"yeah no"
"no yeah"
"wait explain"
```

---

## Joke Behaviour

The random joke system has three stacked constraints:

| Check | Default | Config key |
|---|---|---|
| Cooldown | 60 seconds | `JOKE_COOLDOWN` |
| Random chance | 15% | `JOKE_CHANCE` |
| Daily limit | 3 jokes | hardcoded in `DadJokeService` |

All three must pass before a joke fires. The daily count resets automatically when the day rolls over.

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
