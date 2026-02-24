# Contributing to Ana 🤖

Hey, you actually want to contribute? That's genuinely exciting. Welcome to the chaos.

Ana is a small, opinionated Discord bot project. Contributing is straightforward — the codebase is ~250 lines of Python across 5 files. You can read the whole thing before lunch.

---

## Before You Start

- **Read the README** — understand what Ana actually does before adding stuff she doesn't need
- **Open an issue first** for big changes — don't spend a weekend building something only to find out it's already in progress
- **Small PRs > big PRs** — a 50-line PR that does one thing gets reviewed and merged way faster than a 500-line monster

---

## Setting Up

```bash
git clone https://github.com/Kaelith69/Ana.git
cd Ana
pip install -r requirements.txt
cp .env.example .env  # fill in your keys
python main.py        # confirm it starts without exploding
```

---

## Branching Model

We keep it simple:

| Branch | Purpose |
|---|---|
| `main` | Stable, deployed code. Don't push directly. |
| `feature/your-feature-name` | New features |
| `fix/what-youre-fixing` | Bug fixes |
| `chore/what-youre-doing` | Dependency updates, refactors, cleanup |

```bash
# Good branch names
git checkout -b feature/slash-commands
git checkout -b fix/groq-timeout-handling
git checkout -b chore/update-discord-py

# Less good branch names
git checkout -b mychanges
git checkout -b stuff
git checkout -b aaaaaa
```

---

## Commit Style

We loosely follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add slash command support
fix: handle groq rate limit error gracefully
chore: bump discord.py to latest
docs: update README with new trigger words
refactor: simplify normalize_response logic
```

Keep commit messages short but descriptive. "fix stuff" will be met with a polite but disapproving review comment.

---

## Code Style

- Python 3.10+ features are fine
- Type hints appreciated — see existing code for the pattern
- Keep functions small and focused
- If you're touching `nlp.py`, don't break the fallback chain
- If you're touching `config.py`, don't remove the env-not-found warnings
- Comments should explain *why*, not *what* — the code already says what

Run a quick sanity check before pushing:

```bash
python -m py_compile main.py nlp.py jokes.py config.py keepalive.py
```

---

## Pull Request Checklist

- [ ] Tested locally (bot starts, relevant functionality works)
- [ ] No API keys, tokens, or secrets in the code
- [ ] Description explains *what* and *why* (not just "fixed bug")
- [ ] Doesn't break the AI fallback chain
- [ ] Doesn't remove existing `.env` validation warnings

---

## What We're Looking For

Good contributions:
- Bug fixes with clear reproduction steps
- New trigger words or categories (submit in `config.py`)
- Performance improvements with benchmarks
- Better error handling
- Documentation improvements

Things that need a discussion first:
- Architectural changes to the NLP pipeline
- New external dependencies
- Changing the command prefix from `!`
- Anything that stores user data

---

## What We're Not Looking For

- Converting to a framework with 47 new dependencies
- "Rewriting in Rust" (we've heard it before)
- Replacing the dad jokes with motivational quotes
- AI replies that generate anything inappropriate

---

## Code of Conduct

Be a decent human. Constructive criticism is welcome. Personal attacks are not. The bot is designed to be lighthearted — keep contributions in that spirit.

---

Thanks for contributing. Ana appreciates it, even if she'll probably respond to your PR with a dad joke. 🥁
