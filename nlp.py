import requests
import json
import random
import re
from typing import Optional
from groq import Groq
from config import GEN1_API_KEY, GEN2_API_KEY, GROQ_API_KEY

# Models
GEN1_MODEL = "gemini-flash-lite-latest"
GEN2_MODEL = "gemini-2.5-flash-lite"

# Fallback responses
FALLBACK_RESPONSES = [
    "Not sure what to say to that.",
    "Interesting...",
    "Well, that's something.",
    "Cool story, bro."
]


def process_with_nlp(text: str) -> Optional[str]:
    """Unified entry point: try GROQ first, then GEN1, then GEN2.

    Returns a reply string (may be empty)."""
    clean_text = (text or "").strip()
    if not clean_text:
        return ""

    # Try GROQ primary
    try:
        reply = call_groq(clean_text)
        if reply:
            return reply
    except Exception as e:
        print(f"GROQ primary failed: {e}")

    # Fallback to GEN1 (backup)
    try:
        reply = call_gen1(clean_text)
        if reply:
            return reply
    except Exception as e:
        print(f"Gen1 backup failed: {e}")

    # Final fallback to GEN2 (backup2)
    try:
        reply = call_gen2(clean_text)
        if reply:
            return reply
    except Exception as e:
        print(f"Gen2 backup2 failed: {e}")

    # If everything fails, return a random fallback
    return random.choice(FALLBACK_RESPONSES)


def call_groq(input_text: str) -> Optional[str]:
    """Generate a response using Groq (primary)."""
    truncated = input_text[:1000]
    client = Groq(api_key=GROQ_API_KEY)
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": f"Respond concisely to the user input:\n{truncated}"}],
            temperature=1.0,
            max_completion_tokens=400,
            top_p=1,
            stream=False,
            stop=None,
        )
        content = completion.choices[0].message.content
        # Normalize content to plain text
        raw = None
        if content is None:
            raw = None
        elif isinstance(content, str):
            raw = content
        else:
            try:
                raw = json.dumps(content)
            except Exception:
                raw = str(content)
        reply = normalize_response(raw)
        print("\nGROQ Output:")
        print(reply)
        return reply
    except Exception as err:
        print(f"Groq request failed: {err}")
        return None


def call_gen1(input_text: str) -> Optional[str]:
    """Backup: Use Gen1 (Gemini Flash Lite) to generate a response.

    This replaces the previous mood-detection usage of Gen1 and now generates a reply.
    """
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEN1_MODEL}:streamGenerateContent"

    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': GEN1_API_KEY
    }

    data = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": f"Input: {input_text}\nRespond concisely in 1-2 lines."}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 1.2,
            "thinkingConfig": {"thinkingBudget": 0},
            "responseMimeType": "application/json"
        },
        "systemInstruction": {
            "parts": [
                {"text": "Provide a short, casual, friendly reply. Output only the reply text."}
            ]
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data, stream=True, timeout=30)
    except Exception as e:
        print(f"Gen1 request error: {e}")
        return None

    full_response = ""
    if response.status_code == 200:
        buffer = ""
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                buffer += line_text

        try:
            chunks = json.loads(buffer)
            for chunk in chunks:
                if 'candidates' in chunk and len(chunk['candidates']) > 0:
                    if 'content' in chunk['candidates'][0]:
                        parts = chunk['candidates'][0]['content'].get('parts', [])
                        for part in parts:
                            if 'text' in part:
                                full_response += part['text']
            print("\nGen1 Output:")
            print(full_response)
        except Exception as e:
            print(f"Error parsing Gen1 response: {e}")
            return None
    else:
        print(f"Gen1 Error: {response.status_code}")
        print(response.text)
        return None

    # Normalize the response to plain text
    normalized = normalize_response(full_response)
    if normalized:
        return normalized
    # fallback: remove surrounding braces/brackets and return cleaned
    cleaned = re.sub(r'^[\{\[]+|[\}\]]+$', '', full_response or '').strip()
    return cleaned or None


def call_gen2(input_text: str) -> Optional[str]:
    """Final fallback: Use Gen2 (Gemini 2.5) to generate a response."""
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEN2_MODEL}:streamGenerateContent"

    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': GEN2_API_KEY
    }

    data = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": f"Input: {input_text}\nRespond in a short, friendly tone (1-2 lines)."}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 1.35,
            "thinkingConfig": {"thinkingBudget": 0},
            "responseMimeType": "application/json"
        },
        "systemInstruction": {
            "parts": [
                {"text": "Short, casual chat-like replies. Output only the reply text, one or two lines max."}
            ]
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data, stream=True, timeout=30)
    except Exception as e:
        print(f"Gen2 request error: {e}")
        return None

    full_response = ""
    if response.status_code == 200:
        buffer = ""
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                buffer += line_text

        try:
            chunks = json.loads(buffer)
            for chunk in chunks:
                if 'candidates' in chunk and len(chunk['candidates']) > 0:
                    if 'content' in chunk['candidates'][0]:
                        parts = chunk['candidates'][0]['content'].get('parts', [])
                        for part in parts:
                            if 'text' in part:
                                full_response += part['text']
            print("\nGen2 Output:")
            print(full_response)
        except Exception as e:
            print(f"Error parsing Gen2 response: {e}")
            return None
    else:
        print(f"Gen2 Error: {response.status_code}")
        print(response.text)
        return None

    # Normalize the response to plain text
    normalized = normalize_response(full_response)
    if normalized:
        return normalized
    cleaned = re.sub(r'^[\{\[]+|[\}\]]+$', '', full_response or '').strip()
    return cleaned or None


def normalize_response(raw: Optional[str]) -> Optional[str]:
    """Turn model output into a plain human-like string.

    Handles cases where the model returns JSON like {"message": "..."} or nested structures.
    Returns None if there's no usable text.
    """
    if not raw:
        return None
    s = raw.strip()
    # If it looks like JSON, try parsing
    if s.startswith('{') or s.startswith('['):
        try:
            parsed = json.loads(s)
            # helper to find the first string inside nested structures
            def find_str(obj):
                if isinstance(obj, str):
                    return obj
                if isinstance(obj, dict):
                    for vv in obj.values():
                        r = find_str(vv)
                        if r:
                            return r
                if isinstance(obj, list):
                    for item in obj:
                        r = find_str(item)
                        if r:
                            return r
                return None

            # If it's a plain string
            if isinstance(parsed, str):
                return parsed.strip()
            # If dict, prefer common keys
            if isinstance(parsed, dict):
                for key in ('message', 'response', 'reply', 'text', 'content'):
                    v = parsed.get(key)
                    if isinstance(v, str) and v.strip():
                        return v.strip()
                # look deeper for first string
                r = find_str(parsed)
                if r:
                    return r.strip()
            # If list, find first string element
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, str) and item.strip():
                        return item.strip()
                    r = None
                    if isinstance(item, (dict, list)):
                        r = find_str(item)
                    if r:
                        return r.strip()
        except Exception:
            pass

    # Try regex for common patterns like "message": "..."
    m = re.search(r'"message"\s*:\s*"([^"]+)"', s)
    if m:
        return m.group(1).strip()
    m = re.search(r"[\'\"]message[\'\"]\s*:\s*[\'\"]([^\'\"]+)[\'\"]", s)
    if m:
        return m.group(1).strip()

    # Remove surrounding braces/brackets/quotes if any and return
    cleaned = s.strip(' \n\r\t\"\'')
    return cleaned if cleaned else None


if __name__ == "__main__":
    user_input = input("Enter your input: ")
    print(process_with_nlp(user_input))

