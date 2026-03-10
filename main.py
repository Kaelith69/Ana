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
from nlp import process_with_nlp
from profiles import profile_store, extract_profile_info

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

# Per-channel last-reply timestamp (channel_id -> monotonic time)
_channel_last_reply: dict[int, float] = {}
CHANNEL_COOLDOWN = 7  # seconds between any replies in the same channel

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


# ---------------------------------------------------------------------------
# Sleep / wake routine
# ---------------------------------------------------------------------------

_IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

# Persistent channel ID for sleep/wake announcements.
# Unlike _channel_last_reply, this is NEVER pruned by the cleanup task —
# so _ana_wake() can always find the last active channel even after the
# 5.5h idle sleep window empties _channel_last_reply.
_announcement_channel_id: int | None = None


def _is_sleeping() -> bool:
    """Return True during Ana's sleep window: 00:00–05:29 IST."""
    now = datetime.datetime.now(_IST)
    return now.hour < 5 or (now.hour == 5 and now.minute < 30)


def _best_channel():
    """Return the most recently active TextChannel Ana has spoken in, or None."""
    # Prefer _channel_last_reply (most recent activity) but fall back to the
    # persistent _announcement_channel_id which is never pruned by cleanup.
    cid: int | None = None
    if _channel_last_reply:
        cid = max(_channel_last_reply, key=lambda k: _channel_last_reply[k])
    elif _announcement_channel_id is not None:
        cid = _announcement_channel_id
    if cid is None:
        return None
    ch = bot.get_channel(cid)
    # Guard: only return the channel if it's actually messageable (not a voice/category channel).
    if isinstance(ch, discord.abc.Messageable):
        return ch
    return None


_SLEEP_AFK_RESPONSES = [
    "i'm literally asleep rn",
    "zzz",
    "asleep. come back after 5:30.",
    "i cannot with you rn. sleeping.",
    "not available. sleeping.",
    "...sleeping bro",
    "it's the middle of the night what do you want",
    "asleep. bye.",
    "i'm offline till morning",
    "do not disturb. genuinely.",
]

_GOODNIGHT_LINES = [
    "okay i'm going. gn everyone.",
    "aiyyo it's midnight. gn.",
    "ok gn. don't do anything stupid while i'm gone.",
    "sleep is pulling me. gn 💀",
    "ok i'm logging off. gn.",
    "goodnight. don't miss me too much.",
    "it's that time. gn.",
    "ok i'm done for the night. gn.",
    "gn. try not to implode without me.",
    "alright i'm out. gn everyone.",
    "okay i'm disappearing now. gn.",
    "tired. gn.",
    "gn. don't be weird while i'm asleep.",
    "ok logging off. this was a choice.",
    "aiyyo getting offline. gn.",
    "sleepy. bye.",
    "can't keep my eyes open. gn everyone.",
    "okay going now. gn.",
    "i'm out. gn. behave.",
    "gn. i'd say see u tomorrow but that's technically today now.",
]

_GOODMORNING_LINES = [
    "ok i'm back. barely.",
    "it is 5:30am and i've made a terrible decision to be awake.",
    "gm i guess.",
    "ok i'm here. gm.",
    "aiyyo morning.",
    "gm. don't talk to me for 20 minutes.",
    "ok i'm awake. somehow.",
    "back. don't make me regret it.",
    "gm. coffee first, everything else later.",
    "morning. i'll be human in approximately one cup.",
    "okay woke up. barely counts but here we are.",
    "aiyyo it's early. gm.",
    "gm. don't expect too much from me yet.",
    "technically awake.",
    "alive. questionably. gm.",
    "gm. the sun has no right to be that bright.",
    "back. not happy about it but back.",
    "ok good morning or whatever. still waking up.",
    "aiyyo. peak hours resuming.",
]


def _sanitize_name_for_api(name: str) -> str:
    """Return an API-safe participant name: a-z, A-Z, 0-9, underscores only, max 64 chars.

    Required for the OpenAI/Groq 'name' field in chat messages.
    """
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    sanitized = re.sub(r'_+', '_', sanitized).strip('_')
    return (sanitized or "user")[:64]


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
    All failures are completely silent.
    """
    try:
        extracted = await asyncio.to_thread(extract_profile_info, text, GEN2_API_KEY)
        if extracted:
            await asyncio.to_thread(profile_store.update, user_id, display_name, extracted)
    except Exception:
        pass


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
    sys.exit(0)

@bot.command()
async def joke(ctx):
    punchline = await asyncio.to_thread(joke_service.random_joke)
    if not punchline:
        await ctx.send("idk any rn try again later lol")
        return
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
    _JOKE_OUTROS = [
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
    await ctx.send(random.choice(_JOKE_SETUPS))
    await asyncio.sleep(random.uniform(1.0, 2.0))
    async with ctx.typing():
        await asyncio.sleep(random.uniform(1.2, 2.2))
    await ctx.send(punchline)
    if random.random() < 0.55:
        await asyncio.sleep(random.uniform(1.5, 3.5))
        async with ctx.typing():
            await asyncio.sleep(random.uniform(0.4, 0.9))
        await ctx.send(random.choice(_JOKE_OUTROS))

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


@tasks.loop(time=datetime.time(hour=0, minute=0, second=0, tzinfo=_IST))
async def _ana_sleep() -> None:
    """Send a goodnight message at midnight IST."""
    ch = _best_channel()
    if ch is None:
        return
    try:
        async with ch.typing():
            await asyncio.sleep(random.uniform(0.8, 1.8))
        await ch.send(random.choice(_GOODNIGHT_LINES))
    except (discord.HTTPException, OSError):
        pass


@tasks.loop(time=datetime.time(hour=5, minute=30, second=0, tzinfo=_IST))
async def _ana_wake() -> None:
    """Send a goodmorning message at 05:30 IST."""
    ch = _best_channel()
    if ch is None:
        return
    try:
        async with ch.typing():
            await asyncio.sleep(random.uniform(1.0, 2.0))
        await ch.send(random.choice(_GOODMORNING_LINES))
    except (discord.HTTPException, OSError):
        pass


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    if not _cleanup_cooldowns.is_running():
        _cleanup_cooldowns.start()
    if not _ana_sleep.is_running():
        _ana_sleep.start()
    if not _ana_wake.is_running():
        _ana_wake.start()

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
        # Sleep guard — Ana is unavailable during her sleep window (00:00–05:29 IST).
        # No LLM calls are made; a static AFK message is sent instead.
        if _is_sleeping():
            await asyncio.sleep(random.uniform(0.4, 1.2))
            try:
                await message.channel.send(random.choice(_SLEEP_AFK_RESPONSES))
            except (discord.HTTPException, OSError):
                pass
            return

        now = asyncio.get_running_loop().time()
        uid = message.author.id
        cid = message.channel.id

        # Strip punctuation to extract clean words for the low-signal subset check
        clean_content = re.sub(r'[^\w\s]', '', content)
        words = set(clean_content.split())

        # Detect roast/flirt early — roasts bypass all cooldowns and skip-chances
        is_roast = bool(ROAST_PATTERN.search(content))
        is_flirt = not is_roast and bool(FLIRT_PATTERN.search(content))

        # Silently skip ~20% of the time on low-signal words (never skip a roast)
        is_low_signal = not mentioned and bool(words) and words.issubset(_LOW_SIGNAL)
        if is_low_signal and not is_roast and random.random() < 0.20:
            return

        # Channel cooldown — don't pile on if she just replied here (roasts always go through)
        if not mentioned and not is_roast and now - _channel_last_reply.get(cid, 0) < CHANNEL_COOLDOWN:
            return

        # Per-user cooldown — roasts always get a reply; otherwise do the "seen" reaction
        if not mentioned and not is_roast and now - _user_last_reply.get(uid, 0) < USER_COOLDOWN:
            await asyncio.sleep(random.uniform(0.5, 2.5))  # humans don't react instantly
            try:
                await message.add_reaction(_pick_reaction(content, is_flirt))
            except (discord.HTTPException, OSError):
                pass
            return

        # ~12% chance to just react instead of replying (never on roasts — she always fires back)
        if not mentioned and not is_roast and random.random() < 0.12:
            try:
                await message.add_reaction(_pick_reaction(content, is_flirt))
            except (discord.HTTPException, OSError):
                pass
            _channel_last_reply[cid] = now
            return

        # ~6% chance of ghost typing — she starts typing then goes quiet
        # very human: read it, thought about it, decided not to engage
        if not mentioned and not is_roast and random.random() < 0.06:
            try:
                async with message.channel.typing():
                    await asyncio.sleep(random.uniform(1.5, 4.0))
            except (discord.HTTPException, OSError):
                pass
            _channel_last_reply[cid] = now
            return

        # ~10% chance to also react on top of reply (skip for roasts — no softening)
        if not mentioned and not is_roast and random.random() < 0.10:
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

        # Sanitise display name: strip control chars and context-format chars ([ ] " \)
        # that call_gemini injects as "[name]: text" — prevents prompt injection via display names.
        # Same character set as ref_author sanitisation a few lines below.
        author_name = re.sub(r'[\r\n\t\[\]"\\]', ' ', message.author.display_name).strip()[:50] or "user"

        # Load any profile data we already have for this user — passed to NLP for context
        user_profile_context = await asyncio.to_thread(profile_store.format_for_context, uid)

        # Resolve <@USER_ID> tokens to readable names before sending to NLP
        resolved_content = _resolve_mentions(message.content or "", message)

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
                reply = await asyncio.to_thread(
                    process_with_nlp,
                    text_to_process, history, author_name, is_roast, is_flirt,
                    user_profile_context,
                )
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
                    "name": _sanitize_name_for_api(author_name),
                    "author": author_name,
                })
                _history[cid].append({"role": "assistant", "content": reply})
                # Use the actual current time so the cooldown reflects when the reply
                # was really sent, not the stale handler-start timestamp in `now`.
                _sent_at = asyncio.get_running_loop().time()
                _user_last_reply[uid] = _sent_at
                _channel_last_reply[cid] = _sent_at
                global _announcement_channel_id
                _announcement_channel_id = cid  # persist for sleep/wake announcements
                # Background: extract personal details from this message and build/update user profile.
                # Store the task reference in _bg_tasks so the event loop can't GC it mid-run.
                _task = asyncio.create_task(_update_profile_bg(uid, author_name, resolved_content))
                _bg_tasks.add(_task)
                _task.add_done_callback(_bg_tasks.discard)
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
        except (discord.HTTPException, OSError):
            pass
    else:
        if not _is_sleeping():
            try:
                await joke_service.maybe_send_joke(message.channel)
            except (discord.HTTPException, OSError):
                pass

def main():
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN is missing. Please set it in your .env file.")
        sys.exit(1)
    start_keepalive()
    bot.run(str(DISCORD_TOKEN))

if __name__ == "__main__":
    main()
