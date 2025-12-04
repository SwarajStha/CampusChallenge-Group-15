# run_analysis.py
import os
import pandas as pd
import glob
from api_client import call_groq
from prompt_engine import load_system_prompt, build_messages
from sentiment_analysis import parse_llm_response

PROMPT_PATH = "CampusChallenge-Group-15/prompts/prompt_v3.txt"
DATA_PATH = "CampusChallenge-Group-15/sample-data/API_test_v2.csv"

def get_next_filename(base="Decision_Testing", ext=".csv", directory="results"):
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
        print(f"Processing {idx+1}/{len(df)}")
        messages = build_messages(system_prompt, row['title'])
        raw_output = call_groq(messages)
        score, reason = parse_llm_response(raw_output)
        
        results.append({
            "ID_Number": idx + 1,
            "Ticker": row["ticker"],
            "Headline": row["title"],
            "Score": score,
            "Reason": reason
        })
    
    # Save
    out_df = pd.DataFrame(results)
    os.makedirs("results", exist_ok=True)
    out_path = get_next_filename()  # Now checks results/ directory
    full_path = os.path.join("results", out_path)
    out_df.to_csv(full_path, index=False)
    print(f"✅ Saved to {full_path}")

if __name__ == "__main__":
    main()