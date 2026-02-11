# merge_data_monthly.py
import pandas as pd
from pandas.tseries.offsets import DateOffset
import os

# Get project root (go up two levels from src/Prompt Comparison/)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, '..', '..')  # Go up to project root

# File paths - change these variables to use different files
MONTHLY_SCORES_FILE = os.path.join(project_root, 'Statistics', 'Prompt Testing Phase', 'Merged Data (Test Data - Prompt Evaluation)', 'Monthly_Averaged_Score_v6(Full-Test_Data).csv')
MONTHLY_RETURNS_FILE = os.path.join(project_root, 'data', 'data (sample and setup)', 'Full_TestData_MonthlyReturns.csv')
OUTPUT_FILE = os.path.join(project_root, 'Statistics', 'Prompt Testing Phase', 'Merged Data (Test Data - Prompt Evaluation)', 'Merged_Monthly_Data_v6(Full-Test_Data).csv')

def merge_monthly_datasets(monthly_scores_file, monthly_returns_file, output_file):
    """
    Merge monthly averaged scores and monthly returns datasets based on ticker and adjusted month.
    
    Args:
        monthly_scores_file: Path to the monthly averaged scores CSV file
        monthly_returns_file: Path to the monthly returns CSV file
        output_file: Path to save the merged output CSV file
    """
    
    # Read the datasets
    print(f"Reading {monthly_scores_file}...")
    scores_df = pd.read_csv(monthly_scores_file)
    
    print(f"Reading {monthly_returns_file}...")
    returns_df = pd.read_csv(monthly_returns_file)
    
    # Display original counts
    print(f"\nOriginal rows - Monthly Scores: {len(scores_df)}, Monthly Returns: {len(returns_df)}")
    print(f"Scores columns: {scores_df.columns.tolist()}")
    print(f"Returns columns: {returns_df.columns.tolist()}")
    
    # Convert date columns to datetime
    scores_df['Date'] = pd.to_datetime(scores_df['Date'], format='%Y-%m')
    
    # Check the date column name in returns_df
    date_col_returns = None
    for col in returns_df.columns:
        if col.lower() in ['date', 'month', 'yearmonth']:
            date_col_returns = col
            break
    
    if date_col_returns is None:
        print("Warning: Could not find date column in returns file. Using first column.")
        date_col_returns = returns_df.columns[0]
    
    # Parse date from returns file (may be YYYY-MM-DD format, convert to month)
    returns_df['date'] = pd.to_datetime(returns_df[date_col_returns])
    # Extract year-month only for matching
    returns_df['date_month'] = returns_df['date'].dt.to_period('M').dt.to_timestamp()
    
    # Add 1 month to Monthly Scores dates (handles year transitions automatically)
    print("\nAdding 1 month to Monthly Scores dates...")
    scores_df['Date_Adjusted'] = scores_df['Date'] + DateOffset(months=1)
    
    print(f"Sample date adjustments:")
    print(f"  Original: {scores_df['Date'].iloc[0].strftime('%Y-%m')} -> Adjusted: {scores_df['Date_Adjusted'].iloc[0].strftime('%Y-%m')}")
    if len(scores_df) > 5:
        print(f"  Original: {scores_df['Date'].iloc[5].strftime('%Y-%m')} -> Adjusted: {scores_df['Date_Adjusted'].iloc[5].strftime('%Y-%m')}")
    
    # Standardize ticker column names for merging
    ticker_col_scores = None
    for col in scores_df.columns:
        if col.lower() == 'ticker':
            ticker_col_scores = col
            break
    
    ticker_col_returns = None
    for col in returns_df.columns:
        if col.lower() == 'ticker':
            ticker_col_returns = col
            break
    
    if ticker_col_scores:
        scores_df['ticker_merge'] = scores_df[ticker_col_scores]
    else:
        print("Error: No ticker column found in scores file!")
        return
    
    if ticker_col_returns:
        returns_df['ticker_merge'] = returns_df[ticker_col_returns]
    else:
        print("Error: No ticker column found in returns file!")
        return
    
    # Merge the datasets on ticker and adjusted month
    print("\nMerging datasets on ticker and adjusted month...")
    merged_df = pd.merge(
        scores_df,
        returns_df,
        left_on=['ticker_merge', 'Date_Adjusted'],
        right_on=['ticker_merge', 'date_month'],
        how='inner',
        suffixes=('_daily', '_monthly')
    )
    
    print(f"Merged rows: {len(merged_df)}")
    print(f"Merged columns: {merged_df.columns.tolist()}")
    
    # Select and rename columns to keep
    output_df = pd.DataFrame({
        'Date': merged_df['date_month'].dt.strftime('%Y-%m'),  # Use the date from returns (already adjusted)
        'Ticker': merged_df['ticker_merge'],
        'RET (monthly)': merged_df['RET_monthly'],
        'RET (daily-averaged)': merged_df['RET_daily'],
        'Score': merged_df['Score']
    })
    
    # Round to 3 decimal places
    output_df['RET (monthly)'] = output_df['RET (monthly)'].round(3)
    output_df['RET (daily-averaged)'] = output_df['RET (daily-averaged)'].round(3)
    output_df['Score'] = output_df['Score'].round(3)
    
    # Sort by Ticker and Date
    output_df = output_df.sort_values(['Ticker', 'Date'])
    
    # Save the merged dataset
    print(f"\nSaving merged data to {output_file}...")
    output_df.to_csv(output_file, index=False)
    
    print(f"✅ Successfully saved {len(output_df)} rows to {output_file}")
    
    # Display summary statistics
    print("\n=== Summary Statistics ===")
    print(f"Unique tickers: {output_df['Ticker'].nunique()}")
    print(f"Date range: {output_df['Date'].min()} to {output_df['Date'].max()}")
    print(f"\nFirst 10 rows:")
    print(output_df.head(10))
    
    return output_df


if __name__ == "__main__":
    merge_monthly_datasets(MONTHLY_SCORES_FILE, MONTHLY_RETURNS_FILE, OUTPUT_FILE)
