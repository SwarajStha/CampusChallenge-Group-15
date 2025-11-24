# prompt_engine.py

import os

def load_system_prompt(prompt_path: str) -> str:
    """Load system prompt from .txt file."""
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read().strip()

def build_messages(system_prompt: str, headline: str) -> list:
    """
    Build messages list for Groq API.
    Only system + user (no ticker injection yet — add if needed later).
    """
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Headline: {headline}"}
    ]