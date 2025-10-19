from __future__ import annotations

import asyncio
import random
import time
from typing import Iterable, List, Optional

import requests

from config import JokeSettings

_DEFAULT_JOKES = [
    "Why did the scarecrow win an award? Because he was outstanding in his field.",
    "Why don't skeletons fight each other? They don't have the guts.",
    "I'm reading a book about anti-gravity. It's impossible to put down.",
]


class DadJokeService:
    def __init__(self, settings: JokeSettings) -> None:
        self.settings = settings
        self.dad_jokes: List[str] = self._load_dad_jokes()
        self.known_jokes = set(self.dad_jokes)
        self.last_joke_time = 0.0
        self.daily_joke_count = 0
        self.last_joke_day = self._current_day()
        self.max_jokes_per_day = 3
        self.initial_fetch_started = False
        self.refresh_task: Optional[asyncio.Task[None]] = None

    def _current_day(self) -> int:
        # Returns the current day as an integer (days since epoch)
        return int(time.time() // 86400)

    def _load_dad_jokes(self) -> List[str]:
        try:
            with open(self.settings.jokes_file, "r", encoding="utf-8") as fh:
                jokes = [line.strip() for line in fh if line.strip()]
            if jokes:
                print(f"Loaded {len(jokes)} jokes from {self.settings.jokes_file}")
                return jokes
        except FileNotFoundError:
            print("No joke file found; using default set.")
        return _DEFAULT_JOKES.copy()

    def append_jokes_to_file(self, jokes: Iterable[str]) -> None:
        if not jokes:
            return
        try:
            with open(self.settings.jokes_file, "a", encoding="utf-8") as fh:
                for joke in jokes:
                    fh.write(f"{joke}\n")
        except OSError as err:
            print(f"Failed to write new jokes: {err}")

    def random_joke(self) -> Optional[str]:
        return random.choice(self.dad_jokes) if self.dad_jokes else None

    def has_jokes(self) -> bool:
        return bool(self.dad_jokes)

    async def maybe_send_joke(self, channel) -> None:
        now = time.monotonic()
        today = self._current_day()
        # Reset daily count if new day
        if today != self.last_joke_day:
            self.daily_joke_count = 0
            self.last_joke_day = today
        # Enforce daily joke limit
        if self.daily_joke_count >= self.max_jokes_per_day:
            return
        # Pseudo-random: only send if random chance and cooldown
        if now - self.last_joke_time < self.settings.cooldown:
            return
        # Use a random chance, but also randomize the cooldown a bit
        if random.random() >= self.settings.chance:
            return
        joke = self.random_joke()
        if not joke:
            return
        await channel.send(joke)
        self.last_joke_time = now
        self.daily_joke_count += 1

    def start_background_tasks(self) -> None:
        if not self.initial_fetch_started:
            self.initial_fetch_started = True
            asyncio.create_task(self._kickoff_initial_fetch())
        if self.refresh_task is None or self.refresh_task.done():
            self.refresh_task = asyncio.create_task(self._refresh_jokes_periodically())

    async def fetch_and_store_jokes(self, count: int) -> int:
        new_jokes = await asyncio.to_thread(self._fetch_jokes_batch, count)
        if not new_jokes:
            return 0
        unique = [j for j in new_jokes if j not in self.known_jokes]
        if not unique:
            return 0
        self.dad_jokes.extend(unique)
        self.known_jokes.update(unique)
        self.append_jokes_to_file(unique)
        return len(unique)

    def _fetch_jokes_batch(self, count: int) -> List[str]:
        headers = {"Accept": "application/json", "User-Agent": "DadJokeDiscordBot/2.0"}
        jokes: set[str] = set()
        attempts = 0
        max_attempts = max(count * 3, count + 5)
        while len(jokes) < count and attempts < max_attempts:
            attempts += 1
            try:
                res = requests.get(
                    self.settings.api_url,
                    headers=headers,
                    timeout=self.settings.fetch_timeout,
                )
                if res.status_code != 200:
                    continue
                data = res.json()
                joke = data.get("joke", "").strip()
                if joke:
                    jokes.add(joke)
            except requests.Timeout:
                print(
                    "Joke fetch timed out after"
                    f" {self.settings.fetch_timeout}s; retrying ({attempts}/{max_attempts})."
                )
                continue
            except requests.RequestException as err:
                print(f"Joke fetch error: {err}")
                break
        return list(jokes)

    async def _refresh_jokes_periodically(self) -> None:
        while True:
            await asyncio.sleep(self.settings.fetch_interval)
            try:
                added = await self.fetch_and_store_jokes(self.settings.fetch_batch)
                if added:
                    print(f"Fetched {added} new dad jokes.")
            except Exception as err:
                print(f"Joke refresh failed: {err}")

    async def _kickoff_initial_fetch(self) -> None:
        try:
            added = await self.fetch_and_store_jokes(self.settings.fetch_batch)
            if added:
                print(f"Primed with {added} fresh jokes.")
        except Exception as err:
            print(f"Initial joke fetch failed: {err}")
