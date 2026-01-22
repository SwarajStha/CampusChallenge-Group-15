"""
validate_signal_return_panel.py

Validates the signal-return panel created by prepare_signal_return_panel.py

Performs comprehensive data quality checks:
1. Match rate and coverage statistics
2. Daily ticker count (critical for portfolio formation)
3. Signal and return distributions
4. Gap distribution analysis
5. Outlier detection
6. Missing data checks

Outputs:
- Console statistics report
- Validation plots (saved to results/Panel_Validation/)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# File paths
PANEL_FILE = "CampusChallenge-Group-15\data\signal_return_panel_cleaned(2).csv"
OUTPUT_DIR = "CampusChallenge-Group-15\data\Panel_Validation"

# Thresholds for warnings
MIN_TICKERS_PER_DAY = 30  # Minimum tickers needed for portfolio formation
EXTREME_RETURN_THRESHOLD = 0.50  # Flag returns > 50% (possible data errors)
EXTREME_SIGNAL_THRESHOLD = 1.0  # Signal should be in [-1, 1] range

def load_panel():
    """Load and prepare panel data"""
    print("Loading signal-return panel...")
    df = pd.read_csv(PANEL_FILE)
    
    # Convert dates
    df['signal_date'] = pd.to_datetime(df['signal_date'])
    df['return_date'] = pd.to_datetime(df['return_date'])
    
    print(f"  Total records: {len(df)}")
    print(f"  Date range (signals): {df['signal_date'].min()} to {df['signal_date'].max()}")
    print(f"  Date range (returns): {df['return_date'].min()} to {df['return_date'].max()}")
    
    return df


def analyze_coverage(df):
    """Analyze match coverage and data completeness"""
    print(f"\n{'='*60}")
    print("COVERAGE ANALYSIS")
    print(f"{'='*60}")
    
    # Ticker coverage
    unique_tickers = df['Ticker'].nunique()
    print(f"Unique tickers in panel: {unique_tickers}")
    
    # Observations per ticker
    obs_per_ticker = df.groupby('Ticker').size()
    print(f"\nObservations per ticker:")
    print(f"  Mean: {obs_per_ticker.mean():.1f}")
    print(f"  Median: {obs_per_ticker.median():.0f}")
    print(f"  Min: {obs_per_ticker.min()}")
    print(f"  Max: {obs_per_ticker.max()}")
    
    # Tickers with very few observations
    low_obs_tickers = obs_per_ticker[obs_per_ticker < 5]
    if len(low_obs_tickers) > 0:
        print(f"\n⚠️  Warning: {len(low_obs_tickers)} tickers have < 5 observations")
        print(f"     Sample: {low_obs_tickers.head(5).to_dict()}")


def analyze_daily_ticker_counts(df):
    """Analyze ticker availability per day (critical for portfolio formation)"""
    print(f"\n{'='*60}")
    print("DAILY TICKER COUNT ANALYSIS")
    print(f"{'='*60}")
    
    # Count tickers per signal date
    daily_counts = df.groupby('signal_date')['Ticker'].nunique()
    
    print(f"Trading days with signals: {len(daily_counts)}")
    print(f"\nTickers available per day:")
    print(f"  Mean: {daily_counts.mean():.1f}")
    print(f"  Median: {daily_counts.median():.0f}")
    print(f"  Min: {daily_counts.min()}")
    print(f"  Max: {daily_counts.max()}")
    print(f"  Std: {daily_counts.std():.1f}")
    
    # Check if any days have insufficient tickers
    low_days = daily_counts[daily_counts < MIN_TICKERS_PER_DAY]
    if len(low_days) > 0:
        print(f"\n⚠️  WARNING: {len(low_days)} days have < {MIN_TICKERS_PER_DAY} tickers!")
        print(f"     This may cause issues with portfolio formation.")
        print(f"     Dates with low counts:")
        print(low_days.sort_values().head(10))
    else:
        print(f"\n✅ All days have ≥ {MIN_TICKERS_PER_DAY} tickers (good for portfolio formation)")
    
    return daily_counts


def analyze_gap_distribution(df):
    """Analyze the gap between signal and return dates"""
    print(f"\n{'='*60}")
    print("GAP DISTRIBUTION (Signal → Return)")
    print(f"{'='*60}")
    
    gap_counts = df['days_gap'].value_counts().sort_index()
    print("\nGap frequency:")
    print(gap_counts)
    
    print(f"\nGap statistics:")
    print(f"  Mean: {df['days_gap'].mean():.2f} days")
    print(f"  Median: {df['days_gap'].median():.0f} days")
    print(f"  Mode: {df['days_gap'].mode()[0]} days")
    print(f"  Max: {df['days_gap'].max()} days")
    
    # Interpretation
    if df['days_gap'].median() == 1:
        print("\n✅ Most signals match to next-day returns (expected for weekdays)")
    elif df['days_gap'].median() <= 3:
        print("\n✅ Most signals match within 3 days (includes weekends)")
    else:
        print("\n⚠️  Warning: Median gap is high; check for data issues")
    
    return gap_counts


def analyze_signal_distribution(df):
    """Analyze sentiment signal distribution"""
    print(f"\n{'='*60}")
    print("SIGNAL DISTRIBUTION")
    print(f"{'='*60}")
    
    print(f"\nSignal statistics:")
    print(f"  Mean: {df['signal_score'].mean():.4f}")
    print(f"  Median: {df['signal_score'].median():.4f}")
    print(f"  Std: {df['signal_score'].std():.4f}")
    print(f"  Min: {df['signal_score'].min():.4f}")
    print(f"  Max: {df['signal_score'].max():.4f}")
    
    # Check for extreme signals
    extreme_signals = df[df['signal_score'].abs() > EXTREME_SIGNAL_THRESHOLD]
    if len(extreme_signals) > 0:
        print(f"\n⚠️  Warning: {len(extreme_signals)} signals have |score| > {EXTREME_SIGNAL_THRESHOLD}")
        print(f"     (Sentiment scores should typically be in [-1, 1])")
    
    # Check for concentration
    quantiles = df['signal_score'].quantile([0.05, 0.25, 0.5, 0.75, 0.95])
    print(f"\nSignal quantiles:")
    for q, val in quantiles.items():
        print(f"  {q*100:.0f}%: {val:.4f}")


def analyze_return_distribution(df):
    """Analyze return distribution and flag outliers"""
    print(f"\n{'='*60}")
    print("RETURN DISTRIBUTION")
    print(f"{'='*60}")
    
    print(f"\nReturn statistics:")
    print(f"  Mean: {df['RET'].mean():.6f} ({df['RET'].mean()*100:.4f}%)")
    print(f"  Median: {df['RET'].median():.6f} ({df['RET'].median()*100:.4f}%)")
    print(f"  Std: {df['RET'].std():.6f} ({df['RET'].std()*100:.4f}%)")
    print(f"  Min: {df['RET'].min():.6f} ({df['RET'].min()*100:.2f}%)")
    print(f"  Max: {df['RET'].max():.6f} ({df['RET'].max()*100:.2f}%)")
    
    # Check for extreme returns
    extreme_pos = df[df['RET'] > EXTREME_RETURN_THRESHOLD]
    extreme_neg = df[df['RET'] < -EXTREME_RETURN_THRESHOLD]
    
    if len(extreme_pos) > 0:
        print(f"\n⚠️  {len(extreme_pos)} observations with returns > {EXTREME_RETURN_THRESHOLD*100:.0f}%")
        print(f"     Sample (top 5):")
        print(extreme_pos.nlargest(5, 'RET')[['Ticker', 'return_date', 'RET', 'signal_score']])
    
    if len(extreme_neg) > 0:
        print(f"\n⚠️  {len(extreme_neg)} observations with returns < -{EXTREME_RETURN_THRESHOLD*100:.0f}%")
        print(f"     Sample (bottom 5):")
        print(extreme_neg.nsmallest(5, 'RET')[['Ticker', 'return_date', 'RET', 'signal_score']])
    
    # Quantiles
    quantiles = df['RET'].quantile([0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99])
    print(f"\nReturn quantiles:")
    for q, val in quantiles.items():
        print(f"  {q*100:.0f}%: {val:.6f} ({val*100:.4f}%)")


def check_missing_data(df):
    """Check for any missing values"""
    print(f"\n{'='*60}")
    print("MISSING DATA CHECK")
    print(f"{'='*60}")
    
    missing = df.isnull().sum()
    if missing.sum() == 0:
        print("✅ No missing values detected")
    else:
        print("⚠️  Missing values found:")
        print(missing[missing > 0])


def create_validation_plots(df, daily_counts, gap_counts, output_dir):
    """Generate validation plots"""
    print(f"\n{'='*60}")
    print("GENERATING VALIDATION PLOTS")
    print(f"{'='*60}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a figure with 6 subplots
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('Signal-Return Panel Validation', fontsize=16, fontweight='bold')
    
    # 1. Daily ticker count over time
    ax = axes[0, 0]
    daily_counts.plot(ax=ax, linewidth=1, color='steelblue')
    ax.axhline(y=MIN_TICKERS_PER_DAY, color='red', linestyle='--', linewidth=1, 
               label=f'Min threshold ({MIN_TICKERS_PER_DAY})')
    ax.set_title('Daily Ticker Count')
    ax.set_xlabel('Signal Date')
    ax.set_ylabel('Number of Tickers')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 2. Signal score distribution (histogram)
    ax = axes[0, 1]
    ax.hist(df['signal_score'], bins=50, color='green', alpha=0.7, edgecolor='black')
    ax.axvline(x=df['signal_score'].mean(), color='red', linestyle='--', 
               linewidth=2, label=f'Mean: {df["signal_score"].mean():.3f}')
    ax.set_title('Signal Score Distribution')
    ax.set_xlabel('Sentiment Score')
    ax.set_ylabel('Frequency')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 3. Return distribution (histogram)
    ax = axes[0, 2]
    # Clip extreme values for better visualization
    returns_clipped = df['RET'].clip(-0.20, 0.20)
    ax.hist(returns_clipped, bins=50, color='orange', alpha=0.7, edgecolor='black')
    ax.axvline(x=df['RET'].mean(), color='red', linestyle='--', 
               linewidth=2, label=f'Mean: {df["RET"].mean():.4f}')
    ax.set_title('Return Distribution (clipped at ±20%)')
    ax.set_xlabel('Daily Return')
    ax.set_ylabel('Frequency')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 4. Gap distribution (bar chart)
    ax = axes[1, 0]
    gap_counts.plot(kind='bar', ax=ax, color='purple', alpha=0.7)
    ax.set_title('Gap Distribution (Signal → Return)')
    ax.set_xlabel('Days Gap')
    ax.set_ylabel('Frequency')
    ax.grid(True, alpha=0.3)
    
    # 5. Scatter: Signal vs Return
    ax = axes[1, 1]
    # Sample for plotting if too many points
    if len(df) > 10000:
        plot_df = df.sample(10000, random_state=42)
    else:
        plot_df = df
    ax.scatter(plot_df['signal_score'], plot_df['RET'], alpha=0.3, s=10, color='steelblue')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    ax.set_title('Signal vs Next-Day Return')
    ax.set_xlabel('Sentiment Score')
    ax.set_ylabel('Next-Day Return')
    ax.grid(True, alpha=0.3)
    
    # Compute correlation
    corr = df['signal_score'].corr(df['RET'])
    ax.text(0.05, 0.95, f'Correlation: {corr:.4f}', 
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # 6. Observations per ticker (histogram)
    ax = axes[1, 2]
    obs_per_ticker = df.groupby('Ticker').size()
    ax.hist(obs_per_ticker, bins=30, color='teal', alpha=0.7, edgecolor='black')
    ax.axvline(x=obs_per_ticker.mean(), color='red', linestyle='--', 
               linewidth=2, label=f'Mean: {obs_per_ticker.mean():.1f}')
    ax.set_title('Observations per Ticker')
    ax.set_xlabel('Number of Observations')
    ax.set_ylabel('Number of Tickers')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    output_path = os.path.join(output_dir, 'panel_validation(3).png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"  Saved validation plots to: {output_path}")
    plt.close()


def main():
    print(f"{'='*60}")
    print("SIGNAL-RETURN PANEL VALIDATION")
    print(f"{'='*60}\n")
    
    # Load data
    df = load_panel()
    
    # Run validation checks
    analyze_coverage(df)
    daily_counts = analyze_daily_ticker_counts(df)
    gap_counts = analyze_gap_distribution(df)
    analyze_signal_distribution(df)
    analyze_return_distribution(df)
    check_missing_data(df)
    
    # Generate plots
    create_validation_plots(df, daily_counts, gap_counts, OUTPUT_DIR)
    
    # Final summary
    print(f"\n{'='*60}")
    print("VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total observations: {len(df):,}")
    print(f"Unique tickers: {df['Ticker'].nunique()}")
    print(f"Date range: {df['signal_date'].min()} to {df['signal_date'].max()}")
    print(f"Mean tickers per day: {daily_counts.mean():.1f}")
    print(f"Signal-Return correlation: {df['signal_score'].corr(df['RET']):.4f}")
    
    # Overall health check
    issues = []
    if daily_counts.min() < MIN_TICKERS_PER_DAY:
        issues.append(f"Some days have < {MIN_TICKERS_PER_DAY} tickers")
    if df['signal_score'].abs().max() > EXTREME_SIGNAL_THRESHOLD:
        issues.append("Extreme signal values detected")
    if df['RET'].abs().max() > EXTREME_RETURN_THRESHOLD:
        issues.append("Extreme return values detected")
    
    if len(issues) == 0:
        print("\n✅ Panel passed all validation checks!")
        print("   Ready for portfolio construction.")
    else:
        print("\n⚠️  Potential issues detected:")
        for issue in issues:
            print(f"   - {issue}")
        print("\n   Review the detailed output above before proceeding.")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
