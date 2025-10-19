
# Dad Joke Discord Bot (Groq Edition)

A Discord bot that drops random dad jokes, responds to trigger words, and uses Groq's Llama-4 model for dynamic, sentiment-matching replies. A lightweight Flask app responds on `/` to keep the process alive for hosting providers.

## Features
- Responds to trigger words (case-insensitive, e.g. `hello`, `bot`, `ai`, `nerd`) with replies that match the user's sentiment (positive, negative, neutral) using Groq's Llama-4 model.
- Replies adapt style: flirty/playful for positive, rude/blunt for negative, casual/nerdy for neutral.
- Randomly drops dad jokes with adjustable chance and cooldown.
- Loads jokes from `dad_jokes.txt`, fetches new ones from icanhazdadjoke.com, and appends fresh finds to disk.
- Hourly background refresh of the joke cache.
- Owner-only `!shutdown` command and public `!joke` command.
- Flask keep-alive endpoint for uptime monitors.

## Requirements
- Python 3.10 or newer.
- Discord bot token with the Message Content Intent enabled.
- Groq API key for Llama-4 completions.

Install dependencies once:

```powershell
pip install -r requirements.txt
```

> TextBlob relies on the `pattern` corpus for sentiment analysis. If you see errors about missing corpora, run `python -m textblob.download_corpora` after installing dependencies.


## Configuration
Create a `.env` file next to `main.py`:

```env
DISCORD_TOKEN=your_discord_bot_token
GROQ_API_KEY=your_groq_api_key_here
```

- `DISCORD_TOKEN` is required for Discord bot login.
- `GROQ_API_KEY` is required for Groq completions (Llama-4 model).
- `dad_jokes.txt` is optional. If the file is absent, the bot starts with a small built-in set and creates the file after the first successful fetch.


The joke refresher gracefully retries network timeouts, but if connectivity to `icanhazdadjoke.com` is unavailable for an extended period you may see warnings in the console. The bot continues operating with any cached jokes it already has.


Key tuning constants live in `config.py`:
- `JOKE_CHANCE` (default `0.15`) controls how often to drop jokes opportunistically.
- `JOKE_COOLDOWN` (default `60`) enforces a minimum delay between random jokes.
- `JOKE_FETCH_BATCH`, `JOKE_FETCH_INTERVAL`, and `JOKE_FETCH_TIMEOUT` customize how new jokes are pulled from the API.

## Running Locally
```powershell
# inside the project folder
pip install -r requirements.txt
python main.py
```

The console shows login confirmation, initial joke caching, and hourly refresh logs. Keep the process running while the bot is online.


## Discord Behavior
- **Auto replies**: Any message containing a trigger word runs sentiment analysis and sends a Groq-generated reply that matches the user's tone and style.
- **Random jokes**: After every message the bot evaluates the chance to respond with a dad joke, respecting the cooldown to avoid spam.
- **Commands**:
  - `!joke` — Reply immediately with a random joke from the cache.
  - `!shutdown` — Gracefully stop the bot; only the Discord user who owns the bot token can run this command.

## Deployment Notes
- The Flask server listens on port `8080` for GET `/` and returns `"Bot is alive!"`. Point uptime pings or platform health checks there.
- When hosting on services like Railway, Render, or Replit, ensure environment variables are configured and the process is allowed to bind to port `8080`.
- The bot uses the Discord message content intent; confirm it is toggled in the Discord Developer Portal and that the feature is approved for large servers.


## Troubleshooting
- **Missing Groq API key**: The bot starts but generated replies include an error note. Add `GROQ_API_KEY` to enable genuine completions.
- **Sentiment errors**: Install TextBlob corpora as noted above.
- **No random jokes**: Verify cooldown logs, network connectivity to icanhazdadjoke.com, and that the chance constant is high enough.
- **Connection drops**: Discord.py will log retries. Double-check your hosting provider keeps long-running processes alive or sends periodic requests to the Flask endpoint.

Have fun sprinkling puns across your Discord servers!
