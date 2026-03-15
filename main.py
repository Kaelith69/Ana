from __future__ import annotations
import asyncio
import datetime
import random
import re
import sys
from collections import defaultdict, deque
import discord
from discord.ext import commands, tasks
from config import DISCORD_TOKEN, JOKE_SETTINGS, TRIGGER_WORDS, ROAST_WORDS, FLIRT_WORDS, GEN2_API_KEY
from jokes import DadJokeService
from keepalive import start_keepalive
from nlp import process_with_nlp, _api_safe_name, FALLBACK_RESPONSES
from profiles import profile_store, extract_profile_info
from reminders import reminder_store, parse_reminder, generate_wish

TRIGGER_PATTERN = re.compile(r'\b(?:' + '|'.join(map(re.escape, TRIGGER_WORDS)) + r')\b', re.IGNORECASE)
ROAST_PATTERN = re.compile(r'\b(?:' + '|'.join(map(re.escape, sorted(ROAST_WORDS))) + r')\b', re.IGNORECASE)
FLIRT_PATTERN = re.compile(r'\b(?:' + '|'.join(map(re.escape, sorted(FLIRT_WORDS))) + r')\b', re.IGNORECASE)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

joke_service = DadJokeService(JOKE_SETTINGS)

# Per-channel conversation history: last 10 exchanges (20 messages)
_history: dict[int, deque] = defaultdict(lambda: deque(maxlen=20))

# Per-user last-reply timestamp (user_id -> monotonic time)
_user_last_reply: dict[int, float] = {}
USER_COOLDOWN = 25  # seconds between replies to the same user
MENTION_USER_COOLDOWN = 6  # shorter cooldown for explicit mentions to prevent mention spam floods

# Per-channel last-reply timestamp (channel_id -> monotonic time)
_channel_last_reply: dict[int, float] = {}
CHANNEL_COOLDOWN = 7  # seconds between any replies in the same channel

# Bound concurrent NLP calls to avoid thread-pool pressure under bursty traffic.
NLP_CONCURRENCY_LIMIT = 8
_nlp_semaphore = asyncio.Semaphore(NLP_CONCURRENCY_LIMIT)

# Strong references to in-flight background profile-extraction tasks.
# asyncio.create_task only keeps a weak ref — without this the task could be GC'd mid-run.
_bg_tasks: set[asyncio.Task] = set()

# Low-signal trigger words — Ana may silently ignore these sometimes
_LOW_SIGNAL = frozenset({
    "lmao", "omg", "wow", "bruh", "lol", "haha", "ok", "okay",
    "lmaooo", "lmaoo", "omfg", "hahaha", "rofl", "lolol",
})

# Context-sensitive emoji buckets — no heart emojis (system prompt forbids hearts with strangers)
_REACT_FUNNY    = ["💀", "😂", "🤣", "😭", "💅", "😩", "🤌"]          # lmao / haha / bruh / that was wild
_REACT_HYPE     = ["🔥", "✨", "💯", "😤", "🤌"]                       # fire / slay / let's go
_REACT_SAD      = ["😮‍💨", "🫥", "😑", "😐", "😞", "💀"]             # sad / rough / vent
_REACT_RELATABLE= ["💯", "😩", "😭", "🙄", "😤", "🫡"]                 # same / mood / real / literally
_REACT_WEIRD    = ["🤨", "😵", "🫠", "🤭", "👀", "😳"]                 # what / huh / idk / random
_REACT_CRINGE   = ["😬", "🤦", "🙄", "😐", "💀", "😑"]                 # cringe / gross / yikes / stop
_REACT_FLIRT    = ["😏", "🙃", "🤭", "😮", "👀"]                        # flirty content
_REACT_DEFAULT  = ["😭", "💀", "😂", "🙄", "😤", "🫠", "👀", "😮", "🤙",
                   "🤣", "💅", "😩", "🥺", "✨", "🔥", "😳", "🤦", "😵", "🫡",
                   "😬", "🤌", "🤭", "💯", "😑", "🧍", "🤷", "😏", "🫥", "😮‍💨", "🙃"]

# Keyword sets used by _pick_reaction.
# Rules for inclusion: words must be SPECIFIC to that mood and not ultra-common in normal chat.
# Emoji entries are excluded — they're stripped by re.sub(r'[^\w\s]',...) before matching.
_WORDS_FUNNY    = frozenset({"lol","lmao","lmaooo","lmaoo","haha","hahaha","funny","bruh",
                             "wild","omg","omfg","rofl","lolol","unhinged","chaotic"})
# "letsgo" excluded — never appears as one word; "crazy"/"insane" excluded — fire on negative msgs too
_WORDS_HYPE     = frozenset({"fire","banger","amazing","dope","goat","lit","slay","slaying","based"})
_WORDS_SAD      = frozenset({"sad","cry","crying","depressed","miss","hurt","pain",
                             "rough","vent","tired","exhausted","lonely","alone","upset"})
# "literally" excluded — appears in virtually every Gen-Z sentence regardless of mood
_WORDS_RELATABLE= frozenset({"same","mood","real","facts","fr","relatable","ngl","istg"})
# "what"/"why"/"idk" excluded — ultra-common in normal questions; would mis-fire constantly
_WORDS_WEIRD    = frozenset({"huh","random","weird","strange","wth","wtf"})
_WORDS_CRINGE   = frozenset({"cringe","gross","ew","eww","yikes","tragic","awful","cursed","embarrassing"})


def _pick_reaction(content: str, is_flirt: bool = False) -> str:
    """Pick a contextually appropriate emoji reaction.

    Checks message content against mood keyword sets in priority order:
    flirt > sad > cringe > funny > hype > weird > relatable > default.
    """
    if is_flirt:
        return random.choice(_REACT_FLIRT)
    words = set(re.sub(r'[^\w\s]', '', content.lower()).split())
    if words & _WORDS_SAD:
        return random.choice(_REACT_SAD)
    if words & _WORDS_CRINGE:
        return random.choice(_REACT_CRINGE)
    if words & _WORDS_FUNNY:
        return random.choice(_REACT_FUNNY)
    if words & _WORDS_HYPE:
        return random.choice(_REACT_HYPE)
    if words & _WORDS_WEIRD:
        return random.choice(_REACT_WEIRD)
    if words & _WORDS_RELATABLE:
        return random.choice(_REACT_RELATABLE)
    return random.choice(_REACT_DEFAULT)

# Follow-up lines Ana sends after a flirty exchange
_FLIRT_FOLLOWUPS = [
    "don't make me regret saying that",
    "ok don't read too much into that",
    "...i said what i said",
    "u better not disappoint",
    "ok moving on before i say something worse",
    "that was embarrassing of me",
    "ur actually dangerous wtf",
    "ok this conversation got out of hand fast",
    "don't get used to it",
    "i hate that i mean it",
    "we never speak of this again",
    "ok i'm normal i promise",
    "ur fault not mine",
    "anyway",
    "don't make it weird",
    "ok that was too honest of me ignore it",
    "i was NOT prepared for that",
    "this is ur fault entirely",
    "...okay but like",
    "u know what forget i said anything",
    "i keep saying things and meaning them which is a problem",
    "anyway how's ur day going lol",
    "okay i need to log off before i embarrass myself more",
    "don't look at me",
    "this is the last normal thing i'll say tonight",
    "i blame the hour",
    "ok we move",
    "pretend that didn't happen",
    "this is not representative of my usual behaviour",
    "i'm going now",
    "...yeah okay",
    "okay that was a lot from me. moving on.",
    "don't use that against me",
    "ok i take it back. no i don't.",
    "we're not discussing this further",
    "aiyyo okay fine. i said it.",
    "don't read into it. okay maybe you can. a little.",
    "that came out wrong and also completely right",
    "okay anyway where were we",
    "i'm logging off spiritually",
    "this is why i don't talk",
]

# Sharp follow-up lines Ana sends after firing back at a roast
_ROAST_FOLLOWUPS = [
    "and i meant every word",
    "don't come back",
    "i was being nice tbh",
    "💀",
    "go cry about it",
    "ok i'm done with u",
    "block me if ur mad",
    "that was free btw",
    "next",
    "try harder next time",
    "ur so cooked rn",
    "lmaooo byeee",
    "the disrespect. noted.",
    "anyway",
    "stay mad",
    "ok moving on from u",
    "i don't make the rules",
    "wasn't that hard",
    "u walked into that one",
    "take that home and think about it",
    "not my fault u came here",
    "ok bye",
    "sherikkum. anyway.",
    "the bar was right there and u still missed",
    "i barely tried ngl",
    "...ok next",
    "that was mercy",
    "aiyyo. go home.",
    "it wasn't even a hard one bro",
    "moving on with my life",
    "okay. noted. logging off from this interaction.",
    "i've already forgotten about it tbh",
    "the silence after is also part of it",
    "done here",
]

# Follow-up lines Ana might send a few seconds after her reply
_FOLLOWUPS = [
    "wait actually",
    "nvm ignore me",
    "okay but fr though",
    "...",
    "actually yeah",
    "idk why i said that",
    "ok moving on",
    "anyways",
    "no wait",
    "ok nvm lmao",
    "i take that back",
    "ok that came out wrong",
    "nvm nvm nvm",
    "ok but also",
    "wait no",
    "...wait",
    "no u know what",
    "ugh forget it",
    "ok anyway",
    "actually hold on",
    "idk i might be wrong",
    "lol nvm",
    "ok well",
    "whatever lol",
    "ok but hear me out",
    "omg wait",
    "nvm u don't get it",
    "ok i'm done talking about this",
    "this is so embarrassing for me",
    "okay no but",
    "...hm",
    "u know what forget it",
    "actually no i stand by it",
    "that sounded different in my head",
    "ok ngl",
    "i— nvm",
    "wait hold on",
    "okay yeah no",
    "aiyyo",
    "...okay anyway",
    "this has nothing to do with anything but",
    "not me immediately regretting that",
    "ok that was a lot",
    "no but genuinely",
    "anyway ignore the last thing",
    "actually scratch that",
    "ok i'm overthinking",
    "...nevermind lol",
    "i was going somewhere with that i swear",
    "okay this isn't going anywhere",
    "i have no follow-through i'm sorry",
    "ok wait no that came out like—",
    "aiyyo nvm",
    "literally why did i say that",
    "nm ignore that",
    "i think i meant something else",
    "okay that's not what i was going to say",
    "moving on before i make it worse",
    "ok forget the last message",
    "...you know what",
    "i should not have said that out loud",
    "that was unhinged of me",
    "ok i've moved on already",
]


_IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def _resolve_mentions(content: str, message: discord.Message) -> str:
    """Replace <@USER_ID> Discord mention tokens with human-readable @DisplayName."""
    if not message.guild or '<@' not in content:
        return content
    guild = message.guild  # captured for closure — guaranteed non-None at this point
    def _replace(m: re.Match) -> str:
        uid = int(m.group(1))
        member = guild.get_member(uid)
        return f"@{member.display_name}" if member else m.group(0)
    return re.sub(r'<@!?(\d+)>', _replace, content)


def _maybe_typo(text: str) -> tuple[str, str | None]:
    """~4% chance to swap two adjacent chars in a word and return a star-correction.

    Returns (possibly_typo_text, "*correct_word" or None).
    Contractions (don't, haven't, i'm, you're) are now eligible candidates —
    only the alphabetic base before the apostrophe is typo'd so the correction
    still reads naturally (e.g. "dno't" -> "*don't").
    """
    if random.random() >= 0.04:
        return text, None
    words = text.split()
    # Accept plain alpha words AND contractions (don't, haven't, i'm, you're, etc.)
    candidates = [
        (i, w) for i, w in enumerate(words)
        if len(w) >= 4 and re.match(r"^[a-zA-Z]+(?:'[a-zA-Z]+)?$", w)
    ]
    if not candidates:
        return text, None
    idx, word = random.choice(candidates)
    # Only swap chars in the alphabetic base (pre-apostrophe) to avoid mangling contractions
    base = word.split("'")[0]
    if len(base) < 3:
        return text, None
    pos = random.randint(1, len(base) - 2)
    new_base = base[:pos] + base[pos + 1] + base[pos] + base[pos + 2:]
    if new_base == base:
        return text, None
    typo_word = new_base + word[len(base):]
    words[idx] = typo_word
    return " ".join(words), f"*{word}"


def _split_reply(text: str) -> list[str]:
    """Split a reply into naturally-paced message chunks.

    Newline-separated thoughts always become separate Discord messages —
    Ana's voice has packets on their own lines, not walls of text.
    Single-line long replies are split at a sentence boundary near the midpoint.
    """
    # Always split on newlines — each thought packet = its own message
    parts = [p.strip() for p in text.split('\n') if p.strip()]
    if len(parts) > 1:
        return parts
    # Single-line only: split if long enough
    if len(text) < 120:
        return [text]
    mid = len(text) // 2
    for sep in (". ", "! ", "? ", "... ", ", "):
        idx = text.rfind(sep, 0, mid + 40)
        if idx != -1:
            # Skip if '. ' is the trailing dot of an ellipsis — same guard as post_process.
            if sep == ". " and idx >= 1 and text[idx - 1] == '.':
                continue
            cut = idx + len(sep)
            return [p for p in [text[:cut].strip(), text[cut:].strip()] if p]
    return [text]

async def _update_profile_bg(user_id: int, display_name: str, text: str) -> None:
    """Background task: extract personal details from a message and update the profile store.

    Runs via asyncio.create_task after Ana's reply is sent — never delays the response.
    """
    try:
        if not GEN2_API_KEY:
            print(f"[profile] skipped for {display_name!r}: GEN2_API_KEY not set", file=sys.stderr)
            return
        extracted = await asyncio.to_thread(extract_profile_info, text, GEN2_API_KEY)
        if extracted:
            await asyncio.to_thread(profile_store.update, user_id, display_name, extracted)
            print(f"[profile] updated {display_name!r}: {list(extracted.keys())}", file=sys.stderr)
        else:
            print(f"[profile] no info extracted for {display_name!r} (msg len={len(text)})", file=sys.stderr)
    except Exception as e:
        print(f"[profile] error for {display_name!r}: {e}", file=sys.stderr)


@bot.command()
@commands.is_owner()
async def shutdown(ctx):
    dramatic_lines = [
        "okay fine i'm going",
        "don't miss me too much lol",
        "bye i guess 💀",
        "...",
    ]
    for line in dramatic_lines:
        await ctx.send(line)
        await asyncio.sleep(1.5)
    await bot.close()

_JOKE_SETUPS = [
    "okay don't judge me",
    "wait i have one",
    "ok bear with me",
    "this is terrible and i love it",
    "i hate that this made me laugh",
    "you asked for this",
    "ok this one's bad. in a good way.",
    "u didn't hear this from me",
    "i've been holding this one in",
    "context: i've been awake too long",
    "ok i'm sorry in advance",
    "not me laughing at a dad joke again",
    "don't @ me for this",
]

_JOKE_OUTROS_CMD = [
    "i know i know",
    "...okay i'm embarrassed",
    "don't judge me",
    "ok moving on",
    "i regret nothing",
    "💀",
    "i'm hilarious",
    "u laughed. don't lie.",
    "ok anyway. that happened.",
    "no thoughts just that joke",
    "the delivery was what got me",
]


@bot.command(name="remindme")
async def remindme(ctx, *, text: str = ""):
    """Set a reminder. Usage: !remindme <date> <time> <occasion>"""
    if not text.strip():
        await ctx.send("tell me what to remind you about — date, time, and what's happening")
        return
    async with ctx.typing():
        reminder = await asyncio.to_thread(
            parse_reminder,
            text,
            ctx.author.id,
            ctx.author.display_name,
            ctx.channel.id,
            GEN2_API_KEY,
        )
    if not reminder:
        await ctx.send("couldn't parse that. try: `!remindme march 15 10am john's birthday`")
        return
    # Warn if the reminder is already in the past
    try:
        reminder_dt = datetime.datetime.fromisoformat(reminder["datetime_ist"]).replace(tzinfo=_IST)
        now_ist = datetime.datetime.now(_IST)
        if reminder_dt <= now_ist:
            await ctx.send("that date's already passed — double check and try again")
            return
        dt_fmt = reminder_dt.strftime("%d %b %Y at %I:%M %p IST")
    except Exception:
        dt_fmt = reminder["datetime_ist"]
    reminder_store.add(reminder)
    short_id = reminder["id"][:8]
    await ctx.send(
        f"ok set — {reminder['occasion']} on {dt_fmt} "
        f"\n*(cancel with `!cancelreminder {short_id}`)*"
    )


@bot.command(name="myreminders")
async def myreminders(ctx):
    """List your pending reminders."""
    pending = await asyncio.to_thread(reminder_store.list_pending, ctx.author.id)
    if not pending:
        await ctx.send("no reminders set")
        return
    lines = ["upcoming reminders:"]
    for r in pending:
        try:
            dt = datetime.datetime.fromisoformat(r["datetime_ist"]).replace(tzinfo=_IST)
            dt_str = dt.strftime("%d %b %Y %I:%M %p IST")
        except Exception:
            dt_str = r["datetime_ist"]
        short_id = r["id"][:8]
        lines.append(f"`{short_id}` — {r['occasion']} · {dt_str}")
    await ctx.send("\n".join(lines))


@bot.command(name="cancelreminder")
async def cancelreminder(ctx, id_prefix: str = ""):
    """Cancel a pending reminder by its ID prefix. Usage: !cancelreminder <id>"""
    if not id_prefix.strip():
        await ctx.send("give me the reminder id — use `!myreminders` to see them")
        return
    cancelled = await asyncio.to_thread(
        reminder_store.cancel, ctx.author.id, id_prefix.strip()
    )
    if cancelled:
        await ctx.send("reminder cancelled")
    else:
        await ctx.send("couldn't find that reminder — check `!myreminders`")


@bot.command()
async def joke(ctx):
    punchline = await asyncio.to_thread(joke_service.random_joke)
    if not punchline:
        await ctx.send("idk any rn try again later lol")
        return
    await ctx.send(random.choice(_JOKE_SETUPS))
    await asyncio.sleep(random.uniform(1.0, 2.0))
    async with ctx.typing():
        await asyncio.sleep(random.uniform(1.2, 2.2))
    await ctx.send(punchline)
    if random.random() < 0.55:
        await asyncio.sleep(random.uniform(1.5, 3.5))
        async with ctx.typing():
            await asyncio.sleep(random.uniform(0.4, 0.9))
        await ctx.send(random.choice(_JOKE_OUTROS_CMD))

@tasks.loop(hours=1)
async def _cleanup_cooldowns() -> None:
    """Periodically prune stale entries from the cooldown dicts and history to bound memory use."""
    now = asyncio.get_running_loop().time()
    stale_users = [uid for uid, ts in _user_last_reply.items() if now - ts > USER_COOLDOWN * 20]
    stale_channels = [cid for cid, ts in _channel_last_reply.items() if now - ts > CHANNEL_COOLDOWN * 20]
    for uid in stale_users:
        del _user_last_reply[uid]
    for cid in stale_channels:
        # Clean history at the same threshold so no entries are orphaned in _history
        # after the channel is dropped from _channel_last_reply.
        _history.pop(cid, None)
        del _channel_last_reply[cid]
    # Safety net: prune any history entries whose channel is no longer tracked
    # (e.g. from a previous run where cleanup was interrupted mid-cycle).
    for cid in [c for c in list(_history.keys()) if c not in _channel_last_reply]:
        _history.pop(cid, None)


@tasks.loop(minutes=1)
async def _check_reminders() -> None:
    """Fire due reminders every minute with AI-generated wish/reminder messages."""
    now_ist = datetime.datetime.now(_IST)
    due = await asyncio.to_thread(reminder_store.get_due, now_ist)
    for reminder in due:
        channel = bot.get_channel(reminder["channel_id"])
        if not isinstance(channel, discord.abc.Messageable):
            continue
        msg = await asyncio.to_thread(generate_wish, reminder, GEN2_API_KEY)
        if not msg:
            msg = f"hey — reminder: {reminder['occasion']}"
        try:
            user = bot.get_user(reminder["user_id"])
            if user is None:
                try:
                    user = await bot.fetch_user(reminder["user_id"])
                except (discord.HTTPException, OSError):
                    user = None
            mention = user.mention if user else f"@{reminder['user_name']}"
            await channel.send(f"{mention} {msg}")
            # Mark done only after a successful send so reminders are never dropped.
            await asyncio.to_thread(reminder_store.mark_done_if_pending, reminder["id"])
        except (discord.HTTPException, OSError) as e:
            print(f"[reminders] send failed for id={reminder.get('id')}: {e}", file=sys.stderr)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    if not _cleanup_cooldowns.is_running():
        _cleanup_cooldowns.start()
    if not _check_reminders.is_running():
        _check_reminders.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Process explicit commands (!joke, !shutdown) and exit immediately
    if message.content and message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return

    content = (message.content or "").lower()
    mentioned = bot.user in message.mentions
    # Roast/flirt words should independently trigger Ana, not just change her mode
    is_trigger = (mentioned
                  or bool(TRIGGER_PATTERN.search(content))
                  or bool(ROAST_PATTERN.search(content))
                  or bool(FLIRT_PATTERN.search(content)))
    
    if is_trigger:
        now = asyncio.get_running_loop().time()
        uid = message.author.id
        cid = message.channel.id

        # Strip punctuation to extract clean words for the low-signal subset check
        clean_content = re.sub(r'[^\w\s]', '', content)
        words = set(clean_content.split())

        # Detect roast/flirt early — roasts bypass all cooldowns and skip-chances
        is_roast = bool(ROAST_PATTERN.search(content))
        is_flirt = not is_roast and bool(FLIRT_PATTERN.search(content))

        # Compute these early — needed by both the extraction task below and the NLP path.
        author_name = re.sub(r'[\r\n\t\[\]"\\]', ' ', message.author.display_name).strip()[:50] or "user"
        resolved_content = _resolve_mentions(message.content or "", message)

        # Schedule background profile extraction for ALL triggered messages — not just text
        # replies. extract_profile_info silently skips short/empty content (<15 chars).
        # Placing this before the return branches ensures personal info is never lost just
        # because Ana chose to react, ghost-type, or was within a cooldown window.
        _bg_task = asyncio.create_task(_update_profile_bg(uid, author_name, resolved_content))
        _bg_tasks.add(_bg_task)
        _bg_task.add_done_callback(_bg_tasks.discard)

        # Silently skip ~20% of the time on low-signal words (never skip a roast)
        is_low_signal = not mentioned and bool(words) and words.issubset(_LOW_SIGNAL)
        if is_low_signal and not is_roast and random.random() < 0.20:
            return

        # Channel cooldown — don't pile on if she just replied here (roasts always go through)
        if not is_roast and now - _channel_last_reply.get(cid, 0) < CHANNEL_COOLDOWN:
            return

        # Per-user cooldown — mentions use a shorter throttle; roasts always bypass.
        _user_cooldown = MENTION_USER_COOLDOWN if mentioned else USER_COOLDOWN
        if not is_roast and now - _user_last_reply.get(uid, 0) < _user_cooldown:
            await asyncio.sleep(random.uniform(0.5, 2.5))  # humans don't react instantly
            try:
                await message.add_reaction(_pick_reaction(content, is_flirt))
            except (discord.HTTPException, OSError):
                pass
            return

        # ~12% chance to just react instead of replying (never on roasts — she always fires back)
        if not is_roast and random.random() < 0.12:
            try:
                await message.add_reaction(_pick_reaction(content, is_flirt))
            except (discord.HTTPException, OSError):
                pass
            _channel_last_reply[cid] = now
            return

        # ~6% chance of ghost typing — she starts typing then goes quiet
        # very human: read it, thought about it, decided not to engage
        if not is_roast and random.random() < 0.06:
            try:
                async with message.channel.typing():
                    await asyncio.sleep(random.uniform(1.5, 4.0))
            except (discord.HTTPException, OSError):
                pass
            _channel_last_reply[cid] = now
            return

        # ~10% chance to also react on top of reply (skip for roasts — no softening)
        if not is_roast and random.random() < 0.10:
            try:
                await message.add_reaction(_pick_reaction(content, is_flirt))
            except (discord.HTTPException, OSError):
                pass

        # Claim cooldown slots NOW — before any await that leads to the NLP call.
        # Without this, concurrent on_message handlers for rapid messages in the same
        # channel all see stale timestamps, all pass the cooldown check, all start NLP
        # calls (~console output appears), then all fire send() at once, Discord
        # rate-limits the burst and the excess replies are silently swallowed.
        # The late update below overwrites these with the accurate send timestamp.
        _pre_reserve = asyncio.get_running_loop().time()
        _channel_last_reply[cid] = _pre_reserve
        _user_last_reply[uid] = _pre_reserve

        # Load any profile data we already have for this user — passed to NLP for context
        user_profile_context = await asyncio.to_thread(profile_store.format_for_context, uid)

        # If this message is a Discord reply, inject the referenced message as context so
        # Ana knows who is being addressed / talked about — fixes group-chat confusion
        text_to_process = resolved_content
        if message.reference:
            ref_msg = None
            if isinstance(message.reference.resolved, discord.Message):
                ref_msg = message.reference.resolved
            elif message.reference.message_id:
                # Reference not yet in cache — fetch it (graceful fallback)
                try:
                    ref_msg = await message.channel.fetch_message(message.reference.message_id)
                except (discord.NotFound, discord.HTTPException):
                    pass
            if ref_msg:
                # Sanitize ref fields — prevent prompt injection from crafted content or display names
                ref_author = re.sub(r'[\r\n\t\[\]"\\]', ' ', ref_msg.author.display_name).strip()[:50]
                ref_raw = _resolve_mentions((ref_msg.content or "")[:200], ref_msg)
                ref_text = re.sub(r'[\r\n\t\[\]"\\]', ' ', ref_raw).strip()[:200]
                if ref_text:
                    text_to_process = (
                        f"[replying to @{ref_author}: \"{ref_text}\"]\n{resolved_content}"
                    )

        # Use .get() to avoid creating a spurious empty deque in the defaultdict
        # for channels where Ana has never replied — prevents unbounded memory growth.
        history = list(_history.get(cid, []))

        # Simulate reading the message before typing — humans don't react at network speed.
        # Proportional to message length; roasts fire back faster (she's already mad).
        if is_roast:
            read_delay = random.uniform(0.2, 0.7)
        else:
            read_delay = random.uniform(0.5, 1.2) + min(len(resolved_content) * 0.004, 1.8)
        try:
            await asyncio.sleep(read_delay)

            async with message.channel.typing():
                try:
                    async with _nlp_semaphore:
                        reply = await asyncio.wait_for(
                            asyncio.to_thread(
                                process_with_nlp,
                                text_to_process, history, author_name, is_roast, is_flirt,
                                user_profile_context,
                            ),
                            timeout=90.0,
                        )
                except asyncio.TimeoutError:
                    print(
                        f"[nlp] all APIs timed out after 90s for uid={uid} — using fallback",
                        file=sys.stderr,
                    )
                    reply = random.choice(FALLBACK_RESPONSES)
                # Roasts: fast angry typing (0.4-1.2s). Others: proportional to reply length.
                if is_roast:
                    extra = random.uniform(0.4, 1.2)
                elif reply:
                    length = len(reply)
                    if length < 60:
                        extra = random.uniform(0.8, 1.8)
                    elif length < 180:
                        extra = random.uniform(1.8, 3.5)
                    else:
                        extra = random.uniform(3.0, 5.0)
                else:
                    extra = random.uniform(0.5, 1.5)
                await asyncio.sleep(extra)
            if reply:
                _history[cid].append({
                    "role": "user",
                    "content": text_to_process,
                    "name": _api_safe_name(author_name),
                    "author": author_name,
                })
                _history[cid].append({"role": "assistant", "content": reply})
                # Use the actual current time so the cooldown reflects when the reply
                # was really sent, not the stale handler-start timestamp in `now`.
                _sent_at = asyncio.get_running_loop().time()
                _user_last_reply[uid] = _sent_at
                _channel_last_reply[cid] = _sent_at
                parts = _split_reply(reply)
                # Typo+correction only on non-roast replies (she's not typo-ing when she's mad)
                first_part, correction = _maybe_typo(parts[0]) if not is_roast else (parts[0], None)
                # When mentioned, always reply-thread. Otherwise ~65% reply, ~35% just send into channel.
                use_reply = mentioned or (random.random() < 0.65)
                if use_reply:
                    await message.reply(first_part, mention_author=False)
                else:
                    await message.channel.send(first_part)
                if correction and random.random() < 0.70:  # humans don't always catch their own typos
                    await asyncio.sleep(random.uniform(1.5, 3.0))
                    await message.channel.send(correction)
                for part in parts[1:]:
                    await asyncio.sleep(random.uniform(0.6, 1.2))
                    async with message.channel.typing():
                        await asyncio.sleep(random.uniform(0.4, 0.8) + len(part) * 0.018)
                    await message.channel.send(part)
                # Roasts: 25% chance of sharp follow-up; flirts: 20% chance of flustered follow-up; others: 8%
                if is_roast and random.random() < 0.25:
                    await asyncio.sleep(random.uniform(2.5, 5.0))
                    async with message.channel.typing():
                        await asyncio.sleep(random.uniform(0.4, 1.0))
                    await message.channel.send(random.choice(_ROAST_FOLLOWUPS))
                elif is_flirt and random.random() < 0.20:
                    await asyncio.sleep(random.uniform(3.0, 6.0))
                    async with message.channel.typing():
                        await asyncio.sleep(random.uniform(0.5, 1.2))
                    await message.channel.send(random.choice(_FLIRT_FOLLOWUPS))
                elif not is_roast and not is_flirt and random.random() < 0.08:
                    await asyncio.sleep(random.uniform(4.0, 8.0))
                    async with message.channel.typing():
                        await asyncio.sleep(random.uniform(0.5, 1.5))
                    await message.channel.send(random.choice(_FOLLOWUPS))
        except (discord.HTTPException, OSError) as _msg_err:
            print(f"[on_message] Discord/OS error (uid={uid}): {_msg_err}", file=sys.stderr)
    else:
        try:
            await joke_service.maybe_send_joke(message.channel)
        except (discord.HTTPException, OSError) as _joke_err:
            print(f"[joke] send failed in channel={message.channel.id}: {_joke_err}", file=sys.stderr)

@bot.event
async def on_command_error(ctx, error):
    """Prevent unhandled command errors from logging noisy tracebacks and give users feedback."""
    if isinstance(error, commands.NotOwner):
        return  # silently ignore — don't expose that owner-only commands exist
    if isinstance(error, commands.CommandNotFound):
        return  # ignore unknown commands — Ana uses free-form text, not a command bot
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"missing argument: `{error.param.name}`")
        return
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"slow down — try again in {error.retry_after:.0f}s")
        return
    # Log unexpected errors to stderr so they're visible in hosting logs
    print(f"[command_error] {ctx.command}: {error!r}", file=sys.stderr)


def main():
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN is missing. Please set it in your .env file.")
        sys.exit(1)
    start_keepalive()
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()
