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
HF_API_KEY = os.getenv("HF_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN") or HF_API_KEY
HF_CHAT_MODEL = os.getenv("HF_CHAT_MODEL", "meta-llama/Llama-3.3-70B-Instruct")
HF_CHAT_BASE_URL = os.getenv("HF_CHAT_BASE_URL", "https://router.huggingface.co/v1")
HF_SYSTEM_PROMPT = os.getenv(
    "HF_SYSTEM_PROMPT",
    "You are a friendly Discord bot who provides concise, upbeat responses when users say hello.",
)
HF_MAX_TOKENS = _int_env("HF_MAX_TOKENS", 80)
HF_TEMPERATURE = _float_env("HF_TEMPERATURE", 0.8)

GEN1_API_KEY = os.getenv("GEN1_API_KEY")
GEN2_API_KEY = os.getenv("GEN2_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


@dataclass(frozen=True)
class JokeSettings:
    chance: float
    cooldown: int
    # jokes_file removed; jokes are now fetched live
    fetch_batch: int
    fetch_interval: int
    fetch_timeout: int
    api_url: str


JOKE_SETTINGS = JokeSettings(
    chance=_float_env("JOKE_CHANCE", 0.15),
    cooldown=_int_env("JOKE_COOLDOWN", 60),
    # jokes_file removed; jokes are now fetched live
    fetch_batch=_int_env("JOKE_FETCH_BATCH", 25),
    fetch_interval=_int_env("JOKE_FETCH_INTERVAL", 3600),
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
    "lol", "lmao", "omg", "wtf", "wow", "bruh", "bro", "dude",
    "good", "bad", "cool", "funny", "weird", "nice", "evil", "awesome", "cute",
    "think", "dream", "believe", "reality", "universe", "life", "death",
    "what", "why", "how", "when", "where", "who",
    "idk", "tell", "explain", "say", "help",
    "anime", "movie", "game", "player", "level", "boss", "fight",
    "space", "alien", "future", "time", "matrix",
    "fr", "ngl", "ikr", "smh", "btw", "yup", "nah", "sheesh", "damn", "vibe", "chill"
)


FALLBACK_HF_RESPONSES = (
    "Damn,ok you left me speechless with your shitty as text but I heard you loud and clear",
    "urgh lemme sleep you dumbass",
    "Whats it asshole",
)
HF_FAILURE_LIMIT = _int_env("HF_FAILURE_LIMIT", 3)

if not DISCORD_TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN in .env")

if not GEN1_API_KEY:
    print("⚠️ Warning: Missing GEN1_API_KEY. Mood detection may fail.")

if not GEN2_API_KEY:
    print("⚠️ Warning: Missing GEN2_API_KEY. NLP responses may fail.")

if not GROQ_API_KEY:
    print("⚠️ Warning: Missing GROQ_API_KEY. Groq-based responses may fail.")

if not HF_TOKEN:
    print("⚠️ Warning: Missing HF_TOKEN/HF_API_KEY. Bot will use fallback text generation.")
