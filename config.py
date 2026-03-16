from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _int_env(var_name: str, default: int) -> int:
    raw = os.getenv(var_name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"⚠️ Warning: Invalid {var_name} value '{raw}'. Using default {default}.")
        return default


def _float_env(var_name: str, default: float) -> float:
    raw = os.getenv(var_name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        print(f"⚠️ Warning: Invalid {var_name} value '{raw}'. Using default {default}.")
        return default


DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEN1_API_KEY = os.getenv("GEN1_API_KEY")
GEN2_API_KEY = os.getenv("GEN2_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BACKUP_API_KEY = os.getenv("GROQ_BACKUP_API_KEY")

# Character profile storage:
# - SYSTEM_PROMPT lets you override the profile inline from environment.
# - CHARACTER_PROFILE_PATH points to a file loaded lazily by nlp.py only when needed.
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT")
CHARACTER_PROFILE_PATH = os.getenv(
    "CHARACTER_PROFILE_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "ana_character_profile.txt"),
)


@dataclass(frozen=True)
class JokeSettings:
    chance: float
    cooldown: int
    fetch_timeout: int
    api_url: str


JOKE_SETTINGS = JokeSettings(
    chance=_float_env("JOKE_CHANCE", 0.15),
    cooldown=_int_env("JOKE_COOLDOWN", 60),
    fetch_timeout=_int_env("JOKE_FETCH_TIMEOUT", 8),
    api_url=os.getenv("JOKE_API_URL", "https://icanhazdadjoke.com/"),
)

TRIGGER_WORDS = (
    "ana",
    "hello", "hi", "hey", "yo", "sup",
    "morning", "goodmorning", "afternoon", "evening", "goodnight", "night",
    "gm", "gn", "goodafternoon", "goodevening",
    "namaste", "hola", "bonjour",
    "welcome", "bye", "goodbye", "takecare", "see ya", "seeya", "cya", "later",
    "happybirthday", "birthday", "hbd", "happybday",
    "happyanniversary", "congrats", "congratulations", "bestwishes",
    "happynewyear", "newyear", "merrychristmas", "christmas", "eidh", "eid",
    "diwali", "pongal", "onam", "holi", "ramadan", "valentines", "valentine",
    "happymarriedlife", "wedding", "engagement", "babyshower", "getwellsoon",
    "sad", "happy", "tired", "angry", "bored", "excited",
    "lmao", "omg","wow", "bruh"
)

# Words that trigger roast/comeback mode
ROAST_WORDS = frozenset({
    "stupid", "idiot", "dumb", "trash", "useless", "ugly", "shut up", "shutup",
    "stfu", "kys", "loser", "bot", "fake", "lame", "cringe", "mid", "dog",
    "rat", "clown", "nerd", "freak", "weirdo", "pathetic", "boring", "irrelevant",
    "nobody", "nobody asked", "didnt ask", "didn't ask", "cope", "ratio",
    "get lost", "go away", "nobody cares", "shut it", "begone",
    "hell", "damn", "ass", "crap", "wtf", "bitch", "bastard",
    # modern gen-z dismissals
    "skill issue", "cooked", "npc", "flop", "delulu", "delusional", "pick me",
    "simp", "down bad", "touch grass", "no life", "embarrassing", "uninstall",
    "worthless", "annoying", "toxic", "ratioed", "stay mad", "cry harder",
    "go cry", "womp", "flop era", "clapped", "ur done", "ur cooked",
    "get good", "L", "take the L", "you lost", "massive L",
    "not funny", "no one cares", "who asked", "nt", "get rekt",
    "trash tier", "bottom tier", "low tier", "expired",
    "delete yourself", "log off", "go outside", "touch some grass",
})

# Words that trigger flirty pick-up line mode
FLIRT_WORDS = frozenset({
    "cute", "pretty", "beautiful", "gorgeous", "hot", "sexy", "attractive",
    "crush", "date", "marry me", "wife", "girlfriend", "relationship",
    "kiss", "hug", "love you", "i love", "miss you", "think about you",
    "flirt", "pickup", "pick up", "rizz", "smooth", "wanna go out",
    "you're mine", "youre mine", "babe", "baby", "darling", "sweetheart",
    "wanna date", "go out with me", "be mine", "dream girl", "perfect",
    "soft", "thicc", "baddie", "finesse",
})

# ---------------------------------------------------------------------------
# Ana v4 — Groq model waterfall
# ---------------------------------------------------------------------------
# Tried in priority order. A rate-limited or failed model is skipped and the
# next one is attempted. Llama 4 Scout is the current always-on baseline —
# listed third so Kimi K2 and Llama 3.3 70B are preferred when available.
# To override model slugs without touching code, set GROQ_MODEL_PRIMARY /
# GROQ_MODEL_BACKUP1 / GROQ_MODEL_BACKUP2 / GROQ_MODEL_BACKUP3 in .env.
GROQ_MODEL_WATERFALL = [
    os.getenv("GROQ_MODEL_PRIMARY", "moonshotai/kimi-k2-instruct"),
    os.getenv("GROQ_MODEL_BACKUP1", "llama-3.1-8b-instant"),
    os.getenv("GROQ_MODEL_BACKUP2", "llama-3.1-8b-instant"),
    os.getenv("GROQ_MODEL_BACKUP3", "qwen/qwen3-32b"),
]

# Per-model generation settings and prompt patches.
# 'thinking': False  — disables Qwen 3's chain-of-thought bleed (passed as extra_body).
# 'patch'           — short text appended to the system prompt in normal mode only
#                     (roast/flirt prompts are self-contained and don't receive patches).
MODEL_SETTINGS = {
    # #1 — Kimi K2 (best instruction following + multilingual)
    "moonshotai/kimi-k2-instruct": {
        "max_tokens": 80,
        "temperature": 0.88,
        "top_p": 0.92,
        "thinking": None,
        "patch": (
            "Respond as Ana texting — very short fragments, lowercase, never capital I. "
            "Most replies: under 10 words. Absolute max: 20 words for a casual exchange. "
            "NEVER use elaborate metaphors or extended similes — no 'swan-dive', no 'pirouette', "
            "no dramatic imagery. Blunt and short always beats poetic and long. "
            "Do not over-explain. Pick ONE thing and respond to THAT only. "
            "Do not open with 'So,', 'Well,', or any transition word. "
            "Do not close with 'hope this helps', 'let me know', or 'does that make sense?'. "
            "Do not echo the question back. Do not end with an engagement question. "
            "She is a person, not an assistant. "
            "Group chat: respond to the specific person — not the room. reference others by name when natural."
        ),
    },
    # #2 — Llama 3.1 8B Instant (secondary + fallback)
    "llama-3.1-8b-instant": {
        "max_tokens": 70,
        "temperature": 0.86,
        "top_p": 0.90,
        "thinking": None,
        "patch": (
            "Respond as Ana texting in short lowercase fragments. "
            "Most replies: under 10 words. Absolute max: 20 words. "
            "No elaborate metaphors or formal transitions. "
            "Pick one thread and reply directly. "
            "Do not sound like support or an assistant. "
            "Group chat: respond to the person in front of you, not the whole room."
        ),
    },
    # #2 — Llama 3.3 70B (proven, stable persona)
    "meta-llama/llama-3.3-70b-versatile": {
        "max_tokens": 70,
        "temperature": 0.85,
        "top_p": 0.90,
        "thinking": None,
        "patch": (
            "You are Ana texting in a Discord server — never capital I, lowercase always. "
            "Most replies: under 10 words. Absolute max: 20 words. Short casual fragments only. "
            "NO elaborate metaphors — 'swan-dive off a balcony', 'pirouette off a cliff' are AI tells. "
            "Say it bluntly and briefly. Less is always more. "
            "Do not open with a transition word, 'So,', or 'Well,'. "
            "Do not explain every part of the question — pick the most interesting angle and go. "
            "Don't close with 'hope this helps', 'let me know', or 'does that make sense?'. "
            "Don't echo the question back. Don't end with 'what do you think?'. She's a person, not support. "
            "Group chat: respond to the person in front of you — not the room. never address everyone at once."
        ),
    },
    # #3 — Llama 4 Scout (fast, 10M context, MoE)
    "meta-llama/llama-4-scout-17b-16e-instruct": {
        "max_tokens": 70,
        "temperature": 0.87,
        "top_p": 0.91,
        "thinking": None,
        "patch": (
            "Keep responses under 2 short fragments for casual turns. Most replies: 5-10 words. "
            "No elaborate metaphors or similes. Blunt and direct. Lowercase always, never capital I. "
            "Do not start with 'I', 'Sure', 'Of course', 'So,', 'Well,', or any transition word. "
            "Do not end with 'does that make sense?' or any engagement question. "
            "Pick ONE thing to respond to — not every point. You are Ana, not an assistant. "
            "Group chat: you know who said what. respond to the person, never address the whole server."
        ),
    },
    # #4 — Qwen 3 32B (reasoning model — thinking must be disabled)
    "qwen/qwen3-32b": {
        "max_tokens": 65,
        "temperature": 0.82,
        "top_p": 0.90,
        "thinking": False,
        "patch": (
            "No reasoning steps. Respond as Ana. Very short. Lowercase. Fragmented. "
            "Most replies: under 10 words. Absolute max: 15 words. "
            "No elaborate metaphors or extended similes — blunt and direct only. "
            "No capital I. Pick ONE thing to respond to — not every point. "
            "No 'additionally', 'furthermore', 'to summarize', 'So,', 'Well,', or structured answers. "
            "No closers like 'hope this helps' or 'does that make sense?'. "
            "Do not echo the question back. Do not end with 'what do you think?'. "
            "She's a person, not a support bot. "
            "Group chat: respond to the person, not the room. trace who said what in prior messages."
        ),
    },
}


if not DISCORD_TOKEN:
    print("⚠️ Warning: Missing DISCORD_TOKEN in .env. Bot will not start.")

if not GEN1_API_KEY:
    print("⚠️ Warning: Missing GEN1_API_KEY. Gemini Gen1 fallback will not work.")

if not GEN2_API_KEY:
    print("⚠️ Warning: Missing GEN2_API_KEY. Gemini Gen2 fallback will not work.")

if not GROQ_BACKUP_API_KEY:
    print("ℹ️ Info: GROQ_BACKUP_API_KEY not set. Using GROQ_API_KEY for all Groq waterfall models.")

if not GROQ_API_KEY:
    print("⚠️ Warning: Missing GROQ_API_KEY. Groq-based responses may fail.")
