# api_client.py

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def call_groq(messages: list, model: str = "qwen/qwen3-32b") -> str:
    """
    Low-level function to call Groq API and return raw text.
    """
    response = _client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=0.0,
        max_tokens=50
    )
    return (response.choices[0].message.content or "").strip()