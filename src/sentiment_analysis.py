# sentiment_analysis.py
import re

def parse_llm_response(raw_output: str):
    """
    Parse LLM response supporting two formats:
    
    Format 1 (Persona-based with calculation):
      NOVICE: X.XX | Reason
      FANATIC: X.XX | Reason
      DAY/SWING: X.XX | Reason
      LONG-TERM: X.XX | Reason
      REGIME: [MEME|NORMAL]
      CALCULATION: ...
      FINAL_WEIGHTED: Y.YY
      Line 1: Y.YY
      Line 2: Overall reason
    
    Format 2 (Simple):
      Line 1: Y.YY
      Line 2: Reason
    
    Returns:
        tuple: (score, reason) where score is a float or "error"
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
    
    # Try Format 1 first (Persona-based)
    novice_match = re.search(r'NOVICE:\s*(-?\d+\.?\d*)', cleaned_output, flags=re.IGNORECASE)
    fanatic_match = re.search(r'FANATIC:\s*(-?\d+\.?\d*)', cleaned_output, flags=re.IGNORECASE)
    dayswing_match = re.search(r'DAY/SWING:\s*(-?\d+\.?\d*)', cleaned_output, flags=re.IGNORECASE)
    longterm_match = re.search(r'LONG-TERM:\s*(-?\d+\.?\d*)', cleaned_output, flags=re.IGNORECASE)
    regime_match = re.search(r'REGIME:\s*(MEME|NORMAL)', cleaned_output, flags=re.IGNORECASE)
    
    # If we found persona data, use Format 1
    if all([novice_match, fanatic_match, dayswing_match, longterm_match, regime_match]):
        return parse_persona_format(cleaned_output, novice_match, fanatic_match, 
                                    dayswing_match, longterm_match, regime_match)
    
    # Otherwise try Format 2 (Simple)
    return parse_simple_format(cleaned_output)


def parse_persona_format(cleaned_output, novice_match, fanatic_match, 
                         dayswing_match, longterm_match, regime_match):
    """Parse the persona-based format and calculate weighted score."""
    # Extract final reason from Line 2
    line2_match = re.search(r'line\s*2:\s*(.+?)(?:\n|$)', cleaned_output, flags=re.IGNORECASE | re.DOTALL)
    
    if not line2_match:
        print(f"❌ Missing Line 2 in persona format")
        return "error", ""
    
    try:
        # Parse persona scores
        novice = float(novice_match.group(1))
        fanatic = float(fanatic_match.group(1))
        dayswing = float(dayswing_match.group(1))
        longterm = float(longterm_match.group(1))
        regime = regime_match.group(1).upper()
        reason = line2_match.group(1).strip()
        
        # Calculate weighted score in Python (accurate math!)
        if regime == "MEME":
            # MEME weights: Novice=40%, Fanatic=20%, Day/Swing=30%, Long=10%
            final_score = (0.40 * novice) + (0.20 * fanatic) + (0.30 * dayswing) + (0.10 * longterm)
        else:  # NORMAL
            # NORMAL weights: Novice=20%, Fanatic=10%, Day/Swing=30%, Long=40%
            final_score = (0.20 * novice) + (0.10 * fanatic) + (0.30 * dayswing) + (0.40 * longterm)
        
        # Round to 2 decimal places
        final_score = round(final_score, 2)
        
        # Validate range
        if -1.0 <= final_score <= 1.0:
            # Enforce max 100 characters on the reason
            if len(reason) > 100:
                reason = reason[:97].rstrip() + "..."            
            # print(f"   📊 Calculated Score: {final_score} (Regime: {regime})")
            # print(f"      Novice: {novice}, Fanatic: {fanatic}, Day/Swing: {dayswing}, Long: {longterm}")            
            return final_score, reason
        else:
            print(f"❌ Calculated score out of range [-1, 1]: {final_score}")
            return "error", ""
            
    except ValueError as e:
        print(f"❌ Could not parse persona scores: {e}")
        return "error", ""


def parse_simple_format(cleaned_output):
    """Parse the simple format (just Line 1 and Line 2) with fallback for missing labels."""
    # Try format with "Line 1:" and "Line 2:" labels first
    line1_match = re.search(r'line\s*1:\s*(-?\d+\.?\d*)', cleaned_output, flags=re.IGNORECASE)
    line2_match = re.search(r'line\s*2:\s*(.+?)(?:\n|$)', cleaned_output, flags=re.IGNORECASE | re.DOTALL)
    
    if line1_match and line2_match:
        # Format with labels found
        try:
            score = float(line1_match.group(1))
            reason = line2_match.group(1).strip()
            
            if -1.0 <= score <= 1.0:
                if len(reason) > 100:
                    reason = reason[:97].rstrip() + "..."
                
                print(f"   📊 Simple Format Score: {score}")
                return score, reason
            else:
                print(f"❌ Score out of range [-1, 1]: {score}")
                return "error", ""
        except ValueError:
            print(f"❌ Could not parse score: '{line1_match.group(1)}'")
            return "error", ""
    
    # Fallback: Look for standalone number followed by text (no labels)
    print(f"   ⚠️ 'Line 1:' or 'Line 2:' labels missing, trying fallback parsing...")
    
    # Match: number (with optional sign and decimal) followed by any text
    fallback_match = re.search(r'^(-?\d+\.?\d*)\s*\n?\s*(.+)', cleaned_output.strip(), flags=re.DOTALL)
    
    if not fallback_match:
        print(f"❌ Could not parse output even with fallback")
        return "error", ""
    
    try:
        score = float(fallback_match.group(1))
        reason = fallback_match.group(2).strip()
        
        # Validate range
        if -1.0 <= score <= 1.0:
            # Enforce max 100 characters on the reason
            if len(reason) > 100:
                reason = reason[:97].rstrip() + "..."
            
            print(f"   📊 Fallback Format Score: {score}")
            
            return score, reason
        else:
            print(f"❌ Score out of range [-1, 1]: {score}")
            return "error", ""
    except ValueError:
        print(f"❌ Could not parse score: '{fallback_match.group(1)}'")
        return "error", ""