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
        self.last_joke_time = 0.0
        self.daily_joke_count = 0
        self.last_joke_day = self._current_day()
        self.max_jokes_per_day = 3

    def _current_day(self) -> int:
        # Returns the current day as an integer (days since epoch)
        return int(time.time() // 86400)

    # Removed file-based joke loading. All jokes are fetched live from API.

    # Removed file-based joke appending.

    def random_joke(self) -> Optional[str]:
        """Fetch a live dad joke from the API."""
        headers = {"Accept": "application/json", "User-Agent": "DadJokeDiscordBot/2.0"}
        try:
            res = requests.get(self.settings.api_url, headers=headers, timeout=self.settings.fetch_timeout)
            if res.status_code == 200:
                data = res.json()
                return data.get("joke", "")
        except requests.RequestException as err:
            print(f"Failed to fetch dad joke: {err}")
        return None

    def has_jokes(self) -> bool:
        # Always true since we fetch live jokes
        return True

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

    # Removed background joke fetching logic.

    # Removed batch joke fetching and periodic refresh logic.
