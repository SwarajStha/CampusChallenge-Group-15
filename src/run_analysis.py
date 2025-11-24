# run_analysis.py
import os
import pandas as pd
import glob
from api_client import call_groq
from prompt_engine import load_system_prompt, build_messages
from sentiment_analysis import parse_llm_response

PROMPT_PATH = "prompts/prompt_v1.txt"
DATA_PATH = "sample-data/API_test.csv"

def get_next_filename(base="Decision_Testing", ext=".csv"):
    existing = glob.glob(f"{base}*{ext}")
    nums = []
    for f in existing:
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
        decision, reason = parse_llm_response(raw_output)
        
        results.append({
            "ID_Number": idx + 1,
            "Ticker": row["ticker"],
            "Headline": row["title"],
            "Decision": decision,
            "Reason": reason
        })
    
    # Save
    out_df = pd.DataFrame(results)
    out_path = get_next_filename()
    os.makedirs("results", exist_ok=True)
    out_df.to_csv(f"results/{out_path}", index=False)
    print(f"✅ Saved to results/{out_path}")

if __name__ == "__main__":
    main()