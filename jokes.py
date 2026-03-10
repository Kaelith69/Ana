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
        if self.daily_joke_count >= self.settings.max_jokes_per_day:
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

        _JOKE_INTROS = [
            "okay wait i need to share this",
            "i've been holding onto this one",
            "don't judge me",
            "idk why this got me but",
            "ok bear with me",
            "not me laughing at a dad joke again",
            "u didn't hear this from me but",
            "context: i've been awake too long",
            "wait okay this is bad but it's funny",
            "i hate that i find this funny",
            "someone sent me this and now it's ur problem",
            "okay this is terrible and i love it",
            "ok i'm sorry in advance",
            "don't @ me",
        ]
        _JOKE_OUTROS = [
            "i know i know",
            "...okay i'm embarrassed",
            "don't judge me",
            "the delivery was what got me",
            "ok moving on",
            "anyway",
            "i regret nothing",
            "okay that was bad even for me",
            "💀",
            "i'm hilarious",
            "okay that was free",
            "u laughed. don't lie.",
            "ok well. that happened.",
            "no thoughts just that joke",
        ]

        use_intro = random.random() < 0.75
        use_outro = random.random() < 0.50

        if use_intro:
            async with channel.typing():
                await asyncio.sleep(random.uniform(0.6, 1.2))
            await channel.send(random.choice(_JOKE_INTROS))
            await asyncio.sleep(random.uniform(1.0, 2.0))

        async with channel.typing():
            await asyncio.sleep(random.uniform(1.2, 2.5))
        await channel.send(joke)

        if use_outro:
            await asyncio.sleep(random.uniform(1.5, 3.5))
            async with channel.typing():
                await asyncio.sleep(random.uniform(0.4, 0.9))
            await channel.send(random.choice(_JOKE_OUTROS))
