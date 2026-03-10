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

### `!remindme <text>`

Set a reminder using natural language. Gemini parses the text into a structured reminder using the current IST time as reference.

```
You:  !remindme march 20 10am mum's birthday
Ana:  done ✅ i'll remind you on Mar 20 at 10:00 AM IST — mum's birthday
      (to cancel: !cancelreminder abc12345)
```

Examples of text Gemini can parse:
- `!remindme tomorrow 9am team meeting`
- `!remindme 25th dec christmas`
- `!remindme next friday 6pm dinner with friends`
- `!remindme 10 mins before my exam at 3pm` *(approximate)*

At the specified time, Ana will @mention you in the same channel with an AI-generated message in her voice — a birthday wish, exam pep-talk, or casual heads-up depending on the occasion type.

---

### `!myreminders`

Lists all your pending (not yet fired) reminders with their short IDs and scheduled IST times.

```
You:  !myreminders
Ana:  your pending reminders:
      • abc12345 — Mar 20 10:00 AM — mum's birthday
      • ff994421 — Dec 25 12:00 AM — christmas
```

---

### `!cancelreminder <id>`

Cancels a pending reminder by its short ID (the 8-character prefix shown in `!my reminders`).

```
You:  !cancelreminder abc12345
Ana:  reminder cancelled.
```

You can only cancel your own reminders.

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

## Profile Memory

Ana silently learns about members over time. After every reply, she sends the triggering message to Gemini in a background task (never on the reply path — it doesn't slow anything down) to extract personal details the person explicitly shared.

**What gets stored:** nickname, age, location, favourite games/shows/music/food, interests, family mentions, and miscellaneous facts.

**What doesn't get stored:** anything inferred, assumed, or not directly stated. If you didn't say it, it won't be recorded.

**Where it lives:** `data/profiles/{name}.json` — one file per user, on the host's local disk. Profile files persist across restarts.

**How it's used:** When Ana replies to someone with a stored profile, she gets a compact one-line summary injected into the system prompt:
```
[what you know about Kælith: age 22 · from Bengaluru · faves — game: Minecraft · music: indie pop · interests: anime, coding]
```
This lets her reference things you've mentioned before — naturally, without announcing it.

**To clear your profile:** Delete `data/profiles/{your-display-name}.json` from the host's filesystem. The file path is displayed in the stderr log when extraction runs.

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
| **Reading delay** | Before typing starts: 0.2–0.7s (roast) or 0.5–3s proportional to message length (normal). Simulates reading before replying. |
| **Proportional typing delay** | <60 chars → 0.8–1.8s extra; 60–180 chars → 1.8–3.5s; >180 chars → 3.0–5.0s |
| **Typo + correction** | ~4% of replies: sends with a character-swap typo, then sends `*word` 1.5–3s later (correction only appears ~70% of the time) |
| **Emoji-only reaction** | ~12% of non-roast triggers: adds a single emoji reaction instead of replying |
| **Low-signal skip** | ~20% chance to silently ignore messages that are only `lmao`, `omg`, `wow` etc. |
| **Ghost typing** | ~6% chance she starts typing then goes quiet — read it, thought about it, decided not to engage |
| **Follow-up afterthoughts** | 8% (normal), 25% (roast), 20% (flirt) chance of a second message sent 3–8s later |
| **Conversation history** | Last 10 messages per channel passed as context with per-speaker attribution — Ana knows who said what |
| **Group chat context** | Responds to the person, not the room. Never recaps what someone said. Stays out of conversations not addressed to her. |
| **Per-user cooldown** | 25s between replies to the same person (bypassed on roasts) |
| **Per-channel cooldown** | 7s between any replies in a channel (bypassed on roasts) |
| **"Seen" reaction** | During per-user cooldown: adds 👀 💀 😭 instead of replying |

---

## Group Chat & Multi-User Awareness

Ana is designed for active group channels where multiple people are talking at once.

**Mention resolution** — Discord sends mentions as raw `<@USER_ID>` tokens. Ana resolves all mentions to real display names before passing text to the AI, so the model sees `@Kælith` instead of `<@123456789>`.

**Reply-thread context** — When someone replies to another message, Ana fetches that referenced message and prepends it as context:
```
[replying to @UserA: "original message here"]
Actual message from UserB
```
This means Ana always knows *who they're replying to* and *what was originally said*.

**Per-speaker history** — Every entry in the conversation history carries the speaker's name. The AI sees `[UserA]: text` and `[UserB]: text` — not anonymous blobs. Groq receives them via the `name` field on each message object.

**Group chat instructions** — A dedicated `GROUP CHAT` section in the system prompt tells the model to:
- Respond to the person, not the room
- Reference others by name when natural
- Stay out when two people are talking to each other
- Never recap what someone just said
- Never address "everyone" or "the group" or "the server"

---



When a trigger is detected, Ana runs:

1. **Input prep** — `_resolve_mentions()` replaces `<@ID>` tokens with display names. If the message is a Discord reply, referenced message is fetched and prepended as `[replying to @Name: "..."]`. Text is truncated at 1000 chars. Author name sanitised to prevent prompt injection.
2. **Mode selection** — `ROAST_PROMPT`, `FLIRT_PROMPT`, or `SYSTEM_PROMPT` chosen based on detected mode
3. **Reading delay** — Before the typing indicator: 0.2–0.7s (roast) or 0.5–3s proportional to message length
4. **Groq waterfall** — Tries each model in order until one succeeds:
   - Kimi K2 (`moonshotai/kimi-k2-instruct`) — temp 0.85 normal / ~1.1 roast
   - Llama 3.3 70B (`meta-llama/llama-3.3-70b-versatile`) — temp 0.82
   - Llama 4 Scout (`meta-llama/llama-4-scout-17b-16e-instruct`) — temp 0.88
   - Qwen 3 32B (`qwen/qwen3-32b`) — temp 0.82; all max 200 tokens
5. **Gemini Gen1 fallback** — `gemini-1.5-flash-latest`, temperature 1.2 / 1.4 (roast), max 200 tokens
6. **Gemini Gen2 fallback** — `gemini-flash-latest`, same settings
7. **Static fallback** — random choice from a pool of human-sounding short phrases
8. **`post_process()`** — strips markdown, AI openers, context-injection echoes, name-prefix echoes, stage-direction parens `(laughs)`, trailing periods, capitalised first letter

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
