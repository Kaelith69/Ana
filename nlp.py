def process_with_nlp(text: str) -> str:
    """Unified NLP entry point for Discord bot."""
    mood = call_gen1(text)
    if not mood:
        return "Failed to detect mood."
    if mood in ["Rude", "Sarcastic", "Flirty"]:
        return process_with_gq(text, mood)
    else:
        return call_gen2(text, mood)
import requests
import json
import random
from textblob import TextBlob
from groq import Groq

# API Keys and Models
GEN1_API_KEY = "AIzaSyBC2C8BYmpMmIph43LOeOmsJ9yQQNu9L88"
GEN1_MODEL = "gemini-flash-lite-latest"
GEN2_API_KEY = "AIzaSyBV1Ho3XpPkoiSXCeJAdZ1lIB3lRiphWn4"
GEN2_MODEL = "gemini-2.5-flash-lite"
GROQ_API_KEY = "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"

# Fallback responses for GQ
FALLBACK_HF_RESPONSES = [
    "Not sure what to say to that.",
    "Interesting...",
    "Well, that's something.",
    "Cool story, bro."
]

def call_gen1(input_text):
    """Gen1: Mood detection using Gemini Flash Lite"""
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
                    {"text": input_text}
                ]
            }
        ],
        "generationConfig": {
            "thinkingConfig": {"thinkingBudget": 0},
            "responseMimeType": "application/json"
        },
        "systemInstruction": {
            "parts": [
                {"text": "check and analyze the input and return which mood from the below set it matches, only choose a single one [\"Calm\", \"Happy\", \"Empathetic\", \"Flirty\", \"Rude\", \"Sarcastic\", \"Passionate\", \"Moody\"]"}
            ]
        }
    }
    
    response = requests.post(API_URL, headers=headers, json=data, stream=True)
    mood = None
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
                                text = part['text']
                                full_response += text
            
            print("Gen1 (Mood Detection) Output:")
            print(full_response)
            
            # Extract mood from JSON response
            try:
                mood_json = json.loads(full_response)
                mood = mood_json.get("mood")
            except:
                # Fallback: search for mood keywords in response
                for m in ["Calm", "Happy", "Empathetic", "Flirty", "Rude", "Sarcastic", "Passionate", "Moody"]:
                    if m.lower() in full_response.lower():
                        mood = m
                        break
        except Exception as e:
            print(f"Error parsing Gen1 response: {e}")
    else:
        print(f"Gen1 Error: {response.status_code}")
        print(response.text)
    
    return mood

def process_with_gq(text, mood):
    """GQ: Process with Groq using TextBlob sentiment analysis"""
    clean_text = (text or "").strip()
    if not clean_text:
        return ""
    
    
    truncated = clean_text[:200]
    client = Groq(api_key=GROQ_API_KEY)
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "user", "content": f"Input: {truncated}\nthe mood you should respond in Mood: {mood}"},
            ],
            temperature=1,
            max_completion_tokens=1141,
            top_p=1,
            stream=False,
            stop=None
        )
        content = completion.choices[0].message.content
        reply = content.strip() if content is not None else random.choice(FALLBACK_HF_RESPONSES)
    except Exception as err:
        print(f"Groq request failed: {err}")
        return random.choice(FALLBACK_HF_RESPONSES)
    print("\nGQ Output:")
    print(reply)
    return reply

def call_gen2(input_text, mood):
    """Gen2: Response generation using Gemini 2.5 Flash Lite"""
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
                    {"text": f"Input: {input_text}\n the mood you should respond in Mood: {mood}"}
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
                {"text": "happy, energetic , encourages , empathetic, emotional support, funny , short response one liners ,casual chat like a confident woman"}
            ]
        }
    }
    
    response = requests.post(API_URL, headers=headers, json=data, stream=True)
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
                                text = part['text']
                                full_response += text
            
            print("\nGen2 Output:")
            print(full_response)
        except Exception as e:
            print(f"Error parsing Gen2 response: {e}")
    else:
        print(f"Gen2 Error: {response.status_code}")
        print(response.text)
    
    # Ensure output is plain text, not JSON object
    try:
        # If the response is a JSON string with a 'response' key, extract it
        parsed = json.loads(full_response)
        if isinstance(parsed, dict) and 'response' in parsed:
            return parsed['response']
    except Exception:
        pass
    return full_response

def main():
    user_input = input("Enter your input: ")
    
    # Step 1: Detect mood with Gen1
    mood = call_gen1(user_input)
    
    if not mood:
        print("Failed to detect mood. Exiting.")
        return
    
    print(f"\nDetected Mood: {mood}")
    
    # Step 2: Route to GQ or Gen2 based on mood
    if mood in ["Rude", "Sarcastic", "Flirty"]:
        print("\n→ Routing to GQ (Groq)")
        process_with_gq(user_input, mood)
    else:
        print("\n→ Routing to Gen2 (Gemini)")
        call_gen2(user_input, mood)

if __name__ == "__main__":
    main()
