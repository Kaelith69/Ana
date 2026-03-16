from __future__ import annotations
import asyncio
import datetime
import random
import re
import sys
from collections import defaultdict, deque
import discord
from discord.ext import commands, tasks
from config import DISCORD_TOKEN, JOKE_SETTINGS, TRIGGER_WORDS, ROAST_WORDS, FLIRT_WORDS
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

# Short fallback replies used when throttling or generation fails.
_BUSY_ACKS = [
    "one sec i'm catching up",
    "wait i'm here",
    "hold on, processing that",
    "i got u, give me a sec",
    "yeah i saw that",
    "here. i'm listening",
]


_IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
_SANITIZE_RE = re.compile(r'[\r\n\t\[\]"\\]')


def _sanitize_name(name: str, *, default: str = "user", limit: int = 50) -> str:
    """Sanitize display names before logging/prompt injection and cap length."""
    cleaned = _SANITIZE_RE.sub(' ', name).strip()[:limit]
    return cleaned or default


def _mark_reply_time(uid: int, cid: int, ts: float | None = None) -> None:
    """Update per-user and per-channel cooldown clocks with a single timestamp."""
    when = ts if ts is not None else asyncio.get_running_loop().time()
    _user_last_reply[uid] = when
    _channel_last_reply[cid] = when


def _restore_reply_time(
    uid: int,
    cid: int,
    prev_user_ts: float | None,
    prev_channel_ts: float | None,
) -> None:
    """Restore prior cooldown state when pre-reserved slots were never used."""
    if prev_user_ts is None:
        _user_last_reply.pop(uid, None)
    else:
        _user_last_reply[uid] = prev_user_ts

    if prev_channel_ts is None:
        _channel_last_reply.pop(cid, None)
    else:
        _channel_last_reply[cid] = prev_channel_ts


def _fallback_reply() -> str:
    """Centralized fallback reply selection used on generation/send failures."""
    return random.choice(FALLBACK_RESPONSES)


async def _build_reply_context(
    message: discord.Message,
    resolved_content: str,
    ref_msg: discord.Message | None = None,
) -> str:
    """Attach a compact referenced-message snippet when this is a Discord reply."""
    if not message.reference:
        return resolved_content

    if ref_msg is None:
        ref_msg = await _get_referenced_message(message)

    if not ref_msg:
        return resolved_content

    ref_author = _sanitize_name(ref_msg.author.display_name)
    ref_raw = _resolve_mentions((ref_msg.content or "")[:200], ref_msg)
    ref_text = _SANITIZE_RE.sub(' ', ref_raw).strip()[:200]
    if not ref_text:
        return resolved_content
    return f"[replying to @{ref_author}: \"{ref_text}\"]\n{resolved_content}"


async def _get_referenced_message(message: discord.Message) -> discord.Message | None:
    """Resolve the referenced message, fetching from API when it's not cached."""
    if not message.reference:
        return None
    if isinstance(message.reference.resolved, discord.Message):
        return message.reference.resolved
    if not message.reference.message_id:
        return None
    try:
        return await message.channel.fetch_message(message.reference.message_id)
    except (discord.NotFound, discord.HTTPException, OSError):
        return None
    except Exception as e:
        print(f"[reply-ref] unexpected fetch error in channel={message.channel.id}: {e}", file=sys.stderr)
        return None


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


async def _send_with_fallback(message: discord.Message, text: str, prefer_reply: bool) -> bool:
    """Best-effort message delivery with retry and channel-send fallback.

    Returns True if any send path succeeds, else False.
    """
    mode_reply = prefer_reply
    for attempt in range(1, 4):
        try:
            if mode_reply:
                await message.reply(text, mention_author=False)
            else:
                await message.channel.send(text)
            return True
        except (discord.HTTPException, OSError) as e:
            print(
                f"[send] attempt={attempt} reply_mode={mode_reply} channel={message.channel.id} error={e}",
                file=sys.stderr,
            )
            # If reply path fails, fallback to plain channel send on next attempt.
            mode_reply = False
            await asyncio.sleep(0.25 * attempt)
    return False

async def _update_profile_bg(user_id: int, display_name: str, text: str) -> None:
    """Background task: extract personal details from a message and update the profile store.

    Runs via asyncio.create_task after Ana's reply is sent — never delays the response.
    """
    try:
        extracted = await asyncio.to_thread(extract_profile_info, text)
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
    channel_cache: dict[int, discord.abc.Messageable | None] = {}
    mention_cache: dict[int, str] = {}
    for reminder in due:
        channel_id = reminder["channel_id"]
        channel = channel_cache.get(channel_id)
        if channel is None and channel_id not in channel_cache:
            candidate = bot.get_channel(channel_id)
            channel = candidate if isinstance(candidate, discord.abc.Messageable) else None
            channel_cache[channel_id] = channel

        if channel is None:
            continue

        msg = await asyncio.to_thread(generate_wish, reminder)
        if not msg:
            msg = f"hey — reminder: {reminder['occasion']}"
        try:
            user_id = reminder["user_id"]
            mention = mention_cache.get(user_id)
            if mention is None:
                user = bot.get_user(user_id)
                if user is None:
                    try:
                        user = await bot.fetch_user(user_id)
                    except (discord.HTTPException, OSError):
                        user = None
                mention = user.mention if user else f"@{reminder['user_name']}"
                mention_cache[user_id] = mention

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

    raw_content = message.content or ""
    mentioned = bot.user in message.mentions
    now = asyncio.get_running_loop().time()
    uid = message.author.id
    cid = message.channel.id

    is_roast = bool(ROAST_PATTERN.search(raw_content))
    is_flirt = not is_roast and bool(FLIRT_PATTERN.search(raw_content))
    is_trigger = bool(TRIGGER_PATTERN.search(raw_content))

    # Only engage if @mentioned, trigger/roast/flirt word is present,
    # or this message is a Discord reply specifically to one of Ana's own messages.
    ref_msg = await _get_referenced_message(message)
    is_reply_to_ana = bool(ref_msg and bot.user and ref_msg.author.id == bot.user.id)
    if not (mentioned or is_trigger or is_roast or is_flirt or is_reply_to_ana):
        return

    author_name = _sanitize_name(message.author.display_name)
    resolved_content = _resolve_mentions(raw_content, message)

    # Always schedule extraction so every user message can contribute profile context.
    _bg_task = asyncio.create_task(_update_profile_bg(uid, author_name, resolved_content))
    _bg_tasks.add(_bg_task)
    _bg_task.add_done_callback(_bg_tasks.discard)

    # Throttle bursts, but never drop a message: return a short acknowledgement.
    _user_cooldown = MENTION_USER_COOLDOWN if mentioned else USER_COOLDOWN
    if not is_roast and (
        now - _channel_last_reply.get(cid, 0) < CHANNEL_COOLDOWN
        or now - _user_last_reply.get(uid, 0) < _user_cooldown
    ):
        ack = random.choice(_BUSY_ACKS)
        sent = await _send_with_fallback(message, ack, prefer_reply=mentioned or bool(message.reference))
        if sent:
            _mark_reply_time(uid, cid)
        return

    # Reserve cooldown slots before long-running NLP work to prevent fan-out races.
    prev_user_ts = _user_last_reply.get(uid)
    prev_channel_ts = _channel_last_reply.get(cid)
    _pre_reserve = asyncio.get_running_loop().time()
    _mark_reply_time(uid, cid, _pre_reserve)

    user_profile_context = await asyncio.to_thread(profile_store.format_for_context, uid)

    text_to_process = await _build_reply_context(message, resolved_content, ref_msg=ref_msg)

    history = list(_history.get(cid, []))
    read_delay = random.uniform(0.2, 0.7) if is_roast else random.uniform(0.4, 1.0) + min(len(resolved_content) * 0.003, 1.2)

    sent_any = False
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
                print(f"[nlp] all APIs timed out after 90s for uid={uid} — using fallback", file=sys.stderr)
                reply = _fallback_reply()
            except Exception as e:
                print(f"[nlp] generation error for uid={uid}: {e}", file=sys.stderr)
                reply = _fallback_reply()

            if not reply or not str(reply).strip():
                reply = _fallback_reply()

            length = len(reply)
            if is_roast:
                extra = random.uniform(0.4, 1.1)
            elif length < 60:
                extra = random.uniform(0.7, 1.5)
            elif length < 180:
                extra = random.uniform(1.2, 2.6)
            else:
                extra = random.uniform(2.0, 3.6)
            await asyncio.sleep(extra)

        _history[cid].append({
            "role": "user",
            "content": text_to_process,
            "name": _api_safe_name(author_name),
            "author": author_name,
        })
        _history[cid].append({"role": "assistant", "content": reply})

        _mark_reply_time(uid, cid)

        parts = _split_reply(reply)
        first_part, correction = _maybe_typo(parts[0]) if not is_roast else (parts[0], None)
        use_reply = mentioned or bool(message.reference) or (random.random() < 0.65)

        sent_any = await _send_with_fallback(message, first_part, prefer_reply=use_reply)

        if sent_any and correction and random.random() < 0.70:
            await asyncio.sleep(random.uniform(1.2, 2.4))
            await _send_with_fallback(message, correction, prefer_reply=False)

        if sent_any:
            for part in parts[1:]:
                await asyncio.sleep(random.uniform(0.5, 1.0))
                async with message.channel.typing():
                    await asyncio.sleep(random.uniform(0.3, 0.7) + len(part) * 0.014)
                await _send_with_fallback(message, part, prefer_reply=False)

            if is_roast and random.random() < 0.20:
                await asyncio.sleep(random.uniform(2.2, 4.0))
                await _send_with_fallback(message, random.choice(_ROAST_FOLLOWUPS), prefer_reply=False)
            elif is_flirt and random.random() < 0.16:
                await asyncio.sleep(random.uniform(2.5, 5.0))
                await _send_with_fallback(message, random.choice(_FLIRT_FOLLOWUPS), prefer_reply=False)
            elif not is_roast and not is_flirt and random.random() < 0.06:
                await asyncio.sleep(random.uniform(3.0, 6.0))
                await _send_with_fallback(message, random.choice(_FOLLOWUPS), prefer_reply=False)

    except Exception as _msg_err:
        print(f"[on_message] unexpected error (uid={uid}, channel={cid}): {_msg_err}", file=sys.stderr)

    # Final guarantee: try to send at least one fallback response for every user message.
    if not sent_any:
        fallback = _fallback_reply()
        sent_any = await _send_with_fallback(message, fallback, prefer_reply=mentioned or bool(message.reference))
        if sent_any:
            _mark_reply_time(uid, cid)
        else:
            _restore_reply_time(uid, cid, prev_user_ts, prev_channel_ts)

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
