# Ana Wiki Home

This wiki mirrors implementation details from the current codebase.

## Navigation

| Page | Purpose |
|---|---|
| Architecture | Runtime flow, module interactions, async boundaries |
| Installation | Setup and environment configuration |
| Usage | Commands, trigger and behavior rules |
| API-Reference | Commands, endpoint, core callable surfaces |
| Developer-Guide | Local development and validation workflow |
| Privacy | Actual storage and external data flow |
| Troubleshooting | Known failure classes and checks |
| Roadmap | Planned and deferred work |

## Current implementation highlights

- Main entry point: main.py
- AI path: nlp.py with Groq -> Gemini -> static fallback
- Keepalive: Flask on port 8080
- Persistence: JSON profile files in data/profiles
- Environment loading: dotenv override enabled
