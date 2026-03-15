"""Reminder system for Ana.

Users set reminders with: !remindme <natural language>
Gemini parses the input into structured JSON and stores it in data/reminders/reminders.json.
A background task polls every minute and fires AI-generated wish/reminder messages.

Each reminder record:
  id            : UUID4 string
  user_id       : int  (Discord user ID)
  user_name     : str  (display name at time of setting)
  channel_id    : int  (channel where the reminder was set)
  datetime_ist  : str  (ISO 8601, no tz suffix — always IST)
  occasion      : str  (human-readable event description)
  occasion_type : str  (birthday|anniversary|wedding|exam|meeting|custom)
  notes         : str  (extra details, may be empty)
  done          : bool
  created_at    : str  (ISO 8601)
"""
from __future__ import annotations

import datetime
import json
import os
import re
import threading
import time
import uuid
from typing import Optional

import requests

_REMINDERS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "reminders")
_REMINDERS_FILE = os.path.join(_REMINDERS_DIR, "reminders.json")
_LOCK = threading.Lock()
_IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-flash-latest:generateContent"
)
_ALLOWED_OCCASION_TYPES = {"birthday", "anniversary", "wedding", "exam", "meeting", "custom"}


def _post_with_retries(
    url: str,
    *,
    headers: dict,
    payload: dict,
    timeout: float,
    attempts: int = 3,
) -> Optional[requests.Response]:
    """POST with bounded retry/backoff for transient network and 5xx/429 responses."""
    for attempt in range(1, attempts + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < attempts:
                time.sleep(0.35 * attempt)
                continue
            return resp
        except requests.RequestException:
            if attempt >= attempts:
                return None
            time.sleep(0.35 * attempt)
    return None


# ---------------------------------------------------------------------------
# Gemini helper
# ---------------------------------------------------------------------------

def _gemini_post(api_key: str, prompt: str, temperature: float, max_tokens: int) -> Optional[str]:
    """Single reusable Gemini POST. Returns the first text part, or None on any failure."""
    headers = {"Content-Type": "application/json", "X-goog-api-key": api_key}
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }
    try:
        resp = _post_with_retries(_GEMINI_URL, headers=headers, payload=payload, timeout=15, attempts=3)
        if resp is None:
            import sys
            print("[reminders] Gemini network failure after retries", file=sys.stderr)
            return None
        if resp.status_code != 200:
            import sys
            print(f"[reminders] Gemini HTTP {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
            return None
        candidates = resp.json().get("candidates", [])
        if not candidates:
            return None
        for part in candidates[0].get("content", {}).get("parts", []):
            if "text" in part:
                return part["text"].strip()
    except Exception as e:
        import sys
        print(f"[reminders] Gemini error: {e}", file=sys.stderr)
    return None


# ---------------------------------------------------------------------------
# Parsing — natural language → structured JSON
# ---------------------------------------------------------------------------

def _parse_prompt(now_ist_str: str) -> str:
    return (
        f"Current date and time in IST: {now_ist_str}\n\n"
        "Parse the reminder request below into a JSON object with EXACTLY these fields:\n"
        "{\n"
        '  "datetime_ist": "<ISO 8601 without tz suffix, e.g. 2026-03-15T10:00:00>",\n'
        '  "occasion": "<short human-readable event description>",\n'
        '  "occasion_type": "<one of: birthday|anniversary|wedding|exam|meeting|custom>",\n'
        '  "notes": "<any extra details the user mentioned, or empty string>"\n'
        "}\n\n"
        "Rules:\n"
        "  - Resolve relative dates (today, tomorrow, next week, next month) using today's date.\n"
        "  - If no time is specified, default to 09:00:00.\n"
        "  - If year is not mentioned and the date has already passed this calendar year, use next year.\n"
        "  - occasion_type should be inferred from the occasion text (e.g. 'bday' → birthday).\n"
        "  - Output ONLY valid minified JSON — no markdown fences, no explanation, nothing else.\n\n"
        "Reminder request: "
    )


def parse_reminder(
    raw_text: str,
    user_id: int,
    user_name: str,
    channel_id: int,
    api_key: str,
) -> Optional[dict]:
    """Call Gemini to parse a free-form reminder request into a structured dict.

    Returns a complete reminder record ready to be stored, or None if parsing fails.
    """
    if not api_key or not raw_text.strip():
        return None

    now_str = datetime.datetime.now(_IST).strftime("%Y-%m-%d %H:%M IST (%A)")
    prompt = _parse_prompt(now_str) + raw_text.strip()[:600]

    raw = _gemini_post(api_key, prompt, temperature=0.1, max_tokens=200)
    if not raw:
        return None

    # Strip optional markdown fences the model sometimes adds
    lines = raw.splitlines()
    if lines and re.match(r"^```(?:json)?\s*$", lines[0], re.IGNORECASE):
        lines = lines[1:]
    if lines and re.match(r"^```\s*$", lines[-1]):
        lines = lines[:-1]
    raw = "\n".join(lines).strip()

    try:
        parsed = json.loads(raw)
    except Exception:
        return None

    if not isinstance(parsed, dict) or "datetime_ist" not in parsed:
        return None

    # Validate and normalize parsed fields before persisting.
    dt_raw = str(parsed.get("datetime_ist", "")).strip()
    if not dt_raw:
        return None
    try:
        dt_obj = datetime.datetime.fromisoformat(dt_raw)
    except Exception:
        return None
    if dt_obj.tzinfo is not None:
        # Store timezone-naive ISO string in IST convention to match existing file format.
        dt_obj = dt_obj.astimezone(_IST).replace(tzinfo=None)

    occasion = str(parsed.get("occasion", "reminder")).strip()[:120] or "reminder"
    occasion_type = str(parsed.get("occasion_type", "custom")).strip().lower()
    if occasion_type not in _ALLOWED_OCCASION_TYPES:
        occasion_type = "custom"
    notes = str(parsed.get("notes", "")).strip()[:200]

    return {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "user_name": user_name,
        "channel_id": channel_id,
        "datetime_ist": dt_obj.isoformat(timespec="seconds"),
        "occasion": occasion,
        "occasion_type": occasion_type,
        "notes": notes,
        "done": False,
        "created_at": datetime.datetime.now(_IST).isoformat(),
    }


# ---------------------------------------------------------------------------
# Wish / reminder message generation
# ---------------------------------------------------------------------------

_WISH_SYSTEM = (
    "you are ana — anahita, 23, NRI malayali. you're sending a reminder or wish to someone in a discord server.\n\n"
    "write a short message in ana's voice:\n"
    "- lowercase always, fragmented, genuine warmth hidden under dry tone\n"
    "- mention the person's name naturally — don't force it onto every line\n"
    "- 1 to 3 lines max. never a wall of text. most wishes fit in one punchy line.\n\n"
    "tone by occasion type:\n"
    "  birthday     — dry warmth, maybe lightly teasing but genuinely happy. NOT hollow 'happy birthday!!'\n"
    "  anniversary  — actually warm, quiet, brief. she means it and doesn't perform it.\n"
    "  wedding      — warm congratulations, single line, genuine.\n"
    "  exam         — practical nudge. a little faith in them. not a pep talk.\n"
    "  meeting      — casual reminder, slightly impatient if they might forget.\n"
    "  custom       — her natural voice. read the occasion and match the energy.\n\n"
    "NEVER use: 'hope this helps', 'best wishes', 'warm regards', hollow exclamations, formal openers.\n"
    "output ONLY the final message text. no quotes, no labels, no explanation.\n\n"
    "reminder details:\n"
)


def generate_wish(reminder: dict, api_key: str) -> Optional[str]:
    """Generate an Ana-style wish/reminder message using Gemini.

    Uses a two-step reasoning prompt: Gemini is asked to first assess the right tone
    then produce the final message — both in a single call, output is the message only.
    """
    if not api_key:
        return None

    detail = (
        f"person's name: {reminder.get('user_name', 'someone')}\n"
        f"occasion: {reminder.get('occasion', 'reminder')}\n"
        f"occasion type: {reminder.get('occasion_type', 'custom')}\n"
    )
    if reminder.get("notes"):
        detail += f"extra details: {reminder['notes']}\n"

    # Reasoning step baked into the prompt — ask the model to consider tone before writing,
    # but output only the final message. This produces more contextually appropriate results
    # than a direct generation instruction.
    prompt = (
        _WISH_SYSTEM
        + detail
        + "\nbefore writing, consider silently: what specific tone fits this occasion type "
        "and this person's name? is it warm, teasing, practical, or quiet?\n"
        "then output ONLY the final message — nothing else."
    )

    return _gemini_post(api_key, prompt, temperature=1.1, max_tokens=150)


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

class ReminderStore:
    """Thread-safe persistent reminder store backed by a single JSON array file."""

    def __init__(self) -> None:
        self._reminders: list[dict] = []
        self._loaded: bool = False

    def _load(self) -> None:
        """Populate from disk. Must be called while _LOCK is held."""
        if self._loaded:
            return
        self._loaded = True
        if not os.path.exists(_REMINDERS_FILE):
            return
        try:
            with open(_REMINDERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self._reminders = data
        except Exception:
            self._reminders = []

    def _save(self) -> None:
        """Atomic write. Must be called while _LOCK is held."""
        os.makedirs(_REMINDERS_DIR, exist_ok=True)
        tmp = _REMINDERS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._reminders, f, ensure_ascii=False, indent=2)
        os.replace(tmp, _REMINDERS_FILE)

    def add(self, reminder: dict) -> None:
        with _LOCK:
            self._load()
            self._reminders.append(reminder)
            self._save()

    def get_due(self, now_ist: datetime.datetime) -> list[dict]:
        """Return copies of all pending reminders whose datetime_ist <= now_ist."""
        with _LOCK:
            self._load()
            due = []
            for r in self._reminders:
                if r.get("done"):
                    continue
                try:
                    dt = datetime.datetime.fromisoformat(r["datetime_ist"]).replace(tzinfo=_IST)
                    if dt <= now_ist:
                        due.append(dict(r))
                except Exception:
                    pass
            return due

    def mark_done(self, reminder_id: str) -> None:
        with _LOCK:
            self._load()
            for r in self._reminders:
                if r.get("id") == reminder_id:
                    r["done"] = True
                    break
            self._save()

    def mark_done_if_pending(self, reminder_id: str) -> bool:
        """Mark a reminder done only if it exists and is still pending.

        Returns True when a pending reminder was marked done, False otherwise.
        """
        with _LOCK:
            self._load()
            for r in self._reminders:
                if r.get("id") == reminder_id:
                    if r.get("done"):
                        return False
                    r["done"] = True
                    self._save()
                    return True
        return False

    def list_pending(self, user_id: int) -> list[dict]:
        """Return pending reminders for a user sorted by datetime_ist."""
        with _LOCK:
            self._load()
            pending = [
                r for r in self._reminders
                if r.get("user_id") == user_id and not r.get("done")
            ]
        pending.sort(key=lambda r: r.get("datetime_ist", ""))
        return pending

    def cancel(self, user_id: int, id_prefix: str) -> bool:
        """Cancel the first pending reminder whose id starts with id_prefix. Returns True on success."""
        with _LOCK:
            self._load()
            for r in self._reminders:
                if (
                    r.get("user_id") == user_id
                    and not r.get("done")
                    and r.get("id", "").startswith(id_prefix)
                ):
                    r["done"] = True
                    self._save()
                    return True
        return False


# Module-level singleton
reminder_store = ReminderStore()
