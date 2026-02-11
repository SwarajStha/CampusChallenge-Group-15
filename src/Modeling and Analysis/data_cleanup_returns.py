"""
data_cleanup_returns.py

Cleans the daily return data by:
1. Filtering to only tickers that appear in the sentiment headlines file
2. Removing timestamps from the date column (keep YYYY-MM-DD format only)
"""

import pandas as pd
import os

# File paths (relative to project root)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, '..', '..')  # Go up to project root

RETURNS_FILE = os.path.join(project_root, 'data', 'daily_return_data_datefiltered.csv')
SENTIMENT_FILE = os.path.join(project_root, 'All_RAW_Returns', 'Extracted Files', 'Final Extracted File.csv')
OUTPUT_FILE = os.path.join(project_root, 'data', 'daily_return_data_cleaned.csv')

def main():
    # Read the datasets
    print(f"Reading {RETURNS_FILE}...")
    returns_df = pd.read_csv(RETURNS_FILE)
    
    print(f"Reading {SENTIMENT_FILE}...")
    sentiment_df = pd.read_csv(SENTIMENT_FILE)
    
    # Display initial counts
    print(f"\n{'='*60}")
    print("INITIAL DATA")
    print(f"{'='*60}")
    print(f"Returns records: {len(returns_df)}")
    print(f"Unique tickers in returns: {returns_df['TICKER'].nunique()}")
    print(f"Unique tickers in sentiment: {sentiment_df['Ticker'].nunique()}")
    
    # Get the set of valid tickers from sentiment file
    valid_tickers = set(sentiment_df['Ticker'].unique())
    print(f"\nValid tickers (from sentiment file): {len(valid_tickers)}")
    
    # Filter returns to only include valid tickers
    print("\nFiltering returns data to match sentiment tickers...")
    filtered_returns = returns_df[returns_df['TICKER'].isin(valid_tickers)].copy()
    
    print(f"Records after ticker filtering: {len(filtered_returns)}")
    print(f"Unique tickers after filtering: {filtered_returns['TICKER'].nunique()}")
    
    # Clean the date format (remove timestamp)
    print("\nCleaning date format (removing timestamps)...")
    
    # Convert to datetime first, then to date string
    filtered_returns['date'] = pd.to_datetime(filtered_returns['date'])
    filtered_returns['date'] = filtered_returns['date'].dt.strftime('%Y-%m-%d')
    
    # Display sample of cleaned dates
    print(f"\nSample of cleaned dates:")
    print(filtered_returns['date'].head(10).to_string())
    
    # Sort by TICKER first, then by date
    print("\nSorting data by TICKER and date...")
    filtered_returns = filtered_returns.sort_values(by=['TICKER', 'date'], ascending=[True, True])
    
    # Save the cleaned data
    print(f"\nSaving cleaned data to {OUTPUT_FILE}...")
    filtered_returns.to_csv(OUTPUT_FILE, index=False)
    
    # Summary statistics
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Original records: {len(returns_df)}")
    print(f"Cleaned records: {len(filtered_returns)}")
    print(f"Records removed: {len(returns_df) - len(filtered_returns)}")
    print(f"Unique tickers: {filtered_returns['TICKER'].nunique()}")
    print(f"Date range: {filtered_returns['date'].min()} to {filtered_returns['date'].max()}")
    print(f"\n✅ Cleaned data saved to {OUTPUT_FILE}")
    
    # Show tickers that were in returns but not in sentiment (informational)
    removed_tickers = set(returns_df['TICKER'].unique()) - valid_tickers
    if removed_tickers:
        print(f"\nTickers removed (not in sentiment data): {len(removed_tickers)}")
        if len(removed_tickers) <= 10:
            print(f"Removed tickers: {sorted(removed_tickers)}")
        else:
            print(f"Sample of removed tickers: {sorted(list(removed_tickers))[:10]}")

if __name__ == "__main__":
    main()
