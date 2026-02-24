<div align="center">

<!-- HERO BANNER -->
<svg width="900" height="200" viewBox="0 0 900 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="heroBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#7C3AED;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#2563EB;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#06B6D4;stop-opacity:1" />
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <rect width="900" height="200" rx="16" fill="url(#heroBg)"/>
  <line x1="0" y1="50" x2="900" y2="50" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>
  <line x1="0" y1="100" x2="900" y2="100" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>
  <line x1="0" y1="150" x2="900" y2="150" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>
  <line x1="150" y1="0" x2="150" y2="200" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>
  <line x1="300" y1="0" x2="300" y2="200" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>
  <line x1="450" y1="0" x2="450" y2="200" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>
  <line x1="600" y1="0" x2="600" y2="200" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>
  <line x1="750" y1="0" x2="750" y2="200" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>
  <circle cx="450" cy="72" r="30" fill="rgba(255,255,255,0.15)" filter="url(#glow)"/>
  <text x="450" y="82" font-family="monospace" font-size="28" text-anchor="middle" fill="white">&#x1F916;</text>
  <text x="450" y="132" font-family="'Segoe UI', Arial, sans-serif" font-size="38" font-weight="bold" text-anchor="middle" fill="white" filter="url(#glow)">Ana</text>
  <text x="450" y="162" font-family="'Segoe UI', Arial, sans-serif" font-size="16" text-anchor="middle" fill="rgba(255,255,255,0.85)">Your Discord bot. Powered by AI. Armed with dad jokes. Dangerous.</text>
  <rect x="370" y="175" width="160" height="18" rx="9" fill="rgba(255,255,255,0.15)"/>
  <text x="450" y="188" font-family="monospace" font-size="11" text-anchor="middle" fill="rgba(255,255,255,0.9)">v2.0.0 &#xB7; Python &#xB7; discord.py</text>
</svg>

</div>

# Ana

---

## Badges

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-7C3AED?style=for-the-badge&logo=python&logoColor=white)
![discord.py](https://img.shields.io/badge/discord.py-Latest-2563EB?style=for-the-badge&logo=discord&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-Llama--4-06B6D4?style=for-the-badge&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-7C3AED?style=for-the-badge&logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-2563EB?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Alive%20(barely)-06B6D4?style=for-the-badge)

</div>

---

> **Ana** is a Discord bot that talks back, cracks jokes, and occasionally says something profound.
> Built at some ungodly hour with Python, three AI APIs, and the sheer willpower to not ship another "Hello World" bot.
> She's witty, she's wired up to Llama-4, and she will never, *ever* let a dad joke opportunity pass.

<div align="center">

![Humor](https://media.giphy.com/media/077i6AULCXc0FKTj9s/giphy.gif)

</div>

---

## &#x1F9E0; System Overview

Ana is a **Discord bot** that sits in your server and does three things:

1. **Detects trigger words** in messages (greetings, moods, slang, celebrations, multilingual phrases — 70+ keywords)
2. **Generates AI replies** via a triple-redundant AI pipeline: Groq (Llama-4) → Gemini Flash Lite Gen1 → Gemini Flash Lite Gen2 → snarky fallback
3. **Randomly drops dad jokes** into the chat (15% chance, 60s cooldown, max 3/day — because even chaos has limits)

She also runs a Flask HTTP server on port 8080 so uptime monitors can check she hasn't rage-quit.

---

## &#x2728; Features

| Feature | What it actually does |
|---|---|
| &#x1F916; **AI Replies** | Trigger-word detection → Groq Llama-4 generates a concise, casual reply |
| &#x1F504; **Fallback Chain** | Groq fails? → Gemini Gen1. That fails? → Gemini Gen2. That fails? → "Cool story, bro." |
| &#x1F602; **Dad Jokes** | Live-fetched from `icanhazdadjoke.com`. 15% chance per message, 60s cooldown, max 3/day |
| &#x1F3AF; **70+ Trigger Words** | Greetings, emotions, celebrations, slang, multilingual (Hindi, Spanish, French, Arabic) |
| &#x2699;&#xFE0F; **Fully Configurable** | Everything tunable via `.env` — joke chance, cooldown, timeouts, API keys |
| &#x1F310; **Keepalive Server** | Flask endpoint at `GET /` returns `Bot is alive!` for uptime monitoring |
| &#x1F6D1; **`!shutdown`** | Owner-only command. Dramatic farewell sequence included. No refunds. |
| &#x1F3A4; **`!joke`** | Force-fetch a dad joke on demand. For when you need to clear a room. |

---

## &#x1F4CA; Capability Visualization

<div align="center">

<svg width="700" height="320" viewBox="0 0 700 320" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="barGrad1" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#7C3AED"/>
      <stop offset="100%" style="stop-color:#06B6D4"/>
    </linearGradient>
    <linearGradient id="barGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#2563EB"/>
      <stop offset="100%" style="stop-color:#7C3AED"/>
    </linearGradient>
    <linearGradient id="barGrad3" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#06B6D4"/>
      <stop offset="100%" style="stop-color:#2563EB"/>
    </linearGradient>
  </defs>
  <rect width="700" height="320" rx="12" fill="#0F0F1A"/>
  <text x="350" y="32" font-family="'Segoe UI', Arial, sans-serif" font-size="16" font-weight="bold" text-anchor="middle" fill="#E2E8F0">Ana Capability Overview</text>
  <text x="20" y="72" font-family="monospace" font-size="12" fill="#94A3B8">AI Reply Speed</text>
  <text x="20" y="112" font-family="monospace" font-size="12" fill="#94A3B8">Trigger Coverage</text>
  <text x="20" y="152" font-family="monospace" font-size="12" fill="#94A3B8">Fallback Resilience</text>
  <text x="20" y="192" font-family="monospace" font-size="12" fill="#94A3B8">Joke Quality*</text>
  <text x="20" y="232" font-family="monospace" font-size="12" fill="#94A3B8">Chaos Factor</text>
  <text x="20" y="272" font-family="monospace" font-size="12" fill="#94A3B8">Config Flexibility</text>
  <rect x="190" y="56" width="390" height="22" rx="4" fill="#1E1E2E"/>
  <rect x="190" y="56" width="340" height="22" rx="4" fill="url(#barGrad1)"/>
  <text x="540" y="72" font-family="monospace" font-size="11" fill="#06B6D4">87%</text>
  <rect x="190" y="96" width="390" height="22" rx="4" fill="#1E1E2E"/>
  <rect x="190" y="96" width="370" height="22" rx="4" fill="url(#barGrad2)"/>
  <text x="570" y="112" font-family="monospace" font-size="11" fill="#7C3AED">95%</text>
  <rect x="190" y="136" width="390" height="22" rx="4" fill="#1E1E2E"/>
  <rect x="190" y="136" width="390" height="22" rx="4" fill="url(#barGrad1)"/>
  <text x="590" y="152" font-family="monospace" font-size="11" fill="#06B6D4">100%</text>
  <rect x="190" y="176" width="390" height="22" rx="4" fill="#1E1E2E"/>
  <rect x="190" y="176" width="290" height="22" rx="4" fill="url(#barGrad3)"/>
  <text x="490" y="192" font-family="monospace" font-size="11" fill="#2563EB">74%</text>
  <rect x="190" y="216" width="390" height="22" rx="4" fill="#1E1E2E"/>
  <rect x="190" y="216" width="360" height="22" rx="4" fill="url(#barGrad2)"/>
  <text x="560" y="232" font-family="monospace" font-size="11" fill="#7C3AED">92%</text>
  <rect x="190" y="256" width="390" height="22" rx="4" fill="#1E1E2E"/>
  <rect x="190" y="256" width="350" height="22" rx="4" fill="url(#barGrad1)"/>
  <text x="550" y="272" font-family="monospace" font-size="11" fill="#06B6D4">90%</text>
  <text x="350" y="305" font-family="monospace" font-size="10" text-anchor="middle" fill="#475569">* Joke Quality measured by groans per minute. Higher = better.</text>
</svg>

</div>

---

## &#x1F3D7;&#xFE0F; Architecture

<div align="center">

<svg width="700" height="420" viewBox="0 0 700 420" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#7C3AED"/>
    </marker>
    <marker id="arrowCyan" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#06B6D4"/>
    </marker>
    <marker id="arrowBlue" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#2563EB"/>
    </marker>
  </defs>
  <rect width="700" height="420" rx="12" fill="#0F0F1A"/>
  <text x="350" y="28" font-family="'Segoe UI', Arial, sans-serif" font-size="15" font-weight="bold" text-anchor="middle" fill="#E2E8F0">Ana Architecture</text>
  <rect x="270" y="45" width="160" height="44" rx="8" fill="#2563EB" opacity="0.9"/>
  <text x="350" y="63" font-family="monospace" font-size="12" font-weight="bold" text-anchor="middle" fill="white">Discord Server</text>
  <text x="350" y="80" font-family="monospace" font-size="10" text-anchor="middle" fill="rgba(255,255,255,0.8)">User Messages</text>
  <line x1="350" y1="89" x2="350" y2="118" stroke="#7C3AED" stroke-width="2" marker-end="url(#arrow)"/>
  <rect x="255" y="118" width="190" height="52" rx="8" fill="#7C3AED" opacity="0.9"/>
  <text x="350" y="138" font-family="monospace" font-size="12" font-weight="bold" text-anchor="middle" fill="white">main.py</text>
  <text x="350" y="154" font-family="monospace" font-size="9" text-anchor="middle" fill="rgba(255,255,255,0.8)">Event handling &#xB7; Commands</text>
  <text x="350" y="165" font-family="monospace" font-size="9" text-anchor="middle" fill="rgba(255,255,255,0.8)">on_message &#xB7; on_ready</text>
  <line x1="255" y1="144" x2="140" y2="200" stroke="#7C3AED" stroke-width="2" marker-end="url(#arrow)"/>
  <line x1="445" y1="144" x2="560" y2="200" stroke="#7C3AED" stroke-width="2" marker-end="url(#arrow)"/>
  <line x1="350" y1="170" x2="350" y2="330" stroke="#7C3AED" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#arrow)"/>
  <rect x="30" y="200" width="180" height="70" rx="8" fill="#1E1E2E" stroke="#7C3AED" stroke-width="1.5"/>
  <text x="120" y="222" font-family="monospace" font-size="12" font-weight="bold" text-anchor="middle" fill="#7C3AED">nlp.py</text>
  <text x="120" y="238" font-family="monospace" font-size="9" text-anchor="middle" fill="#94A3B8">AI Reply Pipeline</text>
  <text x="120" y="252" font-family="monospace" font-size="9" text-anchor="middle" fill="#94A3B8">Groq &#x2192; Gen1 &#x2192; Gen2</text>
  <text x="120" y="264" font-family="monospace" font-size="9" text-anchor="middle" fill="#94A3B8">&#x2192; static fallback</text>
  <rect x="490" y="200" width="180" height="70" rx="8" fill="#1E1E2E" stroke="#06B6D4" stroke-width="1.5"/>
  <text x="580" y="222" font-family="monospace" font-size="12" font-weight="bold" text-anchor="middle" fill="#06B6D4">jokes.py</text>
  <text x="580" y="238" font-family="monospace" font-size="9" text-anchor="middle" fill="#94A3B8">DadJokeService</text>
  <text x="580" y="252" font-family="monospace" font-size="9" text-anchor="middle" fill="#94A3B8">Live API fetch</text>
  <text x="580" y="264" font-family="monospace" font-size="9" text-anchor="middle" fill="#94A3B8">Cooldown &#xB7; Daily cap</text>
  <rect x="260" y="330" width="180" height="52" rx="8" fill="#1E1E2E" stroke="#2563EB" stroke-width="1.5"/>
  <text x="350" y="352" font-family="monospace" font-size="12" font-weight="bold" text-anchor="middle" fill="#2563EB">config.py</text>
  <text x="350" y="368" font-family="monospace" font-size="9" text-anchor="middle" fill="#94A3B8">API keys &#xB7; Settings &#xB7; TRIGGER_WORDS</text>
  <rect x="490" y="330" width="180" height="52" rx="8" fill="#1E1E2E" stroke="#06B6D4" stroke-width="1.5"/>
  <text x="580" y="352" font-family="monospace" font-size="12" font-weight="bold" text-anchor="middle" fill="#06B6D4">keepalive.py</text>
  <text x="580" y="368" font-family="monospace" font-size="9" text-anchor="middle" fill="#94A3B8">Flask &#xB7; Port 8080 &#xB7; GET /</text>
  <line x1="445" y1="170" x2="520" y2="330" stroke="#06B6D4" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#arrowCyan)"/>
  <rect x="30" y="310" width="180" height="90" rx="8" fill="#1E1E2E" stroke="#7C3AED" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="120" y="332" font-family="monospace" font-size="11" font-weight="bold" text-anchor="middle" fill="#7C3AED">External APIs</text>
  <text x="120" y="350" font-family="monospace" font-size="9" text-anchor="middle" fill="#94A3B8">Groq (Llama-4)</text>
  <text x="120" y="364" font-family="monospace" font-size="9" text-anchor="middle" fill="#94A3B8">Gemini Flash Lite (Gen1)</text>
  <text x="120" y="378" font-family="monospace" font-size="9" text-anchor="middle" fill="#94A3B8">Gemini 2.5 Flash Lite (Gen2)</text>
  <text x="120" y="392" font-family="monospace" font-size="9" text-anchor="middle" fill="#94A3B8">icanhazdadjoke.com</text>
  <line x1="120" y1="270" x2="120" y2="310" stroke="#7C3AED" stroke-width="1.5" marker-end="url(#arrow)"/>
  <line x1="240" y1="407" x2="270" y2="407" stroke="#7C3AED" stroke-width="2"/>
  <text x="275" y="411" font-family="monospace" font-size="9" fill="#94A3B8">data flow</text>
  <line x1="330" y1="407" x2="360" y2="407" stroke="#7C3AED" stroke-width="1.5" stroke-dasharray="4,3"/>
  <text x="365" y="411" font-family="monospace" font-size="9" fill="#94A3B8">init/config</text>
</svg>

</div>

---

## &#x1F30A; Data Flow

<div align="center">

<svg width="700" height="360" viewBox="0 0 700 360" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="dfArrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#06B6D4"/>
    </marker>
    <marker id="dfArrowPurple" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#7C3AED"/>
    </marker>
    <marker id="dfArrowBlue" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#2563EB"/>
    </marker>
  </defs>
  <rect width="700" height="360" rx="12" fill="#0F0F1A"/>
  <text x="350" y="28" font-family="'Segoe UI', Arial, sans-serif" font-size="15" font-weight="bold" text-anchor="middle" fill="#E2E8F0">Message Processing Flow</text>
  <rect x="20" y="55" width="120" height="44" rx="7" fill="#7C3AED"/>
  <text x="80" y="73" font-family="monospace" font-size="10" font-weight="bold" text-anchor="middle" fill="white">User Message</text>
  <text x="80" y="88" font-family="monospace" font-size="9" text-anchor="middle" fill="rgba(255,255,255,0.8)">Discord event</text>
  <line x1="140" y1="77" x2="168" y2="77" stroke="#06B6D4" stroke-width="2" marker-end="url(#dfArrow)"/>
  <rect x="168" y="55" width="130" height="44" rx="7" fill="#1E1E2E" stroke="#06B6D4" stroke-width="1.5"/>
  <text x="233" y="73" font-family="monospace" font-size="10" font-weight="bold" text-anchor="middle" fill="#06B6D4">Trigger Check</text>
  <text x="233" y="88" font-family="monospace" font-size="9" text-anchor="middle" fill="#94A3B8">70+ keywords scan</text>
  <polygon points="340,55 380,77 340,99 300,77" fill="#2563EB" opacity="0.9"/>
  <text x="340" y="74" font-family="monospace" font-size="9" font-weight="bold" text-anchor="middle" fill="white">Trigger</text>
  <text x="340" y="86" font-family="monospace" font-size="9" text-anchor="middle" fill="white">Match?</text>
  <line x1="268" y1="77" x2="300" y2="77" stroke="#06B6D4" stroke-width="2" marker-end="url(#dfArrow)"/>
  <line x1="380" y1="77" x2="440" y2="77" stroke="#06B6D4" stroke-width="2" marker-end="url(#dfArrow)"/>
  <text x="410" y="70" font-family="monospace" font-size="9" fill="#06B6D4">YES</text>
  <rect x="440" y="55" width="240" height="44" rx="7" fill="#1E1E2E" stroke="#7C3AED" stroke-width="1.5"/>
  <text x="560" y="73" font-family="monospace" font-size="10" font-weight="bold" text-anchor="middle" fill="#7C3AED">NLP Pipeline</text>
  <text x="560" y="88" font-family="monospace" font-size="9" text-anchor="middle" fill="#94A3B8">process_with_nlp(text)</text>
  <rect x="440" y="120" width="70" height="36" rx="5" fill="#7C3AED" opacity="0.85"/>
  <text x="475" y="135" font-family="monospace" font-size="9" font-weight="bold" text-anchor="middle" fill="white">Groq</text>
  <text x="475" y="149" font-family="monospace" font-size="8" text-anchor="middle" fill="rgba(255,255,255,0.8)">Llama-4</text>
  <rect x="525" y="120" width="70" height="36" rx="5" fill="#2563EB" opacity="0.85"/>
  <text x="560" y="135" font-family="monospace" font-size="9" font-weight="bold" text-anchor="middle" fill="white">Gemini</text>
  <text x="560" y="149" font-family="monospace" font-size="8" text-anchor="middle" fill="rgba(255,255,255,0.8)">Gen1 fallback</text>
  <rect x="610" y="120" width="70" height="36" rx="5" fill="#06B6D4" opacity="0.85"/>
  <text x="645" y="135" font-family="monospace" font-size="9" font-weight="bold" text-anchor="middle" fill="white">Gemini</text>
  <text x="645" y="149" font-family="monospace" font-size="8" text-anchor="middle" fill="rgba(255,255,255,0.8)">Gen2 fallback</text>
  <line x1="475" y1="99" x2="475" y2="120" stroke="#7C3AED" stroke-width="1.5" marker-end="url(#dfArrowPurple)"/>
  <line x1="560" y1="99" x2="560" y2="120" stroke="#2563EB" stroke-width="1.5" stroke-dasharray="3,2" marker-end="url(#dfArrowBlue)"/>
  <line x1="645" y1="99" x2="645" y2="120" stroke="#06B6D4" stroke-width="1.5" stroke-dasharray="3,2" marker-end="url(#dfArrow)"/>
  <line x1="510" y1="138" x2="525" y2="138" stroke="#94A3B8" stroke-width="1.5" stroke-dasharray="3,2" marker-end="url(#dfArrow)"/>
  <line x1="595" y1="138" x2="610" y2="138" stroke="#94A3B8" stroke-width="1.5" stroke-dasharray="3,2" marker-end="url(#dfArrow)"/>
  <rect x="440" y="185" width="240" height="30" rx="5" fill="#1E1E2E" stroke="#94A3B8" stroke-width="1" stroke-dasharray="3,2"/>
  <text x="560" y="204" font-family="monospace" font-size="9" text-anchor="middle" fill="#94A3B8">static fallback: "Cool story, bro."</text>
  <line x1="645" y1="156" x2="645" y2="185" stroke="#94A3B8" stroke-width="1" stroke-dasharray="3,2" marker-end="url(#dfArrow)"/>
  <line x1="340" y1="99" x2="340" y2="140" stroke="#2563EB" stroke-width="2" marker-end="url(#dfArrowBlue)"/>
  <text x="346" y="122" font-family="monospace" font-size="9" fill="#2563EB">NO</text>
  <rect x="255" y="140" width="170" height="44" rx="7" fill="#1E1E2E" stroke="#06B6D4" stroke-width="1.5"/>
  <text x="340" y="158" font-family="monospace" font-size="10" font-weight="bold" text-anchor="middle" fill="#06B6D4">maybe_send_joke()</text>
  <text x="340" y="172" font-family="monospace" font-size="9" text-anchor="middle" fill="#94A3B8">15% &#xB7; 60s cooldown &#xB7; max 3/day</text>
  <rect x="255" y="215" width="170" height="30" rx="5" fill="#1E1E2E" stroke="#06B6D4" stroke-width="1"/>
  <text x="340" y="234" font-family="monospace" font-size="9" text-anchor="middle" fill="#06B6D4">icanhazdadjoke.com API</text>
  <line x1="340" y1="184" x2="340" y2="215" stroke="#06B6D4" stroke-width="1.5" marker-end="url(#dfArrow)"/>
  <rect x="255" y="270" width="170" height="36" rx="7" fill="#7C3AED"/>
  <text x="340" y="289" font-family="monospace" font-size="10" font-weight="bold" text-anchor="middle" fill="white">Bot Sends Reply</text>
  <text x="340" y="302" font-family="monospace" font-size="9" text-anchor="middle" fill="rgba(255,255,255,0.8)">channel.send()</text>
  <line x1="340" y1="245" x2="340" y2="270" stroke="#06B6D4" stroke-width="1.5" marker-end="url(#dfArrow)"/>
  <line x1="560" y1="215" x2="420" y2="288" stroke="#7C3AED" stroke-width="1.5" stroke-dasharray="4,2" marker-end="url(#dfArrowPurple)"/>
  <line x1="20" y1="340" x2="50" y2="340" stroke="#06B6D4" stroke-width="2"/>
  <text x="55" y="344" font-family="monospace" font-size="9" fill="#94A3B8">primary path</text>
  <line x1="140" y1="340" x2="170" y2="340" stroke="#94A3B8" stroke-width="1.5" stroke-dasharray="3,2"/>
  <text x="175" y="344" font-family="monospace" font-size="9" fill="#94A3B8">fallback path</text>
  <line x1="270" y1="340" x2="300" y2="340" stroke="#7C3AED" stroke-width="1.5" stroke-dasharray="4,2"/>
  <text x="305" y="344" font-family="monospace" font-size="9" fill="#94A3B8">AI &#x2192; Discord</text>
</svg>

</div>

---

## &#x1F680; Installation

### Prerequisites

- Python 3.10+
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))
- Groq API key ([console.groq.com](https://console.groq.com))
- Google AI API key(s) for Gemini fallbacks ([aistudio.google.com](https://aistudio.google.com))

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/Kaelith69/Ana.git
cd Ana

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up your environment
cp .env.example .env   # or just create .env manually

# 4. Fill in your .env (see below)

# 5. Run Ana
python main.py
```

### `.env` Configuration

```env
# Required
DISCORD_TOKEN=your_discord_bot_token_here
GROQ_API_KEY=your_groq_api_key_here

# Optional (Gemini fallbacks)
GEN1_API_KEY=your_gemini_gen1_api_key_here
GEN2_API_KEY=your_gemini_gen2_api_key_here

# Optional tuning (defaults shown)
JOKE_CHANCE=0.15          # Probability of sending a joke (0.0 - 1.0)
JOKE_COOLDOWN=60          # Seconds between jokes
JOKE_FETCH_TIMEOUT=8      # HTTP timeout for joke API
JOKE_FETCH_BATCH=25       # Batch size (reserved for future use)
JOKE_FETCH_INTERVAL=3600  # Refresh interval (reserved for future use)
```

---

## &#x1F4D6; Usage

### Commands

| Command | Who | What |
|---|---|---|
| `!joke` | Everyone | Fetch and send a live dad joke immediately |
| `!shutdown` | Bot owner only | Trigger dramatic farewell sequence &#x2192; graceful shutdown |

### Trigger Words

Ana responds to messages containing any of these keywords (case-insensitive):

```
ana, hello, hi, hey, yo, sup
morning, gm, gn, goodmorning, goodnight, afternoon, evening
namaste, hola, bonjour
happy, sad, tired, angry, bored, excited
lmao, omg, wow, bruh
birthday, hbd, congrats, congratulations
wedding, engagement, diwali, christmas, eid, newyear, valentines
bye, goodbye, cya, later
... and more
```

### How AI Replies Work

1. Message contains a trigger word &#x2192; `on_message` fires
2. `asyncio.to_thread(process_with_nlp, message.content)` runs the AI pipeline off the event loop
3. **Groq Llama-4** gets first crack (fast, smart, snarky)
4. If Groq fails &#x2192; **Gemini Flash Lite Gen1** takes over
5. If that fails &#x2192; **Gemini 2.5 Flash Lite Gen2** takes over
6. If everything is on fire &#x2192; "Cool story, bro."

---

## &#x1F4C1; Project Structure

```
Ana/
&#x251C;&#x2500;&#x2500; main.py          # Discord bot entry point, event handlers, commands
&#x251C;&#x2500;&#x2500; nlp.py           # AI reply pipeline (Groq + dual Gemini fallbacks)
&#x251C;&#x2500;&#x2500; jokes.py         # DadJokeService: live fetching, cooldown, daily cap
&#x251C;&#x2500;&#x2500; config.py        # Config loader: API keys, settings, trigger words
&#x251C;&#x2500;&#x2500; keepalive.py     # Flask HTTP server for uptime monitoring
&#x251C;&#x2500;&#x2500; requirements.txt # Python dependencies (5 packages)
&#x251C;&#x2500;&#x2500; .env             # Your secrets (NOT committed, don't even try)
&#x251C;&#x2500;&#x2500; .gitignore       # Properly ignores .env, __pycache__, etc.
&#x2514;&#x2500;&#x2500; LICENSE          # MIT License
```

---

## &#x1F4C8; Performance Stats

<div align="center">

<svg width="700" height="220" viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg">
  <rect width="700" height="220" rx="12" fill="#0F0F1A"/>
  <text x="350" y="28" font-family="'Segoe UI', Arial, sans-serif" font-size="15" font-weight="bold" text-anchor="middle" fill="#E2E8F0">Runtime Stats</text>
  <rect x="20" y="45" width="145" height="80" rx="8" fill="#1E1E2E" stroke="#7C3AED" stroke-width="1.5"/>
  <text x="92" y="75" font-family="monospace" font-size="22" font-weight="bold" text-anchor="middle" fill="#7C3AED">~400ms</text>
  <text x="92" y="97" font-family="monospace" font-size="10" text-anchor="middle" fill="#94A3B8">Avg Groq reply time</text>
  <text x="92" y="114" font-family="monospace" font-size="9" text-anchor="middle" fill="#475569">(varies by load)</text>
  <rect x="183" y="45" width="145" height="80" rx="8" fill="#1E1E2E" stroke="#2563EB" stroke-width="1.5"/>
  <text x="255" y="75" font-family="monospace" font-size="22" font-weight="bold" text-anchor="middle" fill="#2563EB">3</text>
  <text x="255" y="97" font-family="monospace" font-size="10" text-anchor="middle" fill="#94A3B8">AI fallback layers</text>
  <text x="255" y="114" font-family="monospace" font-size="9" text-anchor="middle" fill="#475569">Groq &#x2192; Gen1 &#x2192; Gen2</text>
  <rect x="346" y="45" width="145" height="80" rx="8" fill="#1E1E2E" stroke="#06B6D4" stroke-width="1.5"/>
  <text x="418" y="75" font-family="monospace" font-size="22" font-weight="bold" text-anchor="middle" fill="#06B6D4">70+</text>
  <text x="418" y="97" font-family="monospace" font-size="10" text-anchor="middle" fill="#94A3B8">Trigger keywords</text>
  <text x="418" y="114" font-family="monospace" font-size="9" text-anchor="middle" fill="#475569">Multilingual support</text>
  <rect x="509" y="45" width="171" height="80" rx="8" fill="#1E1E2E" stroke="#7C3AED" stroke-width="1.5"/>
  <text x="594" y="75" font-family="monospace" font-size="22" font-weight="bold" text-anchor="middle" fill="#7C3AED">3/day</text>
  <text x="594" y="97" font-family="monospace" font-size="10" text-anchor="middle" fill="#94A3B8">Max jokes per day</text>
  <text x="594" y="114" font-family="monospace" font-size="9" text-anchor="middle" fill="#475569">Your server's dignity: preserved</text>
  <rect x="20" y="148" width="660" height="52" rx="8" fill="#1E1E2E" stroke="#2563EB" stroke-width="1"/>
  <text x="40" y="170" font-family="monospace" font-size="11" fill="#94A3B8">&#x26A1; Single Groq client instance  &#xB7;  async/await throughout  &#xB7;  asyncio.to_thread() for blocking AI calls</text>
  <text x="40" y="190" font-family="monospace" font-size="11" fill="#94A3B8">&#x1F310; Flask keepalive on port 8080  &#xB7;  Stateless across restarts  &#xB7;  Cloud-hosted (Railway/Render/Replit)</text>
</svg>

</div>

---

## &#x1F512; Privacy

Ana processes messages **only when triggered** — she's not silently reading everything (unlike that one friend who screenshots all your texts). Here's the deal:

- &#x2705; Messages are only processed when they contain a **trigger word**
- &#x2705; No messages are stored, logged, or persisted to disk
- &#x2705; API calls to Groq/Gemini include only the triggering message content, truncated to 1000 characters
- &#x2705; `.env` is gitignored — your API keys never leave your machine
- &#x2757; Groq and Google handle their respective API traffic under their own privacy policies

---

## &#x1F5FA;&#xFE0F; Future Roadmap

Things that would be cool to add, ranked by "would probably make the bot less embarrassing":

- [ ] **Per-server personality config** — Let server admins set Ana's vibe
- [ ] **Slash commands** — `/joke`, `/ask`, etc. (the future is typed, not prefixed)
- [ ] **Memory/context** — Multi-turn conversations so Ana doesn't forget what she just said
- [ ] **More trigger categories** — Weather, sports, coding questions
- [ ] **Rate limiting per user** — Prevent one person from interrogating Ana all day
- [ ] **Logging dashboard** — See what Ana's been up to (with privacy controls)
- [ ] **Custom trigger words per server** — Admins add their own keywords
- [ ] **Async joke fetching** — Pre-fetch jokes in background so `!joke` is instant

---

## &#x1F4C4; License

MIT &#xA9; 2025 [Kaelith69](https://github.com/Kaelith69)

Go nuts. Just don't blame us when your Discord server becomes 40% dad jokes.

---

<div align="center">

*Made with &#x2615;, questionable sleep habits, and an irrational love for fallback chains.*

</div>
