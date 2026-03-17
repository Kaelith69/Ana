from __future__ import annotations
import asyncio
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
MENTION_TOKEN_PATTERN = re.compile(r'<@!?(\d+)>')
NON_WORD_PATTERN = re.compile(r'[^\w\s]')

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

# Emoji reactions Ana might use instead of a full reply
_REACTIONS = ["😭", "💀", "😂", "🙄", "❤️", "😤", "🫠", "👀", "😮", "🤙",
              "🤣", "💅", "😩", "🥺", "✨", "🔥", "😳", "🤦", "😵", "🫡",
              "😬", "🤌", "🤭", "💯", "😑", "🫶", "🧍", "🤷"]

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
    "the disrespect will not be tolerated",
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
    "nm nm nm",
    "ok but also",
    "wait no",
    "..wait",
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
]

_JOKE_SETUPS = [
    "okay don't judge me",
    "wait i have one",
    "ok bear with me",
    "this is terrible and i love it",
    "i hate that this made me laugh",
    "you asked for this",
    "ok this one's bad. in a good way.",
    "u didn't hear this from me",
]

RESPONSE_WATCHDOG_SECONDS = 28.0
NLP_ATTEMPT_TIMEOUT_SECONDS = 18.0

_GUARANTEE_FALLBACKS = [
    "i'm here, one sec my brain lagged",
    "i saw that. try me again in one line?",
    "message received. my model glitched but i'm back",
    "i got your message but generation failed. send that again?",
    "network hiccup on my side. i'm still here",
    "i dropped the thread for a sec, continue",
]


def _fallback_response() -> str:
    return random.choice(_GUARANTEE_FALLBACKS)


def _normalize_outbound_text(text: str | None) -> str:
    if not text:
        return _fallback_response()
    cleaned = re.sub(r"\s+", " ", str(text)).strip()
    if not cleaned:
        return _fallback_response()
    return cleaned[:1800]


def _log_message_lifecycle(message_id: int, stage: str, detail: str = "") -> None:
    suffix = f" {detail}" if detail else ""
    print(f"[lifecycle] message_id={message_id} stage={stage}{suffix}")


class ResponseDispatcher:
    """Single-exit response guard: each message can be finalized once."""

    def __init__(self, message: discord.Message) -> None:
        self._message = message
        self._lock = asyncio.Lock()
        self._finalized = False

    async def finalize(self, text: str | None, *, path: str) -> bool:
        payload = _normalize_outbound_text(text)
        async with self._lock:
            if self._finalized:
                _log_message_lifecycle(self._message.id, "duplicate_finalize_blocked", f"path={path}")
                return False

            _log_message_lifecycle(self._message.id, "dispatch_attempt", f"path={path}")
            try:
                await self._message.reply(payload, mention_author=False)
            except (discord.HTTPException, OSError) as reply_err:
                _log_message_lifecycle(
                    self._message.id,
                    "reply_send_failed",
                    f"path={path} error={reply_err}",
                )
                try:
                    await self._message.channel.send(payload)
                except (discord.HTTPException, OSError) as send_err:
                    _log_message_lifecycle(
                        self._message.id,
                        "channel_send_failed",
                        f"path={path} error={send_err}",
                    )
                    return False

            self._finalized = True
            _log_message_lifecycle(self._message.id, "dispatch_complete", f"path={path}")
            return True

    @property
    def is_finalized(self) -> bool:
        return self._finalized


async def _watchdog_finalize(message: discord.Message, dispatcher: ResponseDispatcher) -> None:
    """Ensure a fallback response is emitted if processing stalls."""
    await asyncio.sleep(RESPONSE_WATCHDOG_SECONDS)
    await dispatcher.finalize(_fallback_response(), path="watchdog_timeout")


async def _generate_reply_with_guarantee(
    text_to_process: str,
    history: list[dict],
    author_name: str,
    is_roast: bool,
    is_flirt: bool,
    user_profile_context: str,
    message_id: int,
) -> str:
    """Generate a response with retries and timeout protection."""
    generation_history = history

    for attempt in (1, 2):
        try:
            _log_message_lifecycle(message_id, "nlp_attempt", f"attempt={attempt}")
            reply = await asyncio.wait_for(
                asyncio.to_thread(
                    process_with_nlp,
                    text_to_process,
                    generation_history,
                    author_name,
                    is_roast,
                    is_flirt,
                    user_profile_context,
                ),
                timeout=NLP_ATTEMPT_TIMEOUT_SECONDS,
            )
            if reply and reply.strip():
                return reply.strip()
            _log_message_lifecycle(message_id, "nlp_empty", f"attempt={attempt}")
        except asyncio.TimeoutError:
            _log_message_lifecycle(message_id, "nlp_timeout", f"attempt={attempt}")
        except Exception as nlp_err:
            _log_message_lifecycle(message_id, "nlp_error", f"attempt={attempt} error={nlp_err}")

        # Retry with reduced history to lower token/context and latency pressure.
        generation_history = history[-6:]

    return _fallback_response()


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
    return MENTION_TOKEN_PATTERN.sub(_replace, content)


def _maybe_typo(text: str) -> tuple[str, str | None]:
    """~4% chance to swap two adjacent chars in a word and return a star-correction.

    Returns (possibly_typo_text, "*correct_word" or None).
    """
    if random.random() >= 0.04:
        return text, None
    words = text.split()
    candidates = [(i, w) for i, w in enumerate(words) if len(w) >= 4 and w.isalpha()]
    if not candidates:
        return text, None
    idx, word = random.choice(candidates)
    pos = random.randint(1, len(word) - 2)
    typo_word = word[:pos] + word[pos + 1] + word[pos] + word[pos + 2:]
    if typo_word == word:
        return text, None
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
    await ctx.send(random.choice(_JOKE_SETUPS))
    await asyncio.sleep(random.uniform(1.0, 2.0))
    async with ctx.typing():
        await asyncio.sleep(random.uniform(1.2, 2.2))
    await ctx.send(punchline)

@tasks.loop(hours=1)
async def _cleanup_cooldowns() -> None:
    """Periodically prune stale entries from the cooldown dicts and history to bound memory use."""
    now = asyncio.get_running_loop().time()
    stale_users = [uid for uid, ts in _user_last_reply.items() if now - ts > USER_COOLDOWN * 20]
    stale_channels = [cid for cid, ts in _channel_last_reply.items() if now - ts > CHANNEL_COOLDOWN * 20]
    for uid in stale_users:
        del _user_last_reply[uid]
    for cid in stale_channels:
        del _channel_last_reply[cid]
        _history.pop(cid, None)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    if not _cleanup_cooldowns.is_running():
        _cleanup_cooldowns.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = (message.content or "")
    lowered = content.lower()

    # Keep explicit commands available regardless of trigger/reply gating.
    if content.startswith(str(bot.command_prefix)):
        _log_message_lifecycle(message.id, "received_command", f"author={message.author.id} channel={message.channel.id}")
        dispatcher = ResponseDispatcher(message)
        watchdog_task = asyncio.create_task(_watchdog_finalize(message, dispatcher))
        try:
            cmd = lowered.strip()
            if cmd.startswith("!joke"):
                punchline = await asyncio.wait_for(asyncio.to_thread(joke_service.random_joke), timeout=8.0)
                reply = punchline or "idk any rn try again later lol"
                await dispatcher.finalize(reply, path="command_joke")
                return

            if cmd.startswith("!shutdown"):
                is_owner = await bot.is_owner(message.author)
                if not is_owner:
                    await dispatcher.finalize("nope. owner only", path="command_shutdown_denied")
                    return
                sent = await dispatcher.finalize("okay shutting down", path="command_shutdown")
                if not sent:
                    return
                await bot.close()
                sys.exit(0)

            await dispatcher.finalize("unknown command. try !joke", path="command_unknown")
            return
        except Exception as cmd_err:
            print(f"[on_message] command error: {cmd_err}", file=sys.stderr)
            await dispatcher.finalize(_fallback_response(), path="handled_command_error")
        finally:
            if dispatcher.is_finalized:
                watchdog_task.cancel()
                try:
                    await watchdog_task
                except asyncio.CancelledError:
                    pass
            else:
                await watchdog_task

    is_trigger_word = (
        bool(TRIGGER_PATTERN.search(lowered))
        or bool(ROAST_PATTERN.search(lowered))
        or bool(FLIRT_PATTERN.search(lowered))
    )

    # Respond when user directly replies to Ana's message.
    is_reply_to_ana = False
    if message.reference:
        ref_msg = None
        if isinstance(message.reference.resolved, discord.Message):
            ref_msg = message.reference.resolved
        elif message.reference.message_id:
            try:
                ref_msg = await message.channel.fetch_message(message.reference.message_id)
            except (discord.NotFound, discord.HTTPException, OSError):
                ref_msg = None
        if ref_msg and bot.user and ref_msg.author.id == bot.user.id:
            is_reply_to_ana = True

    if not is_trigger_word and not is_reply_to_ana:
        return

    _log_message_lifecycle(message.id, "received", f"author={message.author.id} channel={message.channel.id}")
    dispatcher = ResponseDispatcher(message)
    watchdog_task = asyncio.create_task(_watchdog_finalize(message, dispatcher))
    is_roast = bool(ROAST_PATTERN.search(lowered))
    is_flirt = (not is_roast) and bool(FLIRT_PATTERN.search(lowered))

    now = asyncio.get_running_loop().time()
    uid = message.author.id
    cid = message.channel.id

    try:
        # Pre-reserve cooldown slots before long NLP awaits to avoid fan-out under bursts.
        _channel_last_reply[cid] = now
        _user_last_reply[uid] = now

        author_name = message.author.display_name
        user_profile_context = await asyncio.to_thread(profile_store.format_for_context, uid)
        resolved_content = _resolve_mentions(content, message)

        if not resolved_content.strip() and not message.attachments:
            await dispatcher.finalize("i got your message but it was empty", path="input_validation_empty")
            return

        if not resolved_content.strip() and message.attachments:
            resolved_content = "[user sent attachment without text]"

        # If this message is a Discord reply, inject referenced-message context.
        text_to_process = resolved_content
        if message.reference:
            ref_msg = None
            if isinstance(message.reference.resolved, discord.Message):
                ref_msg = message.reference.resolved
            elif message.reference.message_id:
                try:
                    ref_msg = await message.channel.fetch_message(message.reference.message_id)
                except (discord.NotFound, discord.HTTPException, OSError):
                    pass
            if ref_msg:
                ref_author = re.sub(r'[\r\n\t\[\]"\\]', ' ', ref_msg.author.display_name).strip()[:50]
                ref_raw = _resolve_mentions((ref_msg.content or "")[:200], ref_msg)
                ref_text = re.sub(r'[\r\n\t\[\]"\\]', ' ', ref_raw).strip()[:200]
                if ref_text:
                    text_to_process = f"[replying to @{ref_author}: \"{ref_text}\"]\n{resolved_content}"

        history = list(_history.get(cid, []))
        async with message.channel.typing():
            reply = await _generate_reply_with_guarantee(
                text_to_process,
                history,
                author_name,
                is_roast,
                is_flirt,
                user_profile_context,
                message.id,
            )

        _history[cid].append({
            "role": "user",
            "content": text_to_process,
            "name": _sanitize_name_for_api(author_name),
            "author": author_name,
        })
        _history[cid].append({"role": "assistant", "content": reply})

        sent_at = asyncio.get_running_loop().time()
        _user_last_reply[uid] = sent_at
        _channel_last_reply[cid] = sent_at

        # Only extract profiles when message has enough signal.
        if len(resolved_content.strip()) >= 15:
            task = asyncio.create_task(_update_profile_bg(uid, author_name, resolved_content))
            _bg_tasks.add(task)
            task.add_done_callback(_bg_tasks.discard)

        sent = await dispatcher.finalize(reply, path="success")
        if not sent:
            await dispatcher.finalize(_fallback_response(), path="success_recovery")

    except (discord.HTTPException, OSError) as msg_err:
        print(f"[on_message] discord/os error uid={uid} cid={cid}: {msg_err}", file=sys.stderr)
        await dispatcher.finalize(_fallback_response(), path="handled_discord_error")
    except Exception as msg_err:
        print(f"[on_message] unexpected error uid={uid} cid={cid}: {msg_err}", file=sys.stderr)
        await dispatcher.finalize(_fallback_response(), path="handled_unexpected_error")
    finally:
        if dispatcher.is_finalized:
            watchdog_task.cancel()
            try:
                await watchdog_task
            except asyncio.CancelledError:
                pass
        else:
            # Keep watchdog alive when no response was finalized yet.
            await watchdog_task

def main():
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN is missing. Please set it in your .env file.")
        sys.exit(1)
    start_keepalive()
    bot.run(str(DISCORD_TOKEN))

if __name__ == "__main__":
    main()
