"""
prepare_signal_return_panel.py

Creates a clean panel linking sentiment signals to next-trading-day returns.

Key features:
1. Maps each (ticker, sentiment_date) to the next available trading day for that ticker
2. Handles weekends, holidays, and ticker-specific missing data automatically
3. Applies a max-gap filter to avoid matching stale signals to distant returns
4. Outputs a clean panel ready for portfolio construction

Output columns:
- Ticker: stock ticker
- signal_date: date of sentiment (original date_day)
- signal_score: sentiment score to use for ranking
- return_date: date of the matched return (next trading day)
- RET: daily return on return_date
- days_gap: calendar days between signal_date and return_date
- PRC, MV_USD_lag: additional return data for weighting/filtering
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# File paths (relative to project root)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, '..', '..')  # Go up to project root

SENTIMENT_FILE = os.path.join(project_root, 'data', 'Full Extracted File (sorted).csv')
RETURNS_FILE = os.path.join(project_root, 'data', 'daily_return_data_cleaned.csv')
OUTPUT_FILE = os.path.join(project_root, 'data', 'signal_return_panel.csv')

# Configuration
MAX_GAP_DAYS = 5  # Maximum calendar days between sentiment and return
                   # (filters out stale signals; adjust if needed)

def load_data():
    """Load and prepare input datasets"""
    print("Loading data files...")
    
    # Load sentiment data
    sentiment_df = pd.read_csv(SENTIMENT_FILE)
    sentiment_df['date_day'] = pd.to_datetime(sentiment_df['date_day'])
    
    # Load returns data
    returns_df = pd.read_csv(RETURNS_FILE)
    returns_df['date'] = pd.to_datetime(returns_df['date'])
    
    print(f"  Sentiment records: {len(sentiment_df)}")
    print(f"  Sentiment date range: {sentiment_df['date_day'].min()} to {sentiment_df['date_day'].max()}")
    print(f"  Unique tickers in sentiment: {sentiment_df['Ticker'].nunique()}")
    print(f"\n  Returns records: {len(returns_df)}")
    print(f"  Returns date range: {returns_df['date'].min()} to {returns_df['date'].max()}")
    print(f"  Unique tickers in returns: {returns_df['TICKER'].nunique()}")
    
    return sentiment_df, returns_df


def build_trading_calendar_by_ticker(returns_df):
    """
    Build a dictionary mapping each ticker to its sorted list of trading days.
    
    Returns:
        dict: {ticker: sorted list of trading dates}
    """
    print("\nBuilding per-ticker trading calendars...")
    
    calendar = {}
    for ticker in returns_df['TICKER'].unique():
        ticker_dates = returns_df[returns_df['TICKER'] == ticker]['date'].sort_values().tolist()
        calendar[ticker] = ticker_dates
    
    print(f"  Created calendars for {len(calendar)} tickers")
    
    # Sample statistics
    lengths = [len(dates) for dates in calendar.values()]
    print(f"  Trading days per ticker: min={min(lengths)}, max={max(lengths)}, avg={np.mean(lengths):.1f}")
    
    return calendar


def find_next_trading_day(signal_date, ticker, trading_calendar, max_gap_days=5):
    """
    Find the next available trading day for a ticker after the signal date.
    
    Args:
        signal_date: datetime of sentiment signal
        ticker: stock ticker
        trading_calendar: dict mapping ticker to list of trading dates
        max_gap_days: maximum allowed gap (calendar days)
    
    Returns:
        datetime of next trading day, or None if no match within max_gap
    """
    if ticker not in trading_calendar:
        return None
    
    ticker_dates = trading_calendar[ticker]
    
    # Find first date strictly after signal_date
    for trade_date in ticker_dates:
        if trade_date > signal_date:
            # Check if within max gap
            gap = (trade_date - signal_date).days
            if gap <= max_gap_days:
                return trade_date
            else:
                return None  # Too far in the future
    
    return None  # No trading day found after signal_date


def create_signal_return_panel(sentiment_df, returns_df, trading_calendar, max_gap_days=5):
    """
    Create the merged signal-return panel with next-trading-day mapping.
    """
    print(f"\nMapping sentiment signals to next trading days (max gap: {max_gap_days} days)...")
    
    # Prepare output lists
    results = []
    
    # Track statistics
    matched = 0
    no_trading_day = 0
    gap_too_large = 0
    
    # Process each sentiment observation
    for idx, row in sentiment_df.iterrows():
        ticker = row['Ticker']
        signal_date = row['date_day']
        signal_score = row['Sentiment_Score']
        
        # Find next trading day
        next_trade_date = find_next_trading_day(signal_date, ticker, trading_calendar, max_gap_days)
        
        if next_trade_date is None:
            # Check if ticker exists in calendar
            if ticker in trading_calendar:
                # Ticker exists but no match within max_gap
                # Try without gap limit to see actual gap
                for trade_date in trading_calendar[ticker]:
                    if trade_date > signal_date:
                        actual_gap = (trade_date - signal_date).days
                        if actual_gap > max_gap_days:
                            gap_too_large += 1
                        break
                else:
                    no_trading_day += 1  # Signal after last trading day
            else:
                no_trading_day += 1  # Ticker not in returns at all
            continue
        
        # Get the return data for this (ticker, next_trade_date)
        return_row = returns_df[
            (returns_df['TICKER'] == ticker) & 
            (returns_df['date'] == next_trade_date)
        ]
        
        if len(return_row) == 0:
            # This shouldn't happen if trading_calendar is built correctly
            no_trading_day += 1
            continue
        
        return_row = return_row.iloc[0]
        
        # Calculate days gap
        days_gap = (next_trade_date - signal_date).days
        
        # Append to results
        results.append({
            'Ticker': ticker,
            'signal_date': signal_date,
            'signal_score': signal_score,
            'return_date': next_trade_date,
            'RET': return_row['RET'],
            'PRC': return_row['PRC'],
            'MV_USD_lag': return_row['MV_USD_lag'],
            'days_gap': days_gap
        })
        
        matched += 1
        
        # Progress indicator
        if (idx + 1) % 10000 == 0:
            print(f"  Processed {idx + 1}/{len(sentiment_df)} records...")
    
    panel_df = pd.DataFrame(results)
    
    # Statistics
    print(f"\n{'='*60}")
    print("MATCHING STATISTICS")
    print(f"{'='*60}")
    print(f"Total sentiment observations: {len(sentiment_df)}")
    print(f"Successfully matched: {matched} ({100*matched/len(sentiment_df):.1f}%)")
    print(f"No trading day found: {no_trading_day} ({100*no_trading_day/len(sentiment_df):.1f}%)")
    print(f"Gap too large (>{max_gap_days} days): {gap_too_large} ({100*gap_too_large/len(sentiment_df):.1f}%)")
    
    if len(panel_df) > 0:
        print(f"\nGap distribution (calendar days):")
        print(panel_df['days_gap'].value_counts().sort_index())
        print(f"\nMean gap: {panel_df['days_gap'].mean():.2f} days")
        print(f"Median gap: {panel_df['days_gap'].median():.0f} days")
    
    return panel_df


def main():
    print(f"{'='*60}")
    print("SIGNAL-RETURN PANEL CREATION")
    print(f"{'='*60}\n")
    
    # Load data
    sentiment_df, returns_df = load_data()
    
    # Build per-ticker trading calendars
    trading_calendar = build_trading_calendar_by_ticker(returns_df)
    
    # Create the merged panel
    panel_df = create_signal_return_panel(
        sentiment_df, 
        returns_df, 
        trading_calendar, 
        max_gap_days=MAX_GAP_DAYS
    )
    
    # Save output
    print(f"\n{'='*60}")
    print("SAVING OUTPUT")
    print(f"{'='*60}")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Records in panel: {len(panel_df)}")
    
    if len(panel_df) > 0:
        panel_df.to_csv(OUTPUT_FILE, index=False)
        
        print(f"\nDate range: {panel_df['signal_date'].min()} to {panel_df['signal_date'].max()}")
        print(f"Unique tickers: {panel_df['Ticker'].nunique()}")
        
        print(f"\nFirst 5 rows:")
        print(panel_df.head().to_string())
        
        print(f"\n✅ Panel saved to {OUTPUT_FILE}")
    else:
        print("⚠️  Warning: No records in output panel!")
    
    print(f"\n{'='*60}")


if __name__ == "__main__":
    main()
