"""
clean_signal_return_panel.py

Cleans the signal-return panel by:
1. Removing tickers with insufficient observations (< min threshold)
2. Dropping rows with missing values in critical columns
3. Outputting a cleaned panel ready for portfolio construction

This addresses data quality issues identified by validate_signal_return_panel.py
"""

import pandas as pd
import numpy as np

# File paths
INPUT_FILE = "CampusChallenge-Group-15\data\signal_return_panel_cleaned.csv"
OUTPUT_FILE = "CampusChallenge-Group-15\data\signal_return_panel_cleaned(2).csv"

# Cleaning parameters
MIN_OBSERVATIONS_PER_TICKER = 5  # Drop tickers with fewer observations
REQUIRED_COLUMNS = ['RET', 'PRC', 'MV_USD_lag']  # Columns that cannot have missing values


def load_panel():
    """Load the signal-return panel"""
    print("Loading signal-return panel...")
    df = pd.read_csv(INPUT_FILE)
    
    # Convert dates
    df['signal_date'] = pd.to_datetime(df['signal_date'])
    df['return_date'] = pd.to_datetime(df['return_date'])
    
    print(f"  Initial records: {len(df)}")
    print(f"  Initial unique tickers: {df['Ticker'].nunique()}")
    
    return df


def remove_low_observation_tickers(df, min_obs):
    """Remove tickers with insufficient observations"""
    print(f"\n{'='*60}")
    print(f"REMOVING TICKERS WITH < {min_obs} OBSERVATIONS")
    print(f"{'='*60}")
    
    # Count observations per ticker
    obs_per_ticker = df.groupby('Ticker').size()
    
    # Identify tickers to remove
    low_obs_tickers = obs_per_ticker[obs_per_ticker < min_obs]
    
    if len(low_obs_tickers) > 0:
        print(f"Found {len(low_obs_tickers)} tickers with < {min_obs} observations:")
        print(low_obs_tickers.to_dict())
        
        # Calculate records to be removed
        records_to_remove = df[df['Ticker'].isin(low_obs_tickers.index)]
        print(f"\nRecords to be removed: {len(records_to_remove)}")
        
        # Filter out low-observation tickers
        df_filtered = df[~df['Ticker'].isin(low_obs_tickers.index)].copy()
        
        print(f"Records after filtering: {len(df_filtered)}")
        print(f"Tickers after filtering: {df_filtered['Ticker'].nunique()}")
    else:
        print(f"✅ No tickers found with < {min_obs} observations")
        df_filtered = df.copy()
    
    return df_filtered


def remove_missing_values(df, required_cols):
    """Remove rows with missing values in critical columns"""
    print(f"\n{'='*60}")
    print("REMOVING ROWS WITH MISSING VALUES")
    print(f"{'='*60}")
    
    # Check for missing values before
    print(f"\nMissing values before cleaning:")
    missing_before = df[required_cols].isnull().sum()
    print(missing_before)
    
    if missing_before.sum() > 0:
        # Count rows to be removed
        rows_with_missing = df[required_cols].isnull().any(axis=1).sum()
        print(f"\nRows with missing values in {required_cols}: {rows_with_missing}")
        
        # Show sample of rows to be removed
        print(f"\nSample of rows with missing values:")
        sample_missing = df[df[required_cols].isnull().any(axis=1)].head(5)
        print(sample_missing[['Ticker', 'signal_date', 'return_date'] + required_cols])
        
        # Drop rows with missing values
        df_cleaned = df.dropna(subset=required_cols).copy()
        
        print(f"\nRecords after removing missing values: {len(df_cleaned)}")
        print(f"Records removed: {len(df) - len(df_cleaned)}")
        
        # Verify no missing values remain
        missing_after = df_cleaned[required_cols].isnull().sum()
        if missing_after.sum() == 0:
            print(f"\n✅ All missing values removed from critical columns")
        else:
            print(f"\n⚠️  Warning: Some missing values remain:")
            print(missing_after[missing_after > 0])
    else:
        print("\n✅ No missing values found in critical columns")
        df_cleaned = df.copy()
    
    return df_cleaned


def final_validation(df_original, df_cleaned):
    """Provide summary statistics comparing original and cleaned datasets"""
    print(f"\n{'='*60}")
    print("CLEANING SUMMARY")
    print(f"{'='*60}")
    
    print(f"\nOriginal dataset:")
    print(f"  Records: {len(df_original):,}")
    print(f"  Unique tickers: {df_original['Ticker'].nunique()}")
    print(f"  Date range: {df_original['signal_date'].min()} to {df_original['signal_date'].max()}")
    
    print(f"\nCleaned dataset:")
    print(f"  Records: {len(df_cleaned):,}")
    print(f"  Unique tickers: {df_cleaned['Ticker'].nunique()}")
    print(f"  Date range: {df_cleaned['signal_date'].min()} to {df_cleaned['signal_date'].max()}")
    
    print(f"\nData removed:")
    print(f"  Records: {len(df_original) - len(df_cleaned):,} ({100*(len(df_original)-len(df_cleaned))/len(df_original):.2f}%)")
    print(f"  Tickers: {df_original['Ticker'].nunique() - df_cleaned['Ticker'].nunique()}")
    
    # Check daily ticker counts
    daily_counts_original = df_original.groupby('signal_date')['Ticker'].nunique()
    daily_counts_cleaned = df_cleaned.groupby('signal_date')['Ticker'].nunique()
    
    print(f"\nDaily ticker counts:")
    print(f"  Original - Mean: {daily_counts_original.mean():.1f}, Min: {daily_counts_original.min()}")
    print(f"  Cleaned  - Mean: {daily_counts_cleaned.mean():.1f}, Min: {daily_counts_cleaned.min()}")
    
    # Check observations per ticker
    obs_per_ticker = df_cleaned.groupby('Ticker').size()
    print(f"\nObservations per ticker (cleaned):")
    print(f"  Mean: {obs_per_ticker.mean():.1f}")
    print(f"  Median: {obs_per_ticker.median():.0f}")
    print(f"  Min: {obs_per_ticker.min()}")
    print(f"  Max: {obs_per_ticker.max()}")


def main():
    print(f"{'='*60}")
    print("SIGNAL-RETURN PANEL CLEANING")
    print(f"{'='*60}\n")
    
    # Load data
    df_original = load_panel()
    
    # Apply cleaning steps
    df_step1 = remove_low_observation_tickers(df_original, MIN_OBSERVATIONS_PER_TICKER)
    df_cleaned = remove_missing_values(df_step1, REQUIRED_COLUMNS)
    
    # Final validation
    final_validation(df_original, df_cleaned)
    
    # Save cleaned panel
    print(f"\n{'='*60}")
    print("SAVING CLEANED PANEL")
    print(f"{'='*60}")
    
    df_cleaned.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Cleaned panel saved to: {OUTPUT_FILE}")
    print(f"   Records: {len(df_cleaned):,}")
    print(f"   Tickers: {df_cleaned['Ticker'].nunique()}")
    
    print(f"\n{'='*60}")
    print("NEXT STEPS")
    print(f"{'='*60}")
    print("1. Run validate_signal_return_panel.py on the cleaned file")
    print("   (update PANEL_FILE to 'signal_return_panel_cleaned.csv')")
    print("2. Proceed to portfolio construction if validation passes")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
