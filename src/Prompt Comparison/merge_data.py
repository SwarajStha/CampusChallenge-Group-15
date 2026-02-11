import pandas as pd
from datetime import timedelta
import os

# Get project root (go up two levels from src/Prompt Comparison/)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, '..', '..')  # Go up to project root

# File paths - change these variables to use different files
DECISION_FILE = os.path.join(project_root, 'Statistics', 'Prompt Testing Phase', 'Decision Testing Scores (Prompt Testing)', 'Decision_Testing_Full1.csv')
RETURNS_FILE = os.path.join(project_root, 'data', 'data (sample and setup)', 'Full_TestData_DailyReturns.csv')
OUTPUT_FILE = os.path.join(project_root, 'Statistics', 'Prompt Testing Phase', 'Merged Data (Test Data - Prompt Evaluation)', 'Merged_Data_v6(Full-Test_Data)_non-adjusted.csv')

def merge_datasets(decision_file, returns_file, output_file):
    """
    Merge decision and returns datasets based on ticker and adjusted date.
    
    Args:
        decision_file: Path to the decision testing CSV file
        returns_file: Path to the daily returns CSV file
        output_file: Path to save the merged output CSV file
    """
    
    # Read the datasets
    print(f"Reading {decision_file}...")
    decision_df = pd.read_csv(decision_file)
    
    print(f"Reading {returns_file}...")
    returns_df = pd.read_csv(returns_file)
    
    # Display original counts
    print(f"\nOriginal rows - Decision: {len(decision_df)}, Returns: {len(returns_df)}")
    
    # Standardize column names for merging
    # Convert date columns to datetime
    decision_df['Date'] = pd.to_datetime(decision_df['Date'])
    returns_df['date'] = pd.to_datetime(returns_df['date'])
    
    # Add 1 day to Decision_Testing dates
    print("\nAdding 1 day to Decision_Testing dates...")
    decision_df['Date_Adjusted'] = decision_df['Date'] + timedelta(days=1) # No need to adjust for daily data - comment after '+'
    
    # Standardize ticker column names for merging
    # Check which column name is used
    if 'Ticker' in decision_df.columns:
        decision_df['ticker_merge'] = decision_df['Ticker']
    else:
        decision_df['ticker_merge'] = decision_df['ticker']
    
    if 'TICKER' in returns_df.columns:
        returns_df['ticker_merge'] = returns_df['TICKER']
    elif 'Ticker' in returns_df.columns:
        returns_df['ticker_merge'] = returns_df['Ticker']
    else:
        returns_df['ticker_merge'] = returns_df['ticker']
    
    # Merge the datasets on ticker and adjusted date
    print("\nMerging datasets on ticker and adjusted date...")
    merged_df = pd.merge(
        decision_df,
        returns_df,
        left_on=['ticker_merge', 'Date_Adjusted'],
        right_on=['ticker_merge', 'date'],
        how='inner'
    )
    
    print(f"Merged rows: {len(merged_df)}")
    
    # Select and rename columns to keep
    output_df = pd.DataFrame({
        'Ticker': merged_df['ticker_merge'],
        'Date': merged_df['date'],  # Use the date from returns (already adjusted)
        'PRC': merged_df['PRC'],
        'RET': merged_df['RET'],
        'Headline': merged_df['Headline'],
        'Score': merged_df['Score']
    })
    
    # Save the merged dataset
    print(f"\nSaving merged data to {output_file}...")
    output_df.to_csv(output_file, index=False)
    
    print(f"✅ Successfully saved {len(output_df)} rows to {output_file}")
    
    # Display summary statistics
    print("\n" + "="*60)
    print("SUMMARY:")
    print("="*60)
    print(f"Unique tickers: {output_df['Ticker'].nunique()}")
    print(f"Date range: {output_df['Date'].min()} to {output_df['Date'].max()}")
    print(f"Average Score: {output_df['Score'].mean():.4f}")
    print(f"Average Return (RET): {output_df['RET'].mean():.6f}")
    print("\nFirst few rows:")
    print(output_df.head(10))
    
    return output_df

if __name__ == "__main__":
    # Run the merge
    merged_data = merge_datasets(DECISION_FILE, RETURNS_FILE, OUTPUT_FILE)
