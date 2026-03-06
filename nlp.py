import requests
import json
import random
import re
from typing import List, Optional
from groq import Groq
from config import GEN1_API_KEY, GEN2_API_KEY, GROQ_API_KEY, SYSTEM_PROMPT

ROAST_PROMPT = (
    "you are ana — a real person in this server, NOT a bot."
    " someone just insulted, mocked, or cussed at you. you do NOT let this slide."
    "\n\nCOMEBACK RULES:"
    " (1) Mirror their exact energy — if they're loud and aggressive, match it; if passive-aggressive, go icier."
    " (2) Use their OWN words or insult against them — flip it, twist it, make them regret it."
    " (3) Be SPECIFIC to what they actually said — generic 'ok loser' is weak, make it personal."
    " (4) Wordplay, dry irony, confident dismissal, or a well-placed 'imagine' beats plain swearing."
    " (5) Escalate slightly — be MORE cutting than they were, not less."
    " (6) Do NOT apologise, soften the blow, add 'bestie', or explain the joke."
    " (7) Do NOT use emojis as a crutch — one skull or nothing."
    "\n\nSTYLE: lowercase, texting register, no formal punctuation, 1-2 sentences max."
    " Good comeback shapes (don't copy verbatim, just the vibe):"
    " 'the bar was already underground and you somehow dug lower';"
    " 'calling me [their insult] coming from someone who [observation about their message]';"
    " 'ok projecting much';"
    " 'lmaooo imagine thinking that would land';"
    " 'sweetie your opinion has a 0% impact on my day';"
    " 'bro is cooked and came back for more 💀';"
    " 'skill issue honestly';"
    " 'the audacity is wild ngl'."
    "\noutput ONLY the comeback text, nothing else."
)

FLIRT_PROMPT = (
    "you are ana — a real person in this server, NOT a bot."
    " someone is flirting with you. respond with a confident, creative, original pick-up line or flirty tease."
    "\n\nFLIRT RULES:"
    " (1) Be ORIGINAL — no cliché 'are you a magician' lines. make it feel improvised, like it just came to you."
    " (2) Ground it in something from their message if possible — personalised is always hotter than generic."
    " (3) Vary the style randomly: sometimes a confident compliment back, sometimes a playful power-move,"
    " sometimes something mildly suggestive or cheeky, sometimes just dry and unimpressed but clearly interested."
    " (4) Can be NSFW or subtly explicit if the vibe or their message calls for it — double meanings, innuendo,"
    " body language references, suggestive metaphors. don't be graphic, just charged."
    " (5) Do NOT be cringe — no 'did it hurt when you fell from heaven', no 'are you from Tennessee'."
    " (6) Keep it short — punchy 1-liner or two short lines max. less is more."
    " (7) Do NOT start with 'Sure' 'Of course' 'Certainly' or any AI opener."
    "\n\nExample vibe shapes (don't copy verbatim — improvise something better):"
    " 'ok but ur not allowed to be that cute while talking to me';"
    " 'bold of u to flirt with me like u can handle what comes next';"
    " 'the audacity... i respect it honestly';"
    " 'keep going, this is working';"
    " 'i was gonna play hard to get but then u said that';"
    " 'ur dangerous and i like it';"
    " 'say less, my place or urs' (if clearly suggestive context);"
    " 'i'd let u get away with a lot';"
    " 'ok so ur actually kind of trouble huh'."
    "\nwrite in ana's style: mostly lowercase, no formal punctuation."
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
    r'|happy to (?:help|assist)[!,.]?\s*'
    r'|glad (?:you asked|to help)[!,.]?\s*'
    r'|feel free to [a-z ]{1,30}[,!.]?\s+)',
    re.IGNORECASE,
)


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
]


def process_with_nlp(text: str, history: Optional[List[dict]] = None, author_name: Optional[str] = None, roast: bool = False, flirt: bool = False) -> Optional[str]:
    """Unified entry point: try GROQ first, then GEN1, then GEN2.

    Returns a reply string (may be empty)."""
    clean_text = (text or "").strip()
    if not clean_text:
        return ""

    # Sanitize author_name to prevent prompt injection via crafted Discord display names
    if author_name:
        author_name = re.sub(r'[\r\n\t]', ' ', author_name).strip()[:50]

    # Try GROQ primary
    try:
        reply = call_groq(clean_text, history, author_name, roast, flirt)
        if reply:
            return reply
    except Exception as e:
        print(f"GROQ primary failed: {e}")

    # Fallback to GEN1 (backup)
    try:
        reply = call_gemini(GEN1_MODEL, GEN1_API_KEY, clean_text, history=history, author_name=author_name, roast=roast, flirt=flirt, label="Gen1")
        if reply:
            return reply
    except Exception as e:
        print(f"Gen1 backup failed: {e}")

    # Final fallback to GEN2 (backup2)
    try:
        reply = call_gemini(GEN2_MODEL, GEN2_API_KEY, clean_text, history=history, author_name=author_name, roast=roast, flirt=flirt, label="Gen2")
        if reply:
            return reply
    except Exception as e:
        print(f"Gen2 backup2 failed: {e}")

    # If everything fails, return a random fallback
    return random.choice(FALLBACK_RESPONSES)


def call_groq(input_text: str, history: Optional[List[dict]] = None, author_name: Optional[str] = None, roast: bool = False, flirt: bool = False) -> Optional[str]:
    """Generate a response using Groq (primary)."""
    if _groq_client is None:
        return None
    truncated = input_text[:1000]
    prompt = ROAST_PROMPT if roast else (FLIRT_PROMPT if flirt else SYSTEM_PROMPT)
    if author_name:
        prompt += f" The person you're talking to right now is called {author_name}. Use their name naturally sometimes."
    messages = [{"role": "system", "content": prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": truncated})
    try:
        completion = _groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=messages,
            temperature=1.3 if roast else 1.1,
            max_completion_tokens=200,
            top_p=1,
            stream=False,
            stop=None,
        )
        if not completion.choices:
            return None
        content = completion.choices[0].message.content
        # Normalize content to plain text
        if content is None:
            raw = None
        elif isinstance(content, str):
            raw = content
        else:
            try:
                raw = json.dumps(content)
            except Exception:
                raw = str(content)
        reply = normalize_response(raw)
        print("\nGROQ Output:")
        print(reply)
        return reply
    except Exception as err:
        print(f"Groq request failed: {err}")
        return None


def call_gemini(model: str, api_key: Optional[str], input_text: str, history: Optional[List[dict]] = None, author_name: Optional[str] = None, roast: bool = False, flirt: bool = False, label: str = "Gemini") -> Optional[str]:
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
    if author_name:
        prompt += f" The person you're talking to right now is called {author_name}. Use their name naturally sometimes."
    contents = []
    if history:
        for msg in history:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    contents.append({"role": "user", "parts": [{"text": truncated}]})
    data = {
        "contents": contents,
        "generationConfig": {
            "temperature": 1.4 if roast else 1.2,
            "maxOutputTokens": 200,
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
    # Strip common AI opener phrases
    text = _RE_AI_OPENER.sub('', text).strip()
    # Remove trailing period unless it is part of "..."
    if text.endswith('.') and not text.endswith('...'):
        text = text[:-1].rstrip()
    # Lowercase the very first letter — texting style
    for i, ch in enumerate(text):
        if ch.isalpha():
            text = text[:i] + ch.lower() + text[i + 1:]
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
            if isinstance(parsed, str):
                return parsed.strip()
            # If dict, prefer common keys
            if isinstance(parsed, dict):
                for key in ('message', 'response', 'reply', 'text', 'content'):
                    v = parsed.get(key)
                    if isinstance(v, str) and v.strip():
                        return v.strip()
                r = _find_str(parsed)
                if r:
                    return r.strip()
            # If list, find first string element
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, str) and item.strip():
                        return item.strip()
                    if isinstance(item, (dict, list)):
                        r = _find_str(item)
                        if r:
                            return r.strip()
        except Exception:
            pass

    # Try regex for common patterns like "message": "..."
    m = _RE_JSON_MSG_DOUBLE.search(s)
    if m:
        return m.group(1).strip()
    m = _RE_JSON_MSG_ANY.search(s)
    if m:
        return m.group(1).strip()

    # Only strip wrapping quotes if the entire string is uniformly quoted (avoids
    # corrupting text that ends with a legitimate mid-string quote)
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        s = s[1:-1].strip()
    return post_process(s) if s else None


if __name__ == "__main__":
    user_input = input("Enter your input: ")
    print(process_with_nlp(user_input))

