# sentiment_analysis.py
import re

def parse_llm_response(raw_output: str):
    """
    Parse LLM response expecting:
    Line 1: A number between -1 and 1
    Line 2: A brief explanation (reason)
    """
    if not raw_output:
        return "error", ""
    
    # Strip out any <think>...</think> reasoning blocks
    cleaned_output = re.sub(
        r"<think>.*?</think>",
        "",
        raw_output,
        flags=re.DOTALL
    ).strip()
    
    # Split into lines
    lines = [line.strip() for line in cleaned_output.splitlines() if line.strip()]
    
    if len(lines) < 2:
        print(f"❌ Unexpected Output: '{cleaned_output}'")
        return "error", ""
    
    # Line 1: Extract the numerical score
    score_line = lines[0]
    reason_line = lines[1]
    
    # Remove "Line 1:" prefix if present, then extract number
    score_text = re.sub(r'^line\s*\d+:\s*', '', score_line, flags=re.IGNORECASE)
    reason_text = re.sub(r'^line\s*\d+:\s*', '', reason_line, flags=re.IGNORECASE)
    
    # Extract the numerical score
    score_match = re.search(r'(-?\d+\.?\d*)', score_text)
    
    if score_match:
        try:
            score = float(score_match.group(1))
            # Validate range
            if -1.0 <= score <= 1.0:
                # Enforce max 100 characters on the reason
                if len(reason_text) > 100:
                    reason_text = reason_text[:97].rstrip() + "..."
                return score, reason_text
            else:
                print(f"❌ Score out of range [-1, 1]: {score}")
                return "error", ""
        except ValueError:
            print(f"❌ Could not parse score: '{score_line}'")
            return "error", ""
    else:
        print(f"❌ No valid score found in: '{score_line}'")
        return "error", ""