"""
fama_macbeth.py

Performs Fama-MacBeth cross-sectional regressions to test if sentiment signal predicts future returns.

Methodology:
1. For each rebalancing period t, run cross-sectional regression:
   R_{i,t+1} = a_t + b_t × Signal_{i,t} + ε_{i,t+1}
   
2. Collect time-series of slope coefficients {b_t}

3. Test if mean(b_t) is statistically different from zero using Newey-West SE

Inputs:
- signal_return_panel_cleaned.csv (contains signal scores and forward returns)

Outputs:
- Fama-MacBeth slope time-series for each configuration
- Summary statistics with t-stats and significance tests
- Saved to ../results/Fama_MacBeth/
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS
import os
import warnings
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')

# File paths
DATA_DIR = "."
OUTPUT_DIR = "../results/Fama_MacBeth"

# Signal/return panel file
PANEL_FILE = "signal_return_panel_cleaned(2).csv"  # Use the latest cleaned version

# Rebalancing configurations
REBALANCE_CONFIGS = {
    'monthly': {'freq': 'M', 'forward_days': 21, 'label': 'Monthly'},
    'weekly': {'freq': 'W', 'forward_days': 5, 'label': 'Weekly'}
}

# Newey-West lag selection for time-series regression
HAC_LAGS = {
    'monthly': 3,  # ~3 months of autocorrelation
    'weekly': 4    # ~4 weeks of autocorrelation
}


def load_signal_return_panel():
    """Load the signal-return panel data"""
    file_path = os.path.join(DATA_DIR, PANEL_FILE)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Panel file not found: {file_path}")
    
    print(f"Loading signal-return panel: {PANEL_FILE}")
    df = pd.read_csv(file_path)
    
    # Standardize column names
    df = df.rename(columns={
        'Ticker': 'ticker',
        'signal_date': 'date',
        'signal_score': 'composite_signal',
        'return_date': 'forward_date',
        'RET': 'forward_return'
    })
    
    # Convert date columns to datetime
    df['date'] = pd.to_datetime(df['date'])
    df['forward_date'] = pd.to_datetime(df['forward_date'])
    
    print(f"  Total observations: {len(df)}")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  Unique tickers: {df['ticker'].nunique()}")
    print(f"  Columns: {df.columns.tolist()}")
    
    return df


def assign_rebalancing_periods(df, freq='M'):
    """
    Assign each observation to a rebalancing period.
    
    Args:
        df: DataFrame with 'date' column
        freq: 'M' for monthly, 'W' for weekly
    
    Returns:
        DataFrame with 'rebal_period' column
    """
    df = df.copy()
    
    if freq == 'M':
        # Monthly: use month-end periods
        df['rebal_period'] = df['date'].dt.to_period('M')
    elif freq == 'W':
        # Weekly: use week-end periods (Sunday)
        df['rebal_period'] = df['date'].dt.to_period('W')
    else:
        raise ValueError(f"Unsupported frequency: {freq}")
    
    return df


def run_cross_sectional_regression(period_data, signal_col='composite_signal'):
    """
    Run cross-sectional regression for one period.
    
    R_{i,t+1} = a_t + b_t × Signal_{i,t} + ε_{i,t+1}
    
    Args:
        period_data: DataFrame with signal and forward return for this period
        signal_col: column name for signal
    
    Returns:
        Dictionary with regression results
    """
    # Check if we have required columns
    if signal_col not in period_data.columns:
        return None
    
    if 'forward_return' not in period_data.columns:
        return None
    
    # Drop missing values
    valid_data = period_data[[signal_col, 'forward_return']].dropna()
    
    if len(valid_data) < 10:  # Need minimum observations
        return None
    
    # Prepare regression
    y = valid_data['forward_return']
    X = valid_data[[signal_col]]
    X = sm.add_constant(X)
    
    try:
        # Run OLS
        model = OLS(y, X)
        results = model.fit()
        
        # Extract results
        intercept = results.params[0]
        slope = results.params[1]
        t_stat = results.tvalues[1]
        r_squared = results.rsquared
        n_obs = len(valid_data)
        
        return {
            'intercept': intercept,
            'slope': slope,
            't_stat': t_stat,
            'r_squared': r_squared,
            'n_obs': n_obs
        }
    except Exception as e:
        print(f"    Warning: Regression failed - {e}")
        return None


def fama_macbeth_analysis(df, config_name, freq='M', signal_col='composite_signal'):
    """
    Perform Fama-MacBeth analysis for a given rebalancing frequency.
    
    Args:
        df: signal-return panel DataFrame
        config_name: name of configuration (e.g., 'monthly', 'weekly')
        freq: rebalancing frequency ('M' or 'W')
        signal_col: signal column to use
    
    Returns:
        DataFrame with results for each period
    """
    print(f"\n{'='*60}")
    print(f"FAMA-MACBETH ANALYSIS: {config_name.upper()}")
    print(f"{'='*60}")
    
    # Assign rebalancing periods
    df = assign_rebalancing_periods(df, freq)
    
    # Get unique periods
    periods = sorted(df['rebal_period'].unique())
    print(f"  Rebalancing periods: {len(periods)}")
    print(f"  First period: {periods[0]}")
    print(f"  Last period: {periods[-1]}")
    
    # Run cross-sectional regression for each period
    results = []
    
    for period in periods:
        period_data = df[df['rebal_period'] == period]
        
        result = run_cross_sectional_regression(period_data, signal_col)
        
        if result is not None:
            result['period'] = str(period)
            result['date'] = period.to_timestamp()
            results.append(result)
            
            # Print progress every 5 periods
            if len(results) % 5 == 0:
                print(f"    Processed {len(results)} periods... Latest slope: {result['slope']:.6f} (t={result['t_stat']:.2f})")
    
    if not results:
        print("  ERROR: No valid cross-sectional regressions")
        return None
    
    results_df = pd.DataFrame(results)
    
    print(f"\n  ✓ Completed {len(results_df)} cross-sectional regressions")
    print(f"  Mean slope: {results_df['slope'].mean():.6f}")
    print(f"  Std dev of slopes: {results_df['slope'].std():.6f}")
    
    return results_df


def compute_fama_macbeth_statistics(slopes_df, hac_lags=3):
    """
    Compute Fama-MacBeth t-statistic with Newey-West standard errors.
    
    Args:
        slopes_df: DataFrame with 'slope' column (time-series of b_t)
        hac_lags: number of lags for Newey-West SE
    
    Returns:
        Dictionary with summary statistics
    """
    slopes = slopes_df['slope'].values
    
    # Mean slope
    mean_slope = slopes.mean()
    
    # Annualized mean slope (assuming daily forward returns)
    # For monthly: 21 trading days, annualize by *252/21 = *12
    # For weekly: 5 trading days, annualize by *252/5 = *50.4
    # But slope is already in terms of forward return, so just report as is
    
    # Time-series regression with Newey-West SE
    # y = slopes, X = constant (just testing if mean != 0)
    y = slopes
    X = np.ones(len(slopes))
    X = sm.add_constant(X[:, np.newaxis])[:, 0:1]  # Add constant for intercept-only model
    
    try:
        model = OLS(y, X)
        results = model.fit()
        results_hac = results.get_robustcov_results(cov_type='HAC', maxlags=hac_lags)
        
        # Extract t-statistic
        t_stat = results_hac.tvalues[0]
        p_value = results_hac.pvalues[0]
        
    except Exception as e:
        print(f"    Warning: Could not compute Newey-West SE - {e}")
        # Fallback to standard SE
        std_error = slopes.std() / np.sqrt(len(slopes))
        t_stat = mean_slope / std_error
        p_value = None
    
    # Determine significance
    if abs(t_stat) >= 2.576:
        significance = "***"
        sig_level = "p<0.01"
    elif abs(t_stat) >= 1.96:
        significance = "**"
        sig_level = "p<0.05"
    elif abs(t_stat) >= 1.645:
        significance = "*"
        sig_level = "p<0.10"
    else:
        significance = ""
        sig_level = "not significant"
    
    # Average R²
    avg_r_squared = slopes_df['r_squared'].mean()
    
    # Average n_obs
    avg_n_obs = slopes_df['n_obs'].mean()
    
    return {
        'mean_slope': mean_slope,
        'std_slope': slopes.std(),
        't_stat': t_stat,
        'p_value': p_value,
        'significance': significance,
        'sig_level': sig_level,
        'avg_r_squared': avg_r_squared,
        'avg_n_obs': avg_n_obs,
        'n_periods': len(slopes)
    }


def print_fama_macbeth_summary(config_name, stats):
    """Print formatted summary of Fama-MacBeth results"""
    print(f"\n  {'─'*56}")
    print(f"  FAMA-MACBETH SUMMARY: {config_name.upper()}")
    print(f"  {'─'*56}")
    
    print(f"\n  📊 CROSS-SECTIONAL RELATIONSHIP:")
    print(f"     • Mean slope (b̄): {stats['mean_slope']:.6f}")
    print(f"     • T-statistic: {stats['t_stat']:.2f}{stats['significance']}")
    print(f"     • Significance: {stats['sig_level']}")
    
    if stats['t_stat'] > 1.645:
        print(f"     ✓ Sentiment signal has significant predictive power")
    else:
        print(f"     ⚠ No significant cross-sectional relationship detected")
    
    print(f"\n  📈 TIME-SERIES PROPERTIES:")
    print(f"     • Number of periods: {stats['n_periods']}")
    print(f"     • Std dev of slopes: {stats['std_slope']:.6f}")
    print(f"     • Average R²: {stats['avg_r_squared']:.3f}")
    print(f"     • Average N per period: {stats['avg_n_obs']:.0f}")
    
    print(f"\n  🔍 INTERPRETATION:")
    mean_slope = stats['mean_slope']
    
    if mean_slope > 0:
        print(f"     • Positive slope → Higher signal predicts higher forward returns")
        if abs(stats['t_stat']) >= 1.645:
            print(f"     ✓ Signal successfully ranks stocks by future performance")
        else:
            print(f"     ⚠ Relationship positive but not statistically reliable")
    else:
        print(f"     • Negative slope → Higher signal predicts lower forward returns")
        print(f"     ✗ Unexpected direction (signal may be inverted)")
    
    # Economic magnitude
    print(f"\n  💰 ECONOMIC MAGNITUDE:")
    print(f"     • 1-unit increase in signal → {mean_slope:+.4%} forward return")
    
    # Assuming signal ranges from -1 to +1, long-short spread
    spread = 2 * mean_slope  # Going from -1 to +1
    print(f"     • Long-short spread (signal=-1 to +1): {spread:+.4%}")
    
    print(f"  {'─'*56}\n")


def main():
    print(f"{'='*60}")
    print("FAMA-MACBETH CROSS-SECTIONAL ANALYSIS")
    print(f"{'='*60}\n")
    
    print("Note: This tests if sentiment signal predicts future returns")
    print("      at the cross-sectional level (across stocks).\n")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load data
    df = load_signal_return_panel()
    
    # Determine which signal column to use
    signal_cols = [col for col in df.columns if 'signal' in col.lower()]
    print(f"\nAvailable signal columns: {signal_cols}")
    
    # Prefer composite_signal, fallback to other signal columns
    if 'composite_signal' in df.columns:
        signal_col = 'composite_signal'
    elif 'weighted_sentiment_score' in df.columns:
        signal_col = 'weighted_sentiment_score'
    elif len(signal_cols) > 0:
        signal_col = signal_cols[0]
    else:
        raise ValueError("No signal column found in data")
    
    print(f"Using signal column: {signal_col}\n")
    
    # Run Fama-MacBeth for each configuration
    all_summaries = []
    
    for config_name, config in REBALANCE_CONFIGS.items():
        # Run Fama-MacBeth analysis
        slopes_df = fama_macbeth_analysis(
            df, 
            config_name, 
            freq=config['freq'],
            signal_col=signal_col
        )
        
        if slopes_df is None:
            continue
        
        # Save slope time-series
        slopes_file = os.path.join(OUTPUT_DIR, f"fmb_slopes_{config_name}.csv")
        slopes_df.to_csv(slopes_file, index=False)
        print(f"  ✓ Saved slope time-series to: {slopes_file}")
        
        # Compute summary statistics
        hac_lags = HAC_LAGS[config_name]
        stats = compute_fama_macbeth_statistics(slopes_df, hac_lags)
        stats['config'] = config_name
        
        # Print summary
        print_fama_macbeth_summary(config_name, stats)
        
        all_summaries.append(stats)
    
    # Create summary table
    summary_df = pd.DataFrame(all_summaries)
    summary_file = os.path.join(OUTPUT_DIR, "fmb_summary.csv")
    summary_df.to_csv(summary_file, index=False)
    
    print(f"\n✅ Saved Fama-MacBeth summary to: {summary_file}")
    
    # Print comparison table
    print(f"\n{'='*60}")
    print("COMPARISON ACROSS CONFIGURATIONS")
    print(f"{'='*60}\n")
    
    print(f"{'Config':<15} {'Mean Slope':<15} {'T-stat':<10} {'Sig':<8} {'Avg R²':<10}")
    print(f"{'-'*60}")
    for _, row in summary_df.iterrows():
        print(f"{row['config']:<15} {row['mean_slope']:>14.6f} {row['t_stat']:>9.2f}{row['significance']:<3} {row['avg_r_squared']:>9.3f}")
    
    print(f"\n{'='*60}")
    print("Significance: * p<0.10, ** p<0.05, *** p<0.01")
    print(f"{'='*60}\n")
    
    # Key takeaways
    print("\n🎯 KEY TAKEAWAYS:")
    
    significant_configs = summary_df[summary_df['t_stat'].abs() >= 1.645]
    
    if len(significant_configs) > 0:
        print(f"  ✓ {len(significant_configs)}/{len(summary_df)} configurations show significant predictive power")
        
        best_config = summary_df.loc[summary_df['t_stat'].abs().idxmax()]
        print(f"  ✓ Strongest signal: {best_config['config']} (t={best_config['t_stat']:.2f})")
    else:
        print(f"  ⚠ No configuration shows statistically significant cross-sectional predictability")
        print(f"  → Sentiment signal may work through other channels (e.g., momentum, volatility)")
    
    print(f"\n  💡 NEXT STEPS:")
    print(f"     1. Add control variables (momentum, size, volatility)")
    print(f"     2. Test subsample stability (early vs late months)")
    print(f"     3. Examine time-variation in slopes (are some periods stronger?)")
    print(f"     4. Compare to portfolio alpha results from Phase C\n")


if __name__ == "__main__":
    main()
