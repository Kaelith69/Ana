"""Reminder system for Ana.

Users set reminders with: !remindme <natural language>
Groq parses the input into structured JSON and stores it in data/reminders/reminders.json.
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
import uuid
from typing import Optional

from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL_WATERFALL

_REMINDERS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "reminders")
_REMINDERS_FILE = os.path.join(_REMINDERS_DIR, "reminders.json")
_LOCK = threading.Lock()
_IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
_ALLOWED_OCCASION_TYPES = {"birthday", "anniversary", "wedding", "exam", "meeting", "custom"}

_groq_client: Groq | None = Groq(api_key=GROQ_API_KEY, timeout=25.0) if GROQ_API_KEY else None


# ---------------------------------------------------------------------------
# Groq helper
# ---------------------------------------------------------------------------

def _groq_complete(system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> Optional[str]:
    """Single reusable Groq completion for reminder parsing and wish generation."""
    if _groq_client is None:
        return None
    try:
        completion = _groq_client.chat.completions.create(
            model=GROQ_MODEL_WATERFALL[0],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_completion_tokens=max_tokens,
            temperature=temperature,
            top_p=0.95,
            stream=False,
        )
        if not completion.choices:
            return None
        return (completion.choices[0].message.content or "").strip() or None
    except Exception as e:
        import sys
        print(f"[reminders] Groq error: {e}", file=sys.stderr)
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
) -> Optional[dict]:
    """Call Groq to parse a free-form reminder request into a structured dict.

    Returns a complete reminder record ready to be stored, or None if parsing fails.
    """
    if _groq_client is None or not raw_text.strip():
        return None

    now_str = datetime.datetime.now(_IST).strftime("%Y-%m-%d %H:%M IST (%A)")
    user_prompt = _parse_prompt(now_str) + raw_text.strip()[:600]

    raw = _groq_complete(
        "You are a reminder parser. Output only valid JSON as instructed. No markdown, no explanation.",
        user_prompt,
        temperature=0.1,
        max_tokens=1024,
    )
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


def generate_wish(reminder: dict) -> Optional[str]:
    """Generate an Ana-style wish/reminder message using Groq."""
    if _groq_client is None:
        return None

    detail = (
        f"person's name: {reminder.get('user_name', 'someone')}\n"
        f"occasion: {reminder.get('occasion', 'reminder')}\n"
        f"occasion type: {reminder.get('occasion_type', 'custom')}\n"
    )
    if reminder.get("notes"):
        detail += f"extra details: {reminder['notes']}\n"

    user_prompt = (
        detail
        + "\nbefore writing, consider silently: what specific tone fits this occasion type "
        "and this person's name? is it warm, teasing, practical, or quiet?\n"
        "then output ONLY the final message — nothing else."
    )

    return _groq_complete(
        _WISH_SYSTEM,
        user_prompt,
        temperature=1.1,
        max_tokens=512,
    )


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

class ReminderStore:
    """Thread-safe persistent reminder store backed by a single JSON array file."""

    def __init__(self) -> None:
        self._reminders: list[dict] = []
        self._loaded: bool = False
        self._dt_cache: dict[str, datetime.datetime] = {}

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
                self._dt_cache.clear()
        except Exception:
            self._reminders = []
            self._dt_cache.clear()

    def _dt_for(self, reminder: dict) -> Optional[datetime.datetime]:
        """Return timezone-aware IST datetime for a reminder using a small parse cache."""
        rid = str(reminder.get("id", ""))
        if rid:
            cached = self._dt_cache.get(rid)
            if cached is not None:
                return cached
        try:
            dt = datetime.datetime.fromisoformat(reminder["datetime_ist"]).replace(tzinfo=_IST)
        except Exception:
            return None
        if rid:
            self._dt_cache[rid] = dt
        return dt

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
            self._dt_for(reminder)
            self._save()

    def get_due(self, now_ist: datetime.datetime) -> list[dict]:
        """Return copies of all pending reminders whose datetime_ist <= now_ist."""
        with _LOCK:
            self._load()
            due = []
            for r in self._reminders:
                if r.get("done"):
                    continue
                dt = self._dt_for(r)
                if dt is not None and dt <= now_ist:
                    due.append(dict(r))
            return due

    def mark_done(self, reminder_id: str) -> None:
        with _LOCK:
            self._load()
            changed = False
            for r in self._reminders:
                if r.get("id") == reminder_id:
                    if not r.get("done"):
                        r["done"] = True
                        changed = True
                    break
            if changed:
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
