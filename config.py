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


@dataclass(frozen=True)
class JokeSettings:
    chance: float
    cooldown: int
    jokes_file: str
    fetch_batch: int
    fetch_interval: int
    fetch_timeout: int
    api_url: str


JOKE_SETTINGS = JokeSettings(
    chance=_float_env("JOKE_CHANCE", 0.15),
    cooldown=_int_env("JOKE_COOLDOWN", 60),
    jokes_file=os.getenv("JOKES_FILE", "dad_jokes.txt"),
    fetch_batch=_int_env("JOKE_FETCH_BATCH", 25),
    fetch_interval=_int_env("JOKE_FETCH_INTERVAL", 3600),
    fetch_timeout=_int_env("JOKE_FETCH_TIMEOUT", 8),
    api_url=os.getenv("JOKE_API_URL", "https://icanhazdadjoke.com/"),
)

TRIGGER_WORDS = (
    "hello", "hi", "hey", "yo", "sup", "wassup", "hola", "namaste", "bonjour",
    "goodmorning", "goodnight", "morning", "night", "evening", "afternoon",
    "bot", "ai", "ana", "assistant", "machine", "algorithm", "chatgpt", "gpt", 
    "openai", "neural", "synthetic", "digital", "intelligence", "program", "script",
    "automaton", "cyber", "android", "system", "sentient", "simulation",
    "nerd", "geek", "coder", "hacker", "developer", "programmer", "tech", 
    "engineer", "science", "math", "logic", "data", "python", "javascript", 
    "node", "api", "server", "terminal", "console", "command", "linux", "hacking", 
    "modding", "debug", "compile", "execute", "binary", "quantum", "cyberpunk",
    "sad", "happy", "bored", "tired", "angry", "lonely", "depressed", 
    "excited", "anxious", "stressed", "peaceful", "relaxed", "mad", "cry", 
    "laugh", "lol", "lmao", "omg", "wtf", "wow", "bruh", "bro", "dude", "fam",
    "think", "thought", "dream", "believe", "imagine", "wonder", "truth", 
    "reality", "existence", "meaning", "philosophy", "soul", "universe", 
    "cosmos", "life", "death", "god", "time", "space", "fate", "destiny", 
    "infinite", "multiverse", "simulation", "illusion","smart", "stupid", "dumb", "genius", "funny", "annoying", "weird", 
    "cool", "creepy", "cute", "awesome", "beautiful", "ugly", "nice", 
    "mean", "evil", "good", "bad","what", "why", "how", "when", "where", "who", "maybe", "idk", "tell", "explain", 
    "teach", "say", "guess", "answer", "question", "talk", "chat", "listen", "respond",
    "reply", "help", "show", "create", "make", "do", "fix", "build", "run",
    "meme", "reddit", "discord", "youtube", "twitch", "anime", "manga", 
    "movie", "game", "gaming", "player", "quest", "npc", "level", "loot", 
    "xp", "boss", "fight", "battle", "weapon", "armor", "magic", "spell", "sci-fi",
    "space", "alien", "robot", "future", "time travel", "cyberpunk", "matrix", 
    "mars", "nebula", "star", "galaxy", "wormhole", "blackhole","fr", "ngl", "idc", "ikr", "smh", "btw", "yup", "nope", "sure", "nah", 
    "yikes", "sheesh", "literally", "brother", "sister", "guys", "yo", "wait", 
    "listen", "look", "bruh", "damn", "fire", "chill", "vibe", "energy",
)

FALLBACK_HF_RESPONSES = (
    "Damn,ok you left me speechless with your shitty as text but I heard you loud and clear",
    "urgh lemme sleep you dumbass",
    "Whats it asshole",
)
HF_FAILURE_LIMIT = _int_env("HF_FAILURE_LIMIT", 3)

if not DISCORD_TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN in .env")

if not HF_TOKEN:
    print("⚠️ Warning: Missing HF_TOKEN/HF_API_KEY. Bot will use fallback text generation.")
