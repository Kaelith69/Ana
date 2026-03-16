# Usage

## Commands

- !joke: fetch and send a live dad joke.
- !shutdown: owner-only graceful shutdown.

## Trigger behavior

A message triggers Ana when one of these is true:

- Message mentions the bot.
- Message matches a trigger word.
- Message matches a roast word.
- Message matches a flirt word.

Mode precedence:

- Roast overrides flirt if both patterns match.

## Cooldowns and behavior simulation

- User cooldown: 25 seconds.
- Channel cooldown: 7 seconds.
- Low-signal skip: 5 percent.
- Ghost typing with no message: 6 percent.
- Reaction overlay on top of text reply: 10 percent.
- Typo injection: 4 percent.

Roast mode bypasses cooldown gating.

## Follow-ups

- Roast follow-up: 25 percent.
- Flirt follow-up: 20 percent.
- Normal follow-up: 8 percent.

## Notes

- Emoji-only reply branch is not present.
- History stores up to 20 recent entries per channel.
- Mention tokens are resolved to display names before model calls.
