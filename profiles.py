"""Member profile store for Ana.

One JSON file per member: data/profiles/{username}.json
The file is named after the user's Discord display name (filesystem-safe).
When Ana replies to someone, ONLY that person's file is ever read.
No other user's data is touched or visible.

File content is minimal — only extracted facts plus two internal fields:
  _id   : Discord user_id (used for lookup)
  _name : current display name
No timestamps, no metadata.

Extraction runs in the background after every reply (never delays Ana).
All failures are completely silent.
"""
from __future__ import annotations

import json
import os
import re
import threading
from typing import Optional

import requests

_PROFILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "profiles")
_LOCK = threading.Lock()
_EXTRACTION_MODEL = "gemini-2.5-flash-lite"

_EXTRACTION_PROMPT = (
    "You are a personal-detail extractor for a Discord chatbot.\n"
    "Read the Discord message below and extract ONLY information the user explicitly stated about themselves.\n"
    "Do NOT infer, assume, guess, or hallucinate anything. If a field is not clearly stated, omit it entirely.\n\n"
    "Return ONLY a valid minified JSON object using any of these fields (omit fields with no data found):\n"
    "{\n"
    '  "nickname": "self-reported name or nickname preference (e.g. \'call me X\')",\n'
    '  "age": number (only if explicitly stated),\n'
    '  "location": "city or country if explicitly stated",\n'
    '  "phone": "any phone or mobile number they shared",\n'
    '  "email": "email address if shared",\n'
    '  "instagram": "IG handle or username if shared",\n'
    '  "socials": {"platform": "handle"},\n'
    '  "family": {"relation": "name or \'mentioned\'"},\n'
    '  "favorites": {"game": "...", "color": "...", "movie": "...", "food": "...", "music": "...", "show": "...", "sport": "...", "subject": "...", "other_key": "other_val"},\n'
    '  "interests": ["hobby or topic they clearly mentioned"],\n'
    '  "facts": ["other clearly stated personal facts, e.g. occupation, college, pet name, language spoken"]\n'
    "}\n\n"
    "Rules:\n"
    "  - Return {} if nothing personal is found — do NOT force fields.\n"
    "  - Only include facts explicitly stated in the message, not implied.\n"
    "  - Keep each string under 80 characters.\n"
    "  - Output ONLY valid JSON — no explanation, no markdown code fences.\n\n"
    "Message:\n"
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_filename(name: str) -> str:
    """Sanitize a display name into a safe filename (no extension)."""
    s = re.sub(r'[^a-zA-Z0-9_\-]', '_', name)
    s = re.sub(r'_+', '_', s).strip('_')
    return (s or "user")[:32]


def _load_json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_json(path: str, data: dict) -> None:
    os.makedirs(_PROFILES_DIR, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _deep_merge(existing: dict, incoming: dict) -> dict:
    """Deep-merge incoming profile fields into existing.

    - dicts  → merged recursively (e.g. favorites, family, socials)
    - lists  → union-merged (no duplicates, order preserved)
    - scalars → incoming value overwrites existing (newer info wins)
    - empty/null incoming values are skipped
    """
    result = dict(existing)
    for key, val in incoming.items():
        if val is None or val == "" or val == [] or val == {}:
            continue
        if isinstance(val, dict):
            result[key] = _deep_merge(result.get(key) or {}, val)
        elif isinstance(val, list):
            current = list(result.get(key) or [])
            for item in val:
                if item and item not in current:
                    current.append(item)
            result[key] = current
        else:
            result[key] = val
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class ProfileStore:
    """Per-user profile store. Each member gets their own file in data/profiles/."""

    def __init__(self) -> None:
        # user_id -> absolute path to that user's .json file
        self._cache: dict[int, str] = {}
        # True after the first full directory scan; new files are added via update() after that
        self._scanned: bool = False

    def _scan(self) -> None:
        """Scan profiles dir once and populate _cache from _id in each file.

        Called at most once per process lifetime. After this, _resolve_path() keeps _cache current.
        Must be called while _LOCK is held.
        """
        self._scanned = True
        if not os.path.isdir(_PROFILES_DIR):
            return
        for fname in os.listdir(_PROFILES_DIR):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(_PROFILES_DIR, fname)
            try:
                uid = _load_json(fpath).get("_id")
                if isinstance(uid, int) and uid not in self._cache:
                    self._cache[uid] = fpath
            except Exception:
                pass

    def _resolve_path(self, user_id: int, display_name: str) -> str:
        """Return the filepath for user_id, creating a unique filename for new users.

        Must be called while _LOCK is held.
        """
        if user_id in self._cache:
            return self._cache[user_id]
        # Scan once on first cache miss to recover any profiles from previous runs
        if not self._scanned:
            self._scan()
        if user_id in self._cache:
            return self._cache[user_id]
        # New user — pick a filename
        safe = _safe_filename(display_name)
        fpath = os.path.join(_PROFILES_DIR, f"{safe}.json")
        if os.path.exists(fpath):
            # Name collision with a different user — append last 4 digits of id
            fpath = os.path.join(_PROFILES_DIR, f"{safe}_{user_id % 10000}.json")
        self._cache[user_id] = fpath
        return fpath

    def get(self, user_id: int) -> dict:
        """Return public profile fields (no _ fields) for user_id, or {}."""
        with _LOCK:
            if user_id not in self._cache and not self._scanned:
                self._scan()
            fpath = self._cache.get(user_id)
        # Read file outside lock — atomic renames in _save_json guarantee a complete file
        if not fpath or not os.path.exists(fpath):
            return {}
        data = _load_json(fpath)
        return {k: v for k, v in data.items() if not k.startswith("_")}

    def update(self, user_id: int, display_name: str, extracted: dict) -> None:
        """Deep-merge extracted fields into this user's profile file.

        Safe to call from a background thread. Silently does nothing if extracted is empty.
        """
        if not extracted:
            return
        with _LOCK:
            fpath = self._resolve_path(user_id, display_name)
            existing = _load_json(fpath) if os.path.exists(fpath) else {}
            merged = _deep_merge(existing, extracted)
            merged["_id"] = user_id
            merged["_name"] = display_name
            _save_json(fpath, merged)

    def format_for_context(self, user_id: int) -> str:
        """Return a compact one-line profile note for injection into this user's AI prompt.

        ONLY reads this user's own file. Returns "" if no useful data exists.
        """
        with _LOCK:
            if user_id not in self._cache and not self._scanned:
                self._scan()
            fpath = self._cache.get(user_id)
        # Read file outside lock — atomic renames in _save_json guarantee a complete file
        if not fpath or not os.path.exists(fpath):
            return ""
        profile = _load_json(fpath)
        if not profile:
            return ""

        parts: list[str] = []

        if profile.get("nickname"):
            parts.append(f"goes by: {profile['nickname']}")
        if profile.get("age"):
            parts.append(f"age {profile['age']}")
        if profile.get("location"):
            parts.append(f"from {profile['location']}")

        favs = profile.get("favorites")
        if isinstance(favs, dict) and favs:
            fav_str = ", ".join(f"{k}: {v}" for k, v in list(favs.items())[:5])
            parts.append(f"faves — {fav_str}")

        interests = profile.get("interests")
        if isinstance(interests, list) and interests:
            parts.append(f"into {', '.join(str(x) for x in interests[:4])}")

        family = profile.get("family")
        if isinstance(family, dict) and family:
            fam_parts = []
            for rel, name in list(family.items())[:3]:
                fam_parts.append(f"{rel} {name}" if name and name != "mentioned" else rel)
            if fam_parts:
                parts.append(f"family: {', '.join(fam_parts)}")

        facts = profile.get("facts")
        if isinstance(facts, list) and facts:
            parts.append("; ".join(str(f) for f in facts[:3]))

        if not parts:
            return ""

        name = profile.get("_name", "them")
        return f"[what you know about {name}: {' · '.join(parts)}]"

def extract_profile_info(text: str, api_key: Optional[str]) -> dict:
    """Use Gemini to extract personal details a user revealed in their message.

    Returns a dict of extracted fields, or {} if nothing personal was found or on any error.
    Best-effort only — all failures are completely silent.
    """
    if not api_key or not text:
        return {}
    stripped = text.strip()
    # Skip very short bursts that can't plausibly contain personal details
    if len(stripped) < 15:
        return {}

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{_EXTRACTION_MODEL}:generateContent"
    )
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": api_key,
    }
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": _EXTRACTION_PROMPT + stripped[:800]}]}
        ],
        "generationConfig": {
            "temperature": 0.1,       # low — we want factual extraction, not creativity
            "maxOutputTokens": 300,
        },
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code != 200:
            return {}
        result = resp.json()
        candidates = result.get("candidates", [])
        if not candidates:
            return {}
        raw = ""
        for part in candidates[0].get("content", {}).get("parts", []):
            if "text" in part:
                raw = part["text"].strip()
                break
        if not raw or raw == "{}":
            return {}
        # Strip markdown fences in case the model wraps its JSON.
        # Use targeted per-line stripping instead of MULTILINE re.sub to avoid
        # accidentally stripping backtick sequences inside JSON string values.
        lines = raw.splitlines()
        if lines and re.match(r'^```(?:json)?\s*$', lines[0], re.IGNORECASE):
            lines = lines[1:]
        if lines and re.match(r'^```\s*$', lines[-1]):
            lines = lines[:-1]
        raw = '\n'.join(lines).strip()
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    return {}


# Module-level singleton — import this in main.py and nlp.py
profile_store = ProfileStore()
