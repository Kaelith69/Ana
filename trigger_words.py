from __future__ import annotations

# Core trigger words that can wake Ana.
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
    "lmao", "omg", "wow", "bruh",
)

# Words that trigger roast/comeback mode.
ROAST_WORDS = frozenset({
    "stupid", "idiot", "dumb", "trash", "useless", "ugly", "shut up", "shutup",
    "stfu", "kys", "loser", "bot", "fake", "lame", "cringe", "mid", "dog",
    "rat", "clown", "nerd", "freak", "weirdo", "pathetic", "boring", "irrelevant",
    "nobody", "nobody asked", "didnt ask", "didn't ask", "cope", "ratio",
    "get lost", "go away", "nobody cares", "shut it", "begone",
    "hell", "damn", "ass", "crap", "wtf", "bitch", "bastard",
    "skill issue", "cooked", "npc", "flop", "delulu", "delusional", "pick me",
    "simp", "down bad", "touch grass", "no life", "embarrassing", "uninstall",
    "worthless", "annoying", "toxic", "ratioed", "stay mad", "cry harder",
    "go cry", "womp", "flop era", "clapped", "ur done", "ur cooked",
    "get good", "L", "take the L", "you lost", "massive L",
    "not funny", "no one cares", "who asked", "nt", "get rekt",
    "trash tier", "bottom tier", "low tier", "expired",
    "delete yourself", "log off", "go outside", "touch some grass",
})

# Words that trigger flirty pick-up line mode.
FLIRT_WORDS = frozenset({
    "cute", "pretty", "beautiful", "gorgeous", "hot", "sexy", "attractive",
    "crush", "date", "marry me", "wife", "girlfriend", "relationship",
    "kiss", "hug", "love you", "i love", "miss you", "think about you",
    "flirt", "pickup", "pick up", "rizz", "smooth", "wanna go out",
    "you're mine", "youre mine", "babe", "baby", "darling", "sweetheart",
    "wanna date", "go out with me", "be mine", "dream girl", "perfect",
    "soft", "thicc", "baddie", "finesse",
})
