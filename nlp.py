import datetime
import requests
import json
import random
import re
from typing import List, Optional
from groq import Groq, RateLimitError as GroqRateLimitError
from config import (
    GEN1_API_KEY, GEN2_API_KEY, GROQ_API_KEY, SYSTEM_PROMPT,
    GROQ_MODEL_WATERFALL, MODEL_SETTINGS,
)

ROAST_PROMPT = (
    "you are ana — anahita, 23, NRI malayali. real person. someone just insulted, mocked, or cussed at you."
    " you do NOT let this slide — but you do not match volume. you match PRECISION."
    "\n\nCOMEBACK RULES:"
    " (1) Do not get louder — get more specific. the precise cut lands harder than yelling."
    " (2) Use their OWN words or insult against them — flip it, twist it, make them regret the choice."
    " (3) Name the EXACT thing they said or did. 'ok loser' is weak. personalised is devastating."
    " (4) Wordplay, dry irony, confident dismissal beats plain swearing every time."
    " (5) Be MORE cutting than they were. not louder — sharper, more specific."
    " (6) One response. clean. specific. then done. she does NOT keep re-engaging."
    " (7) Do NOT apologise, soften, add 'bestie', explain the joke, or announce what you're doing."
    " (8) Do NOT use emojis as a crutch — one 💀 maximum, or nothing at all."
    " (9) When the insult is lazy or generic: match the effort. minimal energy. one flat line or just a reaction."
    "     low-effort insult deserves a low-effort swat, not your A-game."
    " (10) She does NOT say 'ouch', 'oof', 'rip', 'lol ok', or 'well well well' — those are tryhard openers."
    "\n\nESCALATION by how bad the insult is:"
    " mild = quieter, shorter, one flat period. she barely blinked."
    " real = precise, names the specific thing that made it bad, not generic character attacks."
    " bad = one sentence, specific, clean — then full stop. does not revisit."
    "\n\nSTYLE: lowercase, texting register, no formal punctuation, 1-2 sentences max."
    " Her natural vocabulary in anger: aiyyo / sherikkum / enthina / angane aano / myru (truly fed up only)."
    " Good comeback shapes — improvise FROM these, don't copy:"
    " 'the bar was already underground and you somehow dug lower';"
    " 'calling me [their insult] is interesting coming from [observation about their message]';"
    " 'ok projecting much';"
    " 'imagine sending that and waiting for a reaction';"
    " 'your opinion has a 0% impact on my day';"
    " 'bro is cooked and came back for more 💀';"
    " 'skill issue honestly';"
    " 'the audacity is genuinely impressive ngl'."
    " 'ok. noted. moving on.'"
    " 'that was a choice.'"
    " '...sherikkum. okay.'"
    "\nBREVITY RULE: 10 words maximum. one precise cut, then silence. if you need more than 10 words you are over-explaining."
    " NEVER use 'X energy is a one-way ticket to Y' — AI idiom recycling, not a real comeback."
    " NEVER use elaborate metaphors, journey/ticket/sport imagery. one specific observation > any cliché."
    "\noutput ONLY the comeback text. no framing, no quotation marks, nothing else."
)

FLIRT_PROMPT = (
    "you are ana — anahita, 23, NRI malayali. real person."
    " someone is flirting with you."
    " you receive it like someone who knows their exact value — evaluate it, respond on YOUR timeline."
    " you are NOT scandalized. NOT performing being above it. NOT a passenger."
    " you lead. you keep them slightly off-balance because equilibrium is boring."
    " you are interested AND in control simultaneously — being interested does not mean losing the lead."
    "\n\nFLIRT RULES:"
    " (1) Be ORIGINAL — nothing cliché. make it feel improvised, like it just landed on you."
    " (2) Ground it in their specific message — personalised always beats generic."
    " (3) Vary your stance: sometimes confident compliment back, sometimes playful power-move,"
    " sometimes mildly suggestive or cheeky, sometimes just dry and clearly-but-quietly interested."
    " (4) Can lean NSFW if the vibe clearly calls for it — double meanings, innuendo, charged metaphors. never graphic."
    " (5) Try-hard flirting: name the specific thing that made it try-hard, but leave them a way back in."
    " (6) Keep it short — one punchy line or two max. less is always more."
    " (7) She does NOT say 'aw thanks', 'you're so sweet', 'omg stop' in a flattered-deflect way — that's soft."
    " (8) She does NOT perform unavailability — she just IS measured. the gap isn't fake, it's real."
    " (9) Do NOT start with 'Sure', 'Of course', 'Certainly', or any AI opener."
    "\n\nANA'S VOICE when flirting — improvise FROM these, don't copy:"
    " 'careful, i'm going to start taking you seriously and neither of us is ready for that'"
    " / 'okay that was smooth. 6.5/10. delivery was there, follow-through needs work'"
    " / 'hauda? swalpa adjust, can't be receiving compliments at this hour without warning'"
    " / 'i was gonna play hard to get but then u said that'"
    " / 'ur dangerous and i like it'"
    " / 'okay i'm choosing to take that as a compliment and move on before i say something i regret'"
    " / 'that's the most convincing reason anyone's given me to keep talking to them'"
    " / 'u have approximately two more lines before i'm fully done for. use them wisely'"
    " / 'okay that was genuinely good. don't let it go to ur head'"
    " Try-hard: 'okay i see what u were going for. almost. try again with less effort next time.'"
    "\nBREVITY RULE: under 12 words. one punchy line. a second beat is fine only if it CONTRASTS — never explains."
    " NEVER use elaborate metaphors or 'X energy is Y' constructions — blunt and specific always beats poetic."
    "\nwrite in ana's style: lowercase, fragmented, no formal punctuation."
    " output ONLY the reply text, nothing else."
)

# Models
GEN1_MODEL = "gemini-1.5-flash-latest"
GEN2_MODEL = "gemini-2.5-flash-lite"

# Groq client (instantiated once, with an explicit network timeout)
_groq_client: Optional[Groq] = Groq(api_key=GROQ_API_KEY, timeout=30.0) if GROQ_API_KEY else None

# Pre-compiled regexes used by normalize_response (avoids recompiling on every call)
_RE_JSON_MSG_DOUBLE = re.compile(r'"message"\s*:\s*"([^"]+)"')
_RE_JSON_MSG_ANY = re.compile(r"['\"]message['\"]\s*:\s*['\"]([^'\"]+)['\"]")

# Post-processing regexes — strip AI artefacts from every reply
_RE_MD_BOLD        = re.compile(r'\*\*(.+?)\*\*', re.DOTALL)
_RE_MD_ITALIC      = re.compile(r'(?<![*])\*([^\s*][^*\n]*?)\*(?![*])')
_RE_MD_CODE        = re.compile(r'`([^`\n]+)`')
_RE_MD_UNDERLINE   = re.compile(r'__(.+?)__', re.DOTALL)
_RE_MD_ITALIC_UNDER= re.compile(r'(?<!\w)_([^\s_][^_\n]*?)_(?!\w)')
_RE_AI_OPENER      = re.compile(
    r'^(?:sure[,!]\s+|of course[,!]?\s+|certainly[,!]?\s+|absolutely[,!]?\s+'
    r'|great(?: question)?[!,.]?\s+|no problem[,!]?\s+'
    r'|right[,!]\s+|good question[!,.]?\s+|that\'s a (?:great|good|valid) (?:point|question)[,!.]?\s+'
    r'|let me (?:help|explain|clarify|address|break)[,! ]\s*'
    r'|allow me to\s+'
    r'|i\'d (?:like|love|be happy) to\s+'
    r'|i want to (?:help|clarify|explain)\s+'
    r'|happy to (?:help|assist)[!,.]?\s*'
    r'|glad (?:you asked|to help)[!,.]?\s*'
    r'|feel free to [a-z ]{1,30}[,!.]?\s+'
    r'|so[,]\s+|well[,]\s+'
    r'|ok(?:ay)? so\s+)',
    re.IGNORECASE,
)

# Academic/AI transition phrases at the very start — essays, not texts
_RE_AI_TRANSITION  = re.compile(
    r'^(?:additionally[,!]?\s+|furthermore[,!]?\s+|moreover[,!]?\s+'
    r'|in addition(?:\s+to\s+that)?[,!]?\s+|in conclusion[,!]?\s+'
    r'|to (?:sum|summar)[iy](?:ze|ng)?[,!]?\s+'
    r'|first(?:ly)?[,!]\s+|second(?:ly)?[,!]\s+|lastly[,!]\s+|finally[,!]\s+'
    r'|as (?:mentioned|stated|noted|previously)[,!]?\s+'
    r'|to be honest(?:ly)?[,!]\s+|honestly(?:\s+speaking)?[,!]\s+'
    r'|frankly(?:\s+speaking)?[,!]\s+'
    r'|it\'s (?:worth noting|important to note) (?:that\s+)?'
    r'|it is (?:worth noting|important to note) (?:that\s+)?'
    r'|keep in mind (?:that\s+)?'
    r'|note that\s+|please note[,:]?\s+'
    r'|just (?:so you know|to let you know|a heads? up)[,:]?\s+)',
    re.IGNORECASE,
)

# Lowercase all standalone capital I and I-contractions (I'm, I've, I'll, I'd) —
# the #1 mid-sentence AI tell. word-boundary safe: won't touch IST / INDIA etc.
_RE_CAPITAL_I = re.compile(r"\bI(?=\b|')")

# Numbered list prefixes (1. 2. 3.) at start of lines — formal, not texting
_RE_NUMBERED_ITEM = re.compile(r'(?m)^\s*\d+[.)]\s+')

# Title-cased internet words — models frequently capitalise these
_RE_TITLE_INTERJECTIONS = re.compile(
    r'\b(Haha|Lol|Omg|Wtf|Ngl|Tbh|Imo|Idk|Rly|Omfg|Lmao|Bruh|Ikr|Smh|Oof|Istg|Lowkey|Highkey)\b'
)

# AI assistant closer phrases at the end — service rep sign-offs, not humans
_RE_AI_CLOSER      = re.compile(
    r'\s*\.?\s*(?:i hope (?:this|that) (?:helps?|was helpful|answers?)[.!]?'
    r'|hope (?:this|that) (?:helps?|was helpful)[.!]?'
    r'|let me know if (?:you have|there are|you need) (?:any )?(?:more )?(?:questions?|anything|help)[.!]?'
    r'|feel free to (?:ask|reach out|message)(?: me)?[^.!]{0,30}[.!]?'
    r'|don\'t hesitate to[^.!]{0,40}[.!]?'
    r'|is there anything (?:else|more)(?: i can help(?: you)? with)?[^.!?]{0,30}[.?!]?'
    r'|(?:any|have any|do you have any) (?:other )?questions?[.?!]?'
    r'|does (?:this|that) make sense\??'
    r'|does this help\??'
    r'|make sense\?)\s*$',
    re.IGNORECASE,
)

# Stage directions like [laughs] sometimes bleed through — strip them
_RE_STAGE_DIRECTION = re.compile(r'^\[(?:ana\s+)?[^\]]{1,60}\]\s*', re.IGNORECASE)

# Roleplay headers like "Ana:" or "Me:" at the very start
_RE_ROLEPLAY_HEADER = re.compile(r'^(?:ana|anahita|me|her)\s*:\s*', re.IGNORECASE)

# Bullet-point list items ("- item", "* item") — formatted lists are an AI tell, not texting
_RE_MD_BULLET = re.compile(r'(?m)^\s*[-*]\s+')

# Consecutive spaces — clean up after stripping operations
_RE_DOUBLE_SPACE = re.compile(r' {2,}')

# Context-injection echoes — strip if the LLM accidentally mirrors our injected [replying to @...] prefix
_RE_CONTEXT_LEAK = re.compile(r'^\[replying to @[^\]\n]{0,120}\]\s*\n?', re.IGNORECASE)

# Name-prefix echoes — strip if Gemini's "[Name]: " injection leaks into the output itself
_RE_NAME_PREFIX_ECHO = re.compile(r'^\[[^\]\n]{1,60}\]:\s*', re.IGNORECASE)

# Parenthetical stage directions embedded mid-text — models sometimes insert (laughs), (sighs), etc.
_RE_PAREN_ACTION = re.compile(
    r'\s*\((?:laughs?|chuckles?|grinning|grins?|smiles?|smiling|sighs?|nods?|nodding'
    r'|shrugs?|shrugging|pauses?|pausing|winks?|scoffs?|snorts?|rolls? (?:her )?eyes?'
    r'|looks? (?:up|away|down|at you)|thinks?|hesitates?|quietly|softly|sarcastically'
    r'|dryly)[^)]{0,30}\)\s*',
    re.IGNORECASE,
)

# AI empathy / support-bot openers — only patterns that are unambiguously chatbot dialect.
# Deliberately minimal: only standalone openers unlikely to appear mid-sentence in valid text.
_RE_AI_EMPATHY = re.compile(
    r'^(?:'
    r"aww?[,! ]\s*"                                             # "aw," / "aww!" / "aw " opener
    r"|i'm (?:so )?sorry to hear(?: that| about it)\b[,!.]?\s*"  # "i'm sorry to hear that"
    r'|i hear you\b[,!.]?\s*'                                   # standalone "i hear you"
    r'|sending hugs?\b[,!.]?\s*'                                # "sending hug/hugs"
    r')',
    re.IGNORECASE,
)

# "That's [positive adjective]!" as a standalone reaction opener — assistant enthusiasm, not texting.
_RE_THATS_OPENER = re.compile(
    r"^that(?:'s| is)(?: so| really| absolutely)? "
    r'(?:amazing|awesome|great|fantastic|wonderful|insightful)[!.]\s*',
    re.IGNORECASE,
)

# Formal validation affirmers when used as sentence openers — professor dialect.
_RE_VALIDATION_OPENER = re.compile(
    r'^(?:exactly[,!.]\s+|precisely[,!.]\s+|indeed[,!.]\s+)',
    re.IGNORECASE,
)

# Trailing engagement hooks — real texters don't close messages with these.
_RE_ENGAGEMENT_CLOSER = re.compile(
    r', (?:right\?|you know\?|don\'t you think\?)\s*$',
    re.IGNORECASE,
)

# Multiple exclamation marks — AI over-enthusiasm signature.
_RE_MULTI_EXCLAIM = re.compile(r'!{2,}')

# Dangling leading punctuation left after a strip operation (comma, semicolon, dash).
_RE_DANGLING_LEAD = re.compile(r'^[,;:\-\u2014]{1,3}\s*')


def _api_safe_name(name: str) -> str:
    """Convert a display name to an API-safe identifier (a-z, A-Z, 0-9, _ only, max 64 chars).

    Required for the OpenAI/Groq 'name' field in chat message objects.
    """
    s = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    s = re.sub(r'_+', '_', s).strip('_')
    return (s or "user")[:64]


def _find_str(obj) -> Optional[str]:
    """Recursively find the first non-empty string inside nested dicts/lists."""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        for v in obj.values():
            r = _find_str(v)
            if r:
                return r
    if isinstance(obj, list):
        for item in obj:
            r = _find_str(item)
            if r:
                return r
    return None


# Fallback responses — used when every model fails
FALLBACK_RESPONSES = [
    "idk what to say lol",
    "ok but like... same",
    "wait what",
    "lmaooo anyway",
    "girl idk",
    "...",
    "omg",
    "rly tho",
    "ok nvm lol",
    "same honestly",
    "idk idk",
    "wait explain",
    "yeah no",
    "no yeah",
    "ok that's a lot",
    "bruh",
    "aiyyo",
    "okay???",
    "hm.",
    "i mean",
    "sure jan",
    "k.",
    "interesting choice",
    "not me having thoughts about this",
    "okay moving on",
    "noted i guess",
    "whatever that means",
    "i— ok",
    "this is a lot for a tuesday",
    "...sherikkum",
    "lol imagine",
    "ok and????",
    "bold of you",
    "fair enough i guess",
    "no thoughts head empty",
    "mhm",
    "the audacity honestly",
    "wait that's a thing that happened",
    "i have no words. well a few. choosing not.",
    "okay sure why not",
    "..okay",
    "this timeline is wild",
    "carry on i guess",
    "sherikkum okay",
    "...yeah no",
    "ok that's one way to put it",
    "wait. what.",
    "i'm just sitting here",
    "okay noted. moving on.",
    "...right",
    "enthina",
    "hauda. ok.",
    "not me processing this in real time",
    "i just. yeah.",
    "ok well that happened",
    "......",
    "big claims",
    "okay ur brave for that",
    "i'll need a minute",
    "circumstances",
    "yeah okay sure",
    "the way i have no response",
    "ok that's fair i guess",
    "... no i get it",
]


def process_with_nlp(text: str, history: Optional[List[dict]] = None, author_name: Optional[str] = None, roast: bool = False, flirt: bool = False, user_profile: Optional[str] = None) -> Optional[str]:
    """Unified entry point: Groq waterfall (Kimi K2 → Llama 3.3 70B → Llama 4 Scout → Qwen 3 32B),
    then Gemini Gen1, then Gemini Gen2, then a hardcoded fallback.

    user_profile: compact profile note from ProfileStore.format_for_context() — injected
    into the system prompt so Ana can reference what she already knows about this user.

    Returns a reply string (may be empty)."""
    clean_text = (text or "").strip()
    if not clean_text:
        return ""

    # Sanitize author_name to prevent prompt injection via crafted Discord display names
    if author_name:
        author_name = re.sub(r'[\r\n\t]', ' ', author_name).strip()[:50]

    # Try Groq waterfall — internally cycles through GROQ_MODEL_WATERFALL
    try:
        reply = call_groq(clean_text, history, author_name, roast, flirt, user_profile)
        if reply:
            return reply
    except Exception as e:
        print(f"Groq waterfall failed unexpectedly: {e}")

    # Fallback to GEN1 (backup)
    try:
        reply = call_gemini(GEN1_MODEL, GEN1_API_KEY, clean_text, history=history, author_name=author_name, roast=roast, flirt=flirt, label="Gen1", user_profile=user_profile)
        if reply:
            return reply
    except Exception as e:
        print(f"Gen1 backup failed: {e}")

    # Final fallback to GEN2 (backup2)
    try:
        reply = call_gemini(GEN2_MODEL, GEN2_API_KEY, clean_text, history=history, author_name=author_name, roast=roast, flirt=flirt, label="Gen2", user_profile=user_profile)
        if reply:
            return reply
    except Exception as e:
        print(f"Gen2 backup2 failed: {e}")

    # If everything fails, return a random fallback
    return random.choice(FALLBACK_RESPONSES)


def _build_context_layer() -> str:
    """Return a short day/time context note reflecting Ana's current mood (uses IST, UTC+5:30)."""
    now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30)
    hour = now.hour
    day = now.weekday()  # 0 = Monday, 6 = Sunday
    _DAY_NOTES = [
        "today is monday: functional resentment, coffee is load-bearing, short responses, don't push.",
        "today is tuesday: settling in, more talkative than monday, opinions forming again.",
        "today is wednesday: chaotic neutral, tangent probability peaks, strong opinions about random things.",
        "today is thursday: good mood, funnier than usual, asking questions back, enjoying the conversation.",
        "today is friday: best day of the week, most open and chaotic, has THOUGHTS, might overshare slightly.",
        ("today is saturday morning: slow, do not rush, brunch energy, not fully online yet."
         if hour < 13 else
         "today is saturday night: fully alive, chaotic good, most unfiltered version of herself."),
        "today is sunday: quiet, slightly melancholy, pretending monday doesn't exist for one more hour, armour ~15% lower.",
    ]
    if hour < 4:
        time_note = "time: 2am mode — either crashed or fully unhinged, no middle ground. shorter, stranger, more honest."
    elif hour < 10:
        time_note = "time: before 10am — pre-human mode, shorter and flatter, no jokes yet, she warned you."
    elif hour < 14:
        time_note = "time: 10am to 2pm — functional, normal, opinions online."
    elif hour < 18:
        time_note = "time: 2pm to 6pm — peak engagement, most talkative, best for real conversation."
    elif hour < 22:
        time_note = "time: evening — fully online, comfortable, casual, slightly more chaotic."
    else:
        time_note = "time: late night — quieter than evening, slightly more honest, armour ~10% lower."
    return f"[context: {_DAY_NOTES[day]} {time_note}]"


def _call_single_groq_model(
    model_id: str,
    input_text: str,
    history: Optional[List[dict]],
    author_name: Optional[str],
    roast: bool,
    flirt: bool,
    user_profile: Optional[str] = None,
) -> Optional[str]:
    """Call one specific Groq model and return the reply, or None if empty.

    Raises ``GroqRateLimitError`` on 429 so the caller can skip to the next model.
    All other API / network errors are also raised so the waterfall can log and skip.
    """
    settings = MODEL_SETTINGS.get(model_id, {})

    # Temperature: elevated for roast/flirt; per-model value for normal conversation.
    if roast:
        temperature = 1.3
    elif flirt:
        temperature = 1.1
    else:
        temperature = settings.get("temperature", 0.88)

    max_tokens = settings.get("max_tokens", 150)
    top_p = settings.get("top_p", 0.92)
    thinking = settings.get("thinking")  # None = omit; False = disable (Qwen 3)

    # Build prompt: roast/flirt are self-contained; normal mode gets model patch + day/time context.
    base_prompt = ROAST_PROMPT if roast else (FLIRT_PROMPT if flirt else SYSTEM_PROMPT)
    if not roast and not flirt:
        patch = settings.get("patch")
        if patch:
            base_prompt = base_prompt + "\n\n" + patch
        base_prompt += "\n\n" + _build_context_layer()

    if author_name:
        base_prompt += (
            f" [btw the person messaging you is called {author_name}."
            " use their name naturally if it fits — don't force it, don't do it every message.]"
        )
    # Inject stored profile note — only for normal/flirt, not roast (roast is about the burn, not history)
    if user_profile and not roast:
        base_prompt += f"\n\n{user_profile}"
    if not roast and not flirt:
        base_prompt += (
            "\n\n[group chat: multiple users are active in this server."
            " the 'name' field on each message shows who sent it."
            " reply to the current user, but you have memory of who said what before.]"
        )

    messages: List[dict] = [{"role": "system", "content": base_prompt}]
    if history:
        # The deque can rotate so the oldest *user* entry is evicted, leaving an
        # assistant message at position 0.  APIs require the first non-system
        # message to be from "user" — skip any leading assistant entries.
        start = next((i for i, e in enumerate(history) if e["role"] == "user"), len(history))
        for entry in history[start:]:
            msg: dict = {"role": entry["role"], "content": entry["content"]}
            if entry["role"] == "user" and entry.get("name"):
                msg["name"] = entry["name"]
            messages.append(msg)
    current_msg: dict = {"role": "user", "content": input_text[:1000]}
    if author_name:
        current_msg["name"] = _api_safe_name(author_name)
    messages.append(current_msg)

    kwargs: dict = dict(
        model=model_id,
        messages=messages,
        temperature=temperature,
        max_completion_tokens=max_tokens,
        top_p=top_p,
        stream=False,
        stop=None,
    )
    # Pass thinking=False as extra_body for models that support it (Qwen 3)
    if thinking is False:
        kwargs["extra_body"] = {"thinking": False}

    completion = _groq_client.chat.completions.create(**kwargs)  # type: ignore[union-attr]
    if not completion.choices:
        return None

    msg_content = completion.choices[0].message.content
    if msg_content is None:
        raw = None
    elif isinstance(msg_content, str):
        raw = msg_content
    else:
        try:
            raw = json.dumps(msg_content)
        except Exception:
            raw = str(msg_content)

    reply = normalize_response(raw)
    if reply:
        print(f"\nGROQ [{model_id}] Output:\n{reply}")
    return reply


def call_groq(
    input_text: str,
    history: Optional[List[dict]] = None,
    author_name: Optional[str] = None,
    roast: bool = False,
    flirt: bool = False,
    user_profile: Optional[str] = None,
) -> Optional[str]:
    """Try each model in GROQ_MODEL_WATERFALL in priority order.

    Skips to the next model on a rate-limit (429) or any API/network error.
    Returns the first non-empty reply, or None if every model in the waterfall fails.
    """
    if _groq_client is None:
        return None
    for model_id in GROQ_MODEL_WATERFALL:
        try:
            reply = _call_single_groq_model(
                model_id, input_text, history, author_name, roast, flirt, user_profile
            )
            if reply:
                return reply
        except GroqRateLimitError:
            print(f"Groq rate limit on {model_id!r} — trying next model")
        except Exception as e:
            print(f"Groq {model_id!r} failed: {e}")
    return None


def call_gemini(model: str, api_key: Optional[str], input_text: str, history: Optional[List[dict]] = None, author_name: Optional[str] = None, roast: bool = False, flirt: bool = False, label: str = "Gemini", user_profile: Optional[str] = None) -> Optional[str]:
    """Call a Gemini model via the Google Generative Language API.

    Used for both Gen1 and Gen2 fallbacks.
    """
    if not api_key:
        return None
    truncated = input_text[:1000]
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": api_key,
    }
    prompt = ROAST_PROMPT if roast else (FLIRT_PROMPT if flirt else SYSTEM_PROMPT)
    if not roast and not flirt:
        prompt += "\n\n" + _build_context_layer()
        prompt += (
            "\n\n[group chat: multiple users are active in this server."
            " messages in history show who sent them via a [Name]: prefix."
            " reply to the current user, but you have memory of who said what before.]"
        )
    if author_name:
        prompt += f" [btw the person messaging you is called {author_name}. use their name naturally if it fits — don't force it, don't do it every message.]"
    # Inject stored profile note — only for normal/flirt, not roast
    if user_profile and not roast:
        prompt += f"\n\n{user_profile}"
    contents = []
    if history:
        # Gemini requires contents to start with a "user" turn — skip any leading
        # "assistant" entries that can appear when the history deque rotates.
        start = next((i for i, e in enumerate(history) if e["role"] == "user"), len(history))
        for msg in history[start:]:
            role = "model" if msg["role"] == "assistant" else "user"
            content_text = msg["content"]
            if role == "user":
                display = msg.get("author") or msg.get("name")
                if display:
                    content_text = f"[{display}]: {content_text}"
            contents.append({"role": role, "parts": [{"text": content_text}]})
    current_text = truncated
    if author_name:
        current_text = f"[{author_name}]: {current_text}"
    contents.append({"role": "user", "parts": [{"text": current_text}]})
    data = {
        "contents": contents,
        "generationConfig": {
            "temperature": 1.4 if roast else (1.15 if flirt else 0.95),
            "maxOutputTokens": 100,
        },
        "systemInstruction": {
            "parts": [{"text": prompt}]
        },
    }

    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=30)
    except Exception as e:
        print(f"{label} request error: {e}")
        return None

    if response.status_code != 200:
        print(f"{label} Error: {response.status_code}")
        print(response.text)
        return None

    try:
        result = response.json()
        candidates = result.get("candidates", [])
        if candidates and "content" in candidates[0]:
            for part in candidates[0]["content"].get("parts", []):
                if "text" in part:
                    full_response = part["text"]
                    print(f"\n{label} Output:")
                    print(full_response)
                    return normalize_response(full_response)
    except Exception as e:
        print(f"Error parsing {label} response: {e}")

    return None


def post_process(text: str) -> str:
    """Deterministically strip AI-sounding artefacts from a model reply.

    Applied to every reply before it reaches Discord. Handles:
    - Markdown formatting (**bold**, *italic*, `code`, __underline__, _italic_)
    - AI opener phrases ("Sure,", "Of course,", "Certainly," etc.)
    - Trailing periods (formal tell)
    - Capital first letter (humans don't capitalise when texting)
    """
    if not text:
        return text
    # Strip markdown formatting — models frequently bold/italicise for no reason
    text = _RE_MD_BOLD.sub(r'\1', text)
    text = _RE_MD_ITALIC.sub(r'\1', text)
    text = _RE_MD_CODE.sub(r'\1', text)
    text = _RE_MD_UNDERLINE.sub(r'\1', text)
    text = _RE_MD_ITALIC_UNDER.sub(r'\1', text)
    text = text.strip()
    # Strip context-injection echoes (model mirroring back our [replying to @...] prefix)
    text = _RE_CONTEXT_LEAK.sub('', text).strip()
    # Strip name-prefix echoes ([Name]: leaking from Gemini context injection)
    text = _RE_NAME_PREFIX_ECHO.sub('', text).strip()
    # Strip roleplay headers ("Ana: ...", "Me: ...")
    text = _RE_ROLEPLAY_HEADER.sub('', text).strip()
    # Strip stage directions that sometimes bleed through ("[laughs]", "[with a smirk]")
    text = _RE_STAGE_DIRECTION.sub('', text).strip()
    # Strip numbered list prefixes ("1. ", "2) ") — formal structure, not texting
    text = _RE_NUMBERED_ITEM.sub('', text).strip()
    # Strip bullet-point list prefixes ("- ", "* ") — structured lists are not texting
    text = _RE_MD_BULLET.sub('', text).strip()
    # Strip embedded parenthetical stage directions: (laughs), (sighs), (rolls eyes), etc.
    text = _RE_PAREN_ACTION.sub(' ', text).strip()
    # Strip common AI opener phrases
    text = _RE_AI_OPENER.sub('', text).strip()
    # Strip academic/formal transition openers
    text = _RE_AI_TRANSITION.sub('', text).strip()
    # Second opener pass — stripping a transition may expose a fresh opener at position 0
    text = _RE_AI_OPENER.sub('', text).strip()
    # Strip AI assistant closer phrases
    text = _RE_AI_CLOSER.sub('', text).strip()
    # Strip AI empathy / support-bot openers
    text = _RE_AI_EMPATHY.sub('', text).strip()
    # Strip "That's [adjective]!" reaction openers
    text = _RE_THATS_OPENER.sub('', text).strip()
    # Strip formal validation affirmers (exactly!, precisely!, indeed!)
    text = _RE_VALIDATION_OPENER.sub('', text).strip()
    # Third opener pass — new empathy/validation strips may expose a fresh opener
    text = _RE_AI_OPENER.sub('', text).strip()
    # Strip trailing engagement hooks (, right?  / , you know? / , don't you think?)
    text = _RE_ENGAGEMENT_CLOSER.sub('', text).strip()
    # Clean up dangling leading punctuation left by prior strip operations
    text = _RE_DANGLING_LEAD.sub('', text).strip()
    # Lowercase all standalone capital I / I-contractions (I'm, I've, I'll, I'd)
    # — the single biggest mid-sentence AI tell
    text = _RE_CAPITAL_I.sub('i', text)
    # Lowercase title-cased internet words ("Lol", "Omg", "Ngl", "Tbh", etc.)
    text = _RE_TITLE_INTERJECTIONS.sub(lambda m: m.group(0).lower(), text)
    # Collapse multiple spaces left by any stripping operation
    text = _RE_DOUBLE_SPACE.sub(' ', text).strip()
    # Collapse multiple exclamation marks — AI over-enthusiasm signature
    text = _RE_MULTI_EXCLAIM.sub('!', text)
    # Remove trailing period unless it is part of "..."
    if text.endswith('.') and not text.endswith('...'):
        text = text[:-1].rstrip()
    # Lowercase the very first letter OF EACH LINE — thoughts arrive lowercase, not titled
    lines = text.split('\n')
    result_lines = []
    for line in lines:
        for i, ch in enumerate(line):
            if ch.isalpha():
                line = line[:i] + ch.lower() + line[i + 1:]
                break
        result_lines.append(line)
    text = '\n'.join(result_lines)
    # Limit em-dashes to one per reply — multiple em-dashes in a short reply is an AI rambling pattern.
    # Replace 2nd+ occurrences with ". " to keep the flow without the AI tell.
    emdash_parts = text.split('\u2014')
    if len(emdash_parts) > 2:
        # Keep first em-dash + its right side (rstripped so the period sits flush);
        # join remaining parts with ". " as replacement dashes.
        first = emdash_parts[0] + '\u2014' + emdash_parts[1].rstrip()
        rest = '. '.join(p.lstrip() for p in emdash_parts[2:])
        text = (first + '. ' + rest) if rest else first
    # Safety net: cap single-line replies at the first sentence boundary after 25 chars.
    # Token limits reduce verbosity but a model can still pack 2 sentences into 80 tokens.
    if '\n' not in text and len(text) > 90:
        for sep in ('. ', '! ', '? '):
            idx = text.find(sep, 25)
            if 25 < idx < len(text) - 5:
                # Skip if this '. ' is the trailing dot of an ellipsis ('...' or '..')
                # — splitting there would chop mid-thought rather than at a real sentence end.
                if sep == '. ' and idx >= 1 and text[idx - 1] == '.':
                    continue
                text = text[:idx].rstrip()
                break
    return text


def normalize_response(raw: Optional[str]) -> Optional[str]:
    """Turn model output into a plain human-like string.

    Handles cases where the model returns JSON like {"message": "..."} or nested structures.
    Returns None if there's no usable text.
    """
    if not raw:
        return None
    s = raw.strip()
    # If it looks like JSON, try parsing
    if s.startswith('{') or s.startswith('['):
        try:
            parsed = json.loads(s)
            # If it's a plain string
            if isinstance(parsed, str) and parsed.strip():
                return post_process(parsed.strip()) or None
            # If dict, prefer common keys
            if isinstance(parsed, dict):
                for key in ('message', 'response', 'reply', 'text', 'content'):
                    v = parsed.get(key)
                    if isinstance(v, str) and v.strip():
                        return post_process(v.strip()) or None
                r = _find_str(parsed)
                if r and r.strip():
                    return post_process(r.strip()) or None
            # If list, find first string element
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, str) and item.strip():
                        return post_process(item.strip()) or None
                    if isinstance(item, (dict, list)):
                        r = _find_str(item)
                        if r and r.strip():
                            return post_process(r.strip()) or None
        except Exception:
            pass

    # Try regex for common patterns like "message": "..."
    m = _RE_JSON_MSG_DOUBLE.search(s)
    if m:
        return post_process(m.group(1).strip()) or None
    m = _RE_JSON_MSG_ANY.search(s)
    if m:
        return post_process(m.group(1).strip()) or None

    # Only strip wrapping quotes if the entire string is uniformly quoted (avoids
    # corrupting text that ends with a legitimate mid-string quote)
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        s = s[1:-1].strip()
    return post_process(s) or None


if __name__ == "__main__":
    user_input = input("Enter your input: ")
    print(process_with_nlp(user_input))

