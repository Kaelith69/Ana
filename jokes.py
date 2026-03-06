from __future__ import annotations

import asyncio
import random
import time
from typing import Optional

import requests

from config import JokeSettings

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

    def random_joke(self) -> Optional[str]:
        """Fetch a live dad joke from the API."""
        headers = {"Accept": "application/json", "User-Agent": "DadJokeDiscordBot/2.0"}
        try:
            res = requests.get(self.settings.api_url, headers=headers, timeout=self.settings.fetch_timeout)
            if res.status_code == 200:
                data = res.json()
                return data.get("joke") or None
        except requests.RequestException as err:
            print(f"Failed to fetch dad joke: {err}")
        return None

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

        # Update timestamps before fetch to prevent infinite loop API hammering on failure
        self.last_joke_time = now
        self.daily_joke_count += 1

        joke = await asyncio.to_thread(self.random_joke)
        if not joke:
            self.daily_joke_count -= 1  # refund daily quota
            return
        await channel.send(joke)
