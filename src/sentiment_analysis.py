# sentiment_analysis.py
import re

def parse_llm_response(raw_output: str):
    """
    Parses raw LLM output to extract (decision, reason).
    Mirrors your original logic.
    """
    # Remove <think>...</think> blocks
    cleaned = re.sub(r"<think>.*?</think>", "", raw_output, flags=re.DOTALL).strip()
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    
    decision = "error"
    reason = ""

    if lines:
        # Parse first line
        first_line = lines[0]
        m = re.search(r"\b(buy|hold|sell)\b\.?\s*(.*)", first_line, re.IGNORECASE | re.DOTALL)
        if m:
            decision = m.group(1).lower()
            inline_reason = m.group(2).strip()
        else:
            inline_reason = ""
        
        # Use second line if available, else inline reason
        reason = lines[1] if len(lines) >= 2 else inline_reason
        if len(reason) > 100:
            reason = "{}...".format(reason[:97].rstrip())

    return decision, reason