# average_monthly_scores.py
import pandas as pd
import os

def average_monthly_scores(input_file, output_file):
    """
    Average Score and RET by Ticker and month.
    
    Args:
        input_file: Path to input CSV (e.g., Merged_Data_v6.csv)
        output_file: Path to output CSV (e.g., Monthly_Averaged_Score_v6.csv)
    """
    # Read the data
    df = pd.read_csv(input_file)
    
    print(f"Loaded {len(df)} rows from {input_file}")
    print(f"Columns: {df.columns.tolist()}")
    
    # Convert date to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Extract year-month
    df['YearMonth'] = df['Date'].dt.to_period('M')
    
    # Group by Ticker and YearMonth, then average Score and RET
    monthly_avg = df.groupby(['Ticker', 'YearMonth']).agg({
        'RET': 'mean',
        'Score': 'mean'
    }).reset_index()
    
    # Round to 3 decimal places
    monthly_avg['RET'] = monthly_avg['RET'].round(3)
    monthly_avg['Score'] = monthly_avg['Score'].round(3)
    
    # Convert YearMonth back to string format (YYYY-MM)
    monthly_avg['Date'] = monthly_avg['YearMonth'].astype(str)
    
    # Drop the YearMonth column and reorder
    monthly_avg = monthly_avg[['Ticker', 'Date', 'RET', 'Score']]
    
    # Sort by Ticker and Date
    monthly_avg = monthly_avg.sort_values(['Ticker', 'Date'])
    
    print(f"\nAveraged to {len(monthly_avg)} monthly records")
    print(f"Tickers: {monthly_avg['Ticker'].nunique()}")
    print(f"Date range: {monthly_avg['Date'].min()} to {monthly_avg['Date'].max()}")
    
    # Save to CSV
    monthly_avg.to_csv(output_file, index=False)
    print(f"\n✅ Saved to {output_file}")
    
    return monthly_avg


if __name__ == "__main__":
    # Define paths
    RESULTS_DIR = "CampusChallenge-Group-15/results/Merged Data"
    INPUT_FILE = os.path.join(RESULTS_DIR, "Merged_Data_v6(Full-Test_Data).csv")
    OUTPUT_FILE = os.path.join(RESULTS_DIR, "Monthly_Averaged_Score_v6(Full-Test_Data).csv")
    
    # Run averaging
    df_monthly = average_monthly_scores(INPUT_FILE, OUTPUT_FILE)
    
    # Display first few rows
    print("\nFirst 10 rows of output:")
    print(df_monthly.head(10))
