# prompt_engine.py

import os

def load_system_prompt(prompt_path: str) -> str:
    """Load system prompt from .txt file."""
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read().strip()

def build_messages(system_prompt: str, headline: str, tags: str = None) -> list:
    """
    Build messages list for Groq API.
    Includes headline and optional tags.
    """
    if tags and tags.strip():
        user_content = f"Headline: {headline}\nTags: {tags}"
    else:
        user_content = f"Headline: {headline}"
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]