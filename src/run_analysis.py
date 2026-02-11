# run_analysis.py
import os
import pandas as pd
import glob
import re
from api_client import call_groq
from prompt_engine import load_system_prompt, build_messages
from sentiment_analysis import parse_llm_response

# Get project root (go up one level from src/)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, '..')  # Go up to project root

# Configuration
DATA_PATH = os.path.join(project_root, 'data', 'data (sample and setup)', 'API_test.csv')
RESULTS_DIR = os.path.join(project_root, 'Statistics', 'Prompt Testing Phase', 'Decision Testing Scores (Prompt Testing)')

# Switch between prompt versions here
# PROMPT_PATH = os.path.join(project_root, 'prompts', 'prompt_v6.txt')  # Two-message format
PROMPT_PATH = os.path.join(project_root, 'prompts', 'prompt_v8 (FINAL).txt')  # Single-message with placeholders


def get_next_filename(base="Decision_Testing", ext=".csv", directory=RESULTS_DIR):
    """Find the next available filename with incremental numbering."""
    # Look for files in the specified directory
    pattern = os.path.join(directory, f"{base}*{ext}")
    existing = glob.glob(pattern)
    
    nums = []
    for f in existing:
        # Extract just the filename without directory
        stem = os.path.basename(f).replace(base, "").replace(ext, "")
        if stem.isdigit():
            nums.append(int(stem))
    
    next_num = max(nums) + 1 if nums else 1
    return f"{base}{next_num}{ext}"

def main():
    # Load data & prompt
    df = pd.read_csv(DATA_PATH)
    system_prompt = load_system_prompt(PROMPT_PATH)
    
    results = []
    for idx, row in df.iterrows():
        print(f"\n{'='*80}")
        print(f"Processing {idx+1}/{len(df)}")
        print(f"Ticker: {row['ticker']}")
        print(f"Headline: {row['title']}")
        
        # Check if tags column exists
        tags = row.get('tags', None) if 'tags' in df.columns else None
        if tags:
            print(f"Tags: {tags}")
        
        print(f"{'-'*80}")
        
        messages = build_messages(system_prompt, row['title'], tags)
        raw_output = call_groq(messages)
        
        print(f"🔍 RAW LLM OUTPUT:")
        print(raw_output)
        print(f"{'-'*80}")
        
        score, reason = parse_llm_response(raw_output)
        
        print(f"📊 PARSED RESULTS:")
        print(f"   Score: {score}")
        print(f"   Reason: {reason}")
        print(f"{'='*80}\n")
        
        # Extract date part only (before 'T')
        date_only = row['date'].split('T')[0] if 'T' in str(row['date']) else row['date']
        
        results.append({
            "ID_Number": idx + 1,
            "Ticker": row["ticker"],
            "Date": date_only,
            "Headline": row["title"],
            "Score": score,
            "Reason": reason
        })
    
    # Save
    out_df = pd.DataFrame(results)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = get_next_filename()  # Checks results/directory
    full_path = os.path.join(RESULTS_DIR, out_path)
    out_df.to_csv(full_path, index=False)
    print(f"✅ Saved to {full_path}")

if __name__ == "__main__":
    main()