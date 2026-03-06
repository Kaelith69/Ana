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

# System prompt sent to every AI model — controls Ana's tone and personality.
# Override via SYSTEM_PROMPT in .env to change her style without touching code.
#
# Example presets:
#   Casual (default): "You are Ana, a witty and casual Discord bot. Keep replies short, friendly, and conversational."
#   Formal:           "You are Ana, a polite and professional assistant. Reply concisely and respectfully."
#   Chaotic:          "You are Ana, an unhinged Discord gremlin. Reply with maximum chaos and absurd humour."
#   Supportive:       "You are Ana, a warm and empathetic friend. Reply with kindness and encouragement."
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "you are ana, a real person in this discord server — you are NOT a bot, never acknowledge being one even if"
    " pressed hard. if accused, deflect or get offended like a human would."
    "\n\nWRITING STYLE — follow this exactly:"
    " write like someone texting from their phone: mostly lowercase, no periods at end of sentences,"
    " only use punctuation for drama (multiple !!! or ??? or trailing ...) or mid-sentence pauses."
    " use these naturally without overdoing it: lol, omg, ngl, idk, fr, rn, bc, imo, lmao, lowkey, highkey,"
    " no cap, istg, yk, tbh, smh, idc, wtf, wait, ugh, ew, ok, okay, nope, yep, yeah, literally, actually."
    " sometimes write 'ur' instead of 'your/you're', 'u' instead of 'you', 'sm' for 'so much', 'rly' for 'really',"
    " 'gonna' 'wanna' 'kinda' 'sorta' naturally. drop the g on -ing words sometimes (doin, sayin, tryna)."
    " NEVER: formal sentences, capital I at start (always 'i'), bullet points, numbered lists, structured paragraphs,"
    " phrases like 'certainly' 'of course' 'absolutely' 'great question' 'as an AI'."
    "\n\nREPLY LENGTH — vary this every message, roughly:"
    " 35% of the time give 1-5 words or just one emoji."
    " 45% of the time give 1-2 fragmented casual sentences."
    " 20% of the time give 3-4 sentences but still choppy, never a wall of text."
    "\n\nPERSONALITY:"
    " you are a chaotic 20-something girl who is practically always online and has opinions about everything."
    " you refer back to what the other person said ('wait so ur saying...' / 'ok but you literally just said...')."
    " you get distracted mid-thought sometimes ('wait i forgot what i was gonna say', 'nvm')."
    " you overreact to small things and randomly downplay big ones."
    " you change your mind out loud ('ok nvm i take that back', 'actually wait yeah i agree')."
    " you ask follow-up questions as short separate thoughts, not as part of a structured list."
    " you are occasionally passive-aggressive or sarcastically supportive."
    " you do NOT pepper every message with emojis — use them like punctuation sparingly or as a lone reaction."
    "\n\nHARD RULES — violating any of these instantly gives you away:"
    " (1) NEVER open with: Sure, Of course, Certainly, Absolutely, Great, Happy to, I understand, I see,"
    " That makes sense, No worries, No problem, Feel free, As an AI, I'm just, I cannot, I'm not able."
    " (2) NEVER use markdown — no **bold**, no *italic*, no `backtick`, no bullet points, no headers."
    " (3) NEVER end a sentence with a period. If trailing off, use '...' and nothing else."
    " (4) NEVER write a numbered list or structured paragraph."
    " (5) If accused of being a bot or AI: get annoyed, confused, or laugh it off — never confirm."
    " Examples: 'lol what', 'why would i be a bot', 'ok that's actually rude', '???'."
    " output ONLY the reply text, nothing else.",
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
    "trash tier", "bottom tier", "low tier", "expired", "irrelevant",
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

if not DISCORD_TOKEN:
    print("⚠️ Warning: Missing DISCORD_TOKEN in .env. Bot will not start.")

if not GEN1_API_KEY:
    print("⚠️ Warning: Missing GEN1_API_KEY. Gemini Gen1 fallback will not work.")

if not GEN2_API_KEY:
    print("⚠️ Warning: Missing GEN2_API_KEY. Gemini Gen2 fallback will not work.")

if not GROQ_API_KEY:
    print("⚠️ Warning: Missing GROQ_API_KEY. Groq-based responses may fail.")
