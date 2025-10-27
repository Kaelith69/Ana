

# Ana: Dad Joke & Sentiment Discord Bot

Ana is a Discord bot that delivers dad jokes, responds to trigger words, and adapts its replies to match the user's mood using advanced NLP models (Groq Llama-4 and Gemini). It also includes a Flask keepalive endpoint for reliable hosting.

---

## Features

- **Sentiment-Adaptive Replies:**
  - Detects user mood (Calm, Happy, Empathetic, Flirty, Rude, Sarcastic, Passionate, Moody) using Gemini.
  - Replies with Groq Llama-4 for moods like Rude, Sarcastic, Flirty; otherwise uses Gemini for friendly, supportive, or casual responses.
- **Dad Jokes:**
  - Randomly drops dad jokes from a local cache or fetches new ones from [icanhazdadjoke.com](https://icanhazdadjoke.com/).
  - Adjustable joke chance and cooldown to prevent spam.
  - Owner-only `!shutdown` and public `!joke` commands.
- **Trigger Word Detection:**
  - Responds to messages containing trigger words (e.g., `hello`, `bot`, `ai`, `nerd`).
- **Keepalive Endpoint:**
  - Flask app responds on `/` for uptime monitoring and hosting platforms.
- **Configurable:**
  - All key settings (joke chance, cooldown, fetch batch/interval) are in `config.py`.

---

## Setup & Installation

### Requirements

- Python 3.10+
- Discord bot token (with Message Content Intent enabled)
- Groq API key (for Llama-4 completions)
- Gemini API key (for mood detection and friendly completions)

### Install Dependencies

```powershell
pip install -r requirements.txt
```

TextBlob requires the `pattern` corpus for sentiment analysis. If you see errors about missing corpora, run:

```powershell
python -m textblob.download_corpora
```

### Configuration

Create a `.env` file in the project root:

```env
DISCORD_TOKEN=your_discord_bot_token
GROQ_API_KEY=your_groq_api_key_here
GEN2_API_KEY=your_gemini_api_key_here
```

- `DISCORD_TOKEN`: Discord bot login
- `GROQ_API_KEY`: Groq completions (Llama-4)
- `GEN2_API_KEY`: Gemini completions
- `dad_jokes.txt`: Optional. If missing, bot starts with built-in jokes and creates the file after first fetch.

IMPORTANT: Do NOT commit your `.env` file to the repository. It often contains secrets (bot tokens, API keys). This project already includes `.env` in `.gitignore`, but if you accidentally have a tracked `.env` file you should remove it from the git index (see steps below).

To avoid committing secrets, set the environment variable instead of storing it in the repo. Example PowerShell commands:

```powershell
# Temporary for current session
$env:DISCORD_TOKEN = '<PASTE_YOUR_TOKEN_HERE>'

# Persist for current Windows user (restart terminals/IDE to pick up)
[Environment]::SetEnvironmentVariable('DISCORD_TOKEN','<PASTE_YOUR_TOKEN_HERE>','User')
```

If you already committed a `.env` with secrets, remove it from the repo history or at least from the index with:

```powershell
git rm --cached .env
git commit -m "Remove .env from repository"
git push origin main
```


---

## Usage

### Running Locally

```powershell
python main.py
```

Console output shows login, joke caching, and refresh logs. Keep the process running for the bot to stay online.

### Discord Commands & Behavior

- **Auto replies:**
  - Any message with a trigger word runs sentiment analysis and sends a reply matching the user's mood and style.
- **Random jokes:**
  - After every message, the bot may respond with a dad joke (based on chance and cooldown).
- **Commands:**
  - `!joke`: Reply with a random joke from the cache.
  - `!shutdown`: Gracefully stop the bot (owner only).

---

## Code Structure

- `main.py`: Discord bot logic, command handling, and message routing.
- `nlp.py`: Sentiment analysis, mood detection, and reply generation using Groq and Gemini APIs.
- `jokes.py`: Dad joke management, caching, and API fetching.
- `config.py`: All configuration constants and environment variable loading.
- `keepalive.py`: Flask server for keepalive endpoint.
- `dad_jokes.txt`: Local cache of jokes (auto-populated).
- `requirements.txt`: Python dependencies.

---

## Advanced Configuration

Tune these in `config.py`:

- `JOKE_CHANCE`: Probability of dropping a joke (default: 0.15)
- `JOKE_COOLDOWN`: Minimum seconds between jokes (default: 60)
- `JOKE_FETCH_BATCH`, `JOKE_FETCH_INTERVAL`, `JOKE_FETCH_TIMEOUT`: Control joke fetching from API

---

## Deployment

- Flask server listens on port `8080` for GET `/` and returns `"Bot is alive!"` for uptime checks.
- On Railway, Render, Replit, etc., set environment variables and allow binding to port `8080`.
- Discord message content intent must be enabled in the Developer Portal (required for trigger word detection).

---

## Troubleshooting

- **Groq API key missing:** Bot starts but replies include error notes. Add `GROQ_API_KEY`.
- **TextBlob errors:** Run `python -m textblob.download_corpora`.
- **No jokes:** Check cooldown logs, network connectivity, and chance constant.
- **Connection drops:** Discord.py will retry. Ensure your host supports long-running processes and pings the Flask endpoint.

---

## Example Dad Jokes

See `dad_jokes.txt` for hundreds of jokes. Example:

> Why did the scarecrow win an award? Because he was outstanding in his field.
> Why don't skeletons fight each other? They don't have the guts.
> I'm reading a book about anti-gravity. It's impossible to put down.

---

## License

MIT License. See LICENSE file if present.

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
