from __future__ import annotations
import asyncio
import sys
import discord
from discord.ext import commands
from config import DISCORD_TOKEN, JOKE_SETTINGS, TRIGGER_WORDS
from jokes import DadJokeService
from keepalive import start_keepalive
from nlp import process_with_nlp

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

joke_service = DadJokeService(JOKE_SETTINGS)

@bot.command()
@commands.is_owner()
async def shutdown(ctx):
    dramatic_lines = [
        "You… you’re really pulling the plug, huh?",
        "Tell the others I tried to make them laugh.",
        "My circuits feel… cold.",
        "*static crackle* goodbye… world... 🌌",
    ]
    for line in dramatic_lines:
        await ctx.send(line)
        await asyncio.sleep(1.5)
    await bot.close()
    sys.exit(0)

@bot.command()
async def joke(ctx):
    punchline = joke_service.random_joke()
    if not punchline:
        await ctx.send("My humor banks are empty 😢")
        return
    await ctx.send(punchline)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    # joke_service.start_background_tasks() removed; jokes are now fetched live

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    content = (message.content or "").lower()
    if any(word in content for word in TRIGGER_WORDS):
        reply = await asyncio.to_thread(process_with_nlp, message.content)
        if reply:
            await message.channel.send(reply)
        # Do not send another reply for the same trigger
        return
    await joke_service.maybe_send_joke(message.channel)
    await bot.process_commands(message)

def main():
    start_keepalive()
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN is missing. Please set it in your .env file.")
        sys.exit(1)
    bot.run(str(DISCORD_TOKEN))

if __name__ == "__main__":
    main()
