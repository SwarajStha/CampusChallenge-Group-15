# prompt_engine.py

import os

def load_system_prompt(prompt_path: str) -> str:
    """Load system prompt from .txt file."""
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read().strip()

def build_messages(system_prompt: str, headline: str, tags: str = None) -> list:
    """
    Build messages list for Groq API.
    Supports two formats:
    1. Single-message with placeholders (v7): Replaces {headline} and {tags}
    2. Two-message system/user (v6): Separate system and user messages
    """
    # Check if prompt has placeholders (v7 format)
    if '{headline}' in system_prompt:
        # Single-message format with placeholder replacement
        tags_str = tags if (tags and tags.strip()) else "None"
        user_content = system_prompt.replace('{headline}', headline).replace('{tags}', tags_str)
        
        return [
            {"role": "user", "content": user_content}
        ]
    else:
        # Two-message format (v6 and earlier)
        if tags and tags.strip():
            user_content = f"Headline: {headline}\nTags: {tags}"
        else:
            user_content = f"Headline: {headline}"
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]