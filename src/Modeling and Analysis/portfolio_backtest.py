"""
portfolio_backtest.py

Constructs and backtests Long and Long-Short portfolios based on sentiment signals.

Supports multiple configurations:
- Rebalance frequency: Monthly and Weekly
- Weighting schemes: Equal-weight and Value-weight (using MV_USD_lag)
- Long/Short buckets: Top/Bottom 20% (configurable)
- Minimum tickers per rebalance: 20 (configurable)

Outputs:
- Daily portfolio return series for Long, Short, and Long-Short portfolios
- Summary statistics: 2024 return, volatility, Sharpe ratio, turnover
- Results saved to ../results/Portfolio/
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

# File paths (relative to project root)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, '..', '..')  # Go up to project root

PANEL_FILE = os.path.join(project_root, 'data', 'signal_return_panel_cleaned(2).csv')
OUTPUT_DIR = os.path.join(project_root, 'Statistics', 'Portfolio Returns')

# Portfolio configuration
LONG_PERCENTILE = 80  # Top 20% for long
SHORT_PERCENTILE = 20  # Bottom 20% for short
MIN_TICKERS_PER_REBALANCE = 20  # Minimum stocks needed for portfolio formation
RISK_FREE_RATE = 0.0  # Annual risk-free rate (0% for now; update if you get RF data)

# Configurations to run (will loop through these)
REBALANCE_FREQUENCIES = ['monthly', 'weekly']
WEIGHTING_SCHEMES = ['equal', 'value']


def load_panel():
    """Load the cleaned signal-return panel"""
    print("Loading cleaned signal-return panel...")
    df = pd.read_csv(PANEL_FILE)
    
    # Convert dates
    df['signal_date'] = pd.to_datetime(df['signal_date'])
    df['return_date'] = pd.to_datetime(df['return_date'])
    
    print(f"  Records: {len(df):,}")
    print(f"  Tickers: {df['Ticker'].nunique()}")
    print(f"  Date range: {df['signal_date'].min()} to {df['signal_date'].max()}")
    
    return df


def aggregate_signals(df, frequency='monthly'):
    """
    Aggregate daily signals to the rebalance frequency.
    
    For each ticker and rebalance period, compute mean signal score.
    
    Args:
        df: panel with daily signals
        frequency: 'monthly' or 'weekly'
    
    Returns:
        DataFrame with aggregated signals per (ticker, rebalance_period)
    """
    print(f"\nAggregating signals to {frequency} frequency...")
    
    if frequency == 'monthly':
        # Use end-of-month as rebalance date
        df['rebalance_period'] = df['signal_date'].dt.to_period('M').dt.to_timestamp('M')
    elif frequency == 'weekly':
        # Use end-of-week (Friday) as rebalance date
        df['rebalance_period'] = df['signal_date'].dt.to_period('W').dt.to_timestamp('W')
    else:
        raise ValueError(f"Unsupported frequency: {frequency}")
    
    # Aggregate: mean signal score per (ticker, rebalance_period)
    # Also keep the most recent MV_USD_lag for value-weighting
    agg_signals = df.groupby(['Ticker', 'rebalance_period']).agg({
        'signal_score': 'mean',
        'MV_USD_lag': 'last'  # Use most recent market cap in the period
    }).reset_index()
    
    print(f"  Rebalance periods: {agg_signals['rebalance_period'].nunique()}")
    print(f"  Total (ticker, period) pairs: {len(agg_signals)}")
    
    return agg_signals


def form_portfolios(agg_signals, long_pct, short_pct, min_tickers):
    """
    Form long and short portfolios for each rebalance date.
    
    Args:
        agg_signals: aggregated signals with (Ticker, rebalance_period, signal_score, MV_USD_lag)
        long_pct: percentile threshold for long bucket (e.g., 80 = top 20%)
        short_pct: percentile threshold for short bucket (e.g., 20 = bottom 20%)
        min_tickers: minimum number of tickers needed for portfolio formation
    
    Returns:
        DataFrame with (rebalance_period, Ticker, position, signal_score, MV_USD_lag)
        where position is 'long' or 'short'
    """
    print(f"\nForming portfolios (top {100-long_pct:.0f}% long, bottom {short_pct:.0f}% short)...")
    
    portfolio_members = []
    skipped_periods = 0
    
    for period in agg_signals['rebalance_period'].unique():
        period_data = agg_signals[agg_signals['rebalance_period'] == period].copy()
        
        # Check minimum ticker requirement
        if len(period_data) < min_tickers:
            skipped_periods += 1
            continue
        
        # Rank by signal score
        period_data['rank_pct'] = period_data['signal_score'].rank(pct=True) * 100
        
        # Long: top percentile
        long_members = period_data[period_data['rank_pct'] >= long_pct].copy()
        long_members['position'] = 'long'
        
        # Short: bottom percentile
        short_members = period_data[period_data['rank_pct'] <= short_pct].copy()
        short_members['position'] = 'short'
        
        portfolio_members.append(long_members)
        portfolio_members.append(short_members)
    
    portfolio_df = pd.concat(portfolio_members, ignore_index=True)
    
    print(f"  Valid rebalance periods: {portfolio_df['rebalance_period'].nunique()}")
    print(f"  Skipped periods (< {min_tickers} tickers): {skipped_periods}")
    print(f"  Total portfolio memberships: {len(portfolio_df)}")
    
    # Statistics per period
    stats = portfolio_df.groupby(['rebalance_period', 'position']).size().unstack(fill_value=0)
    print(f"\n  Average tickers per position:")
    print(f"    Long:  {stats['long'].mean():.1f}")
    print(f"    Short: {stats['short'].mean():.1f}")
    
    return portfolio_df


def assign_weights(portfolio_df, weighting='equal'):
    """
    Assign portfolio weights to each member.
    
    Args:
        portfolio_df: portfolio members with positions
        weighting: 'equal' or 'value' (value-weighted by MV_USD_lag)
    
    Returns:
        portfolio_df with added 'weight' column
    """
    print(f"\nAssigning {weighting}-weights...")
    
    if weighting == 'equal':
        # Equal weight within each (rebalance_period, position) group
        portfolio_df['weight'] = 1.0 / portfolio_df.groupby(['rebalance_period', 'position'])['Ticker'].transform('count')
    
    elif weighting == 'value':
        # Value-weight by MV_USD_lag within each (rebalance_period, position) group
        portfolio_df['weight'] = (
            portfolio_df['MV_USD_lag'] / 
            portfolio_df.groupby(['rebalance_period', 'position'])['MV_USD_lag'].transform('sum')
        )
    
    else:
        raise ValueError(f"Unsupported weighting: {weighting}")
    
    # Verify weights sum to 1 within each group
    weight_sums = portfolio_df.groupby(['rebalance_period', 'position'])['weight'].sum()
    assert np.allclose(weight_sums, 1.0), "Weights do not sum to 1 within groups!"
    
    print(f"  Weights assigned successfully")
    print(f"  Sample weights (first period):")
    sample = portfolio_df[portfolio_df['rebalance_period'] == portfolio_df['rebalance_period'].min()].head(5)
    print(sample[['Ticker', 'position', 'weight', 'signal_score']])
    
    return portfolio_df


def compute_portfolio_returns(portfolio_df, returns_df):
    """
    Compute daily portfolio returns by applying weights to constituent returns.
    
    Args:
        portfolio_df: portfolio members with weights and rebalance dates
        returns_df: original panel with daily returns
    
    Returns:
        DataFrame with daily returns for Long, Short, and Long-Short portfolios
    """
    print(f"\nComputing daily portfolio returns...")
    
    # Merge portfolio weights with daily return data
    # For each rebalance period, weights are held constant until next rebalance
    
    # Create a mapping of (Ticker, rebalance_period) -> weight and position
    portfolio_weights = portfolio_df[['Ticker', 'rebalance_period', 'position', 'weight']].copy()
    
    # For daily returns, we need to know which rebalance period each return_date belongs to
    # Map each return_date to the most recent rebalance_period
    
    # Get all rebalance dates
    rebalance_dates = sorted(portfolio_df['rebalance_period'].unique())
    
    # For each return in the panel, find which rebalance period it belongs to
    returns_with_weights = []
    
    for ticker in returns_df['Ticker'].unique():
        ticker_returns = returns_df[returns_df['Ticker'] == ticker].copy()
        ticker_weights = portfolio_weights[portfolio_weights['Ticker'] == ticker].copy()
        
        if len(ticker_weights) == 0:
            continue  # Ticker never in portfolio
        
        # For each return_date, find the applicable rebalance_period
        # (most recent rebalance_period <= return_date)
        for idx, row in ticker_returns.iterrows():
            return_date = row['return_date']
            
            # Find the rebalance period this return belongs to
            applicable_rebalances = [rb for rb in rebalance_dates if rb <= return_date]
            
            if len(applicable_rebalances) == 0:
                continue  # Return is before first rebalance
            
            current_rebalance = applicable_rebalances[-1]  # Most recent rebalance
            
            # Get weight for this ticker in this rebalance period
            ticker_weight_row = ticker_weights[ticker_weights['rebalance_period'] == current_rebalance]
            
            if len(ticker_weight_row) == 0:
                continue  # Ticker not in portfolio for this period
            
            returns_with_weights.append({
                'return_date': return_date,
                'Ticker': ticker,
                'RET': row['RET'],
                'position': ticker_weight_row.iloc[0]['position'],
                'weight': ticker_weight_row.iloc[0]['weight'],
                'rebalance_period': current_rebalance
            })
    
    weighted_returns = pd.DataFrame(returns_with_weights)
    
    print(f"  Weighted return observations: {len(weighted_returns)}")
    
    # Compute portfolio returns for each date and position
    # Portfolio return = sum of (weight * return) for all constituents
    daily_portfolio_returns = weighted_returns.groupby(['return_date', 'position']).apply(
        lambda x: (x['weight'] * x['RET']).sum()
    ).reset_index(name='portfolio_return')
    
    # Pivot to have Long and Short as columns
    daily_returns_wide = daily_portfolio_returns.pivot(
        index='return_date', 
        columns='position', 
        values='portfolio_return'
    ).reset_index()
    
    # Compute Long-Short return
    daily_returns_wide['long_short'] = daily_returns_wide['long'] - daily_returns_wide['short']
    
    # Fill any missing dates with 0 (days where portfolio had no returns)
    daily_returns_wide = daily_returns_wide.fillna(0)
    
    print(f"  Daily return series length: {len(daily_returns_wide)}")
    print(f"  Date range: {daily_returns_wide['return_date'].min()} to {daily_returns_wide['return_date'].max()}")
    
    return daily_returns_wide


def calculate_performance_metrics(daily_returns, rf_annual=0.0):
    """
    Calculate performance metrics for portfolio return series.
    
    Args:
        daily_returns: DataFrame with columns ['return_date', 'long', 'short', 'long_short']
        rf_annual: annual risk-free rate
    
    Returns:
        Dictionary with performance metrics
    """
    print(f"\nCalculating performance metrics...")
    
    # Daily risk-free rate (simple approximation)
    rf_daily = rf_annual / 252
    
    metrics = {}
    
    for col in ['long', 'short', 'long_short']:
        returns = daily_returns[col]
        
        # Total return (compounded)
        total_return = (1 + returns).prod() - 1
        
        # Annualized return (geometric mean)
        n_days = len(returns)
        annualized_return = (1 + total_return) ** (252 / n_days) - 1
        
        # Volatility (annualized)
        volatility = returns.std() * np.sqrt(252)
        
        # Sharpe ratio (using excess returns)
        excess_returns = returns - rf_daily
        sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0
        
        # Max drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        metrics[col] = {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'mean_daily_return': returns.mean(),
            'n_days': n_days
        }
    
    return metrics


def calculate_turnover(portfolio_df):
    """
    Calculate portfolio turnover (average across rebalance dates).
    
    Turnover = sum of absolute weight changes / 2
    
    Args:
        portfolio_df: portfolio members with weights and rebalance dates
    
    Returns:
        float: average turnover per rebalance
    """
    print(f"\nCalculating turnover...")
    
    rebalance_dates = sorted(portfolio_df['rebalance_period'].unique())
    
    turnovers = []
    
    for i in range(1, len(rebalance_dates)):
        prev_date = rebalance_dates[i-1]
        curr_date = rebalance_dates[i]
        
        for position in ['long', 'short']:
            prev_portfolio = portfolio_df[
                (portfolio_df['rebalance_period'] == prev_date) & 
                (portfolio_df['position'] == position)
            ][['Ticker', 'weight']].set_index('Ticker')
            
            curr_portfolio = portfolio_df[
                (portfolio_df['rebalance_period'] == curr_date) & 
                (portfolio_df['position'] == position)
            ][['Ticker', 'weight']].set_index('Ticker')
            
            # Align and compute weight changes
            all_tickers = set(prev_portfolio.index).union(set(curr_portfolio.index))
            
            weight_changes = 0.0
            for ticker in all_tickers:
                prev_weight = prev_portfolio.loc[ticker, 'weight'] if ticker in prev_portfolio.index else 0.0
                curr_weight = curr_portfolio.loc[ticker, 'weight'] if ticker in curr_portfolio.index else 0.0
                weight_changes += abs(curr_weight - prev_weight)
            
            # Turnover = sum of absolute weight changes / 2
            turnover = weight_changes / 2
            turnovers.append(turnover)
    
    avg_turnover = np.mean(turnovers) if len(turnovers) > 0 else 0.0
    
    print(f"  Average turnover per rebalance: {avg_turnover:.2%}")
    
    return avg_turnover


def run_backtest(frequency, weighting):
    """
    Run a complete backtest for a specific configuration.
    
    Args:
        frequency: 'monthly' or 'weekly'
        weighting: 'equal' or 'value'
    
    Returns:
        tuple: (daily_returns, metrics, turnover)
    """
    print(f"\n{'='*60}")
    print(f"RUNNING BACKTEST: {frequency.upper()} / {weighting.upper()}-WEIGHT")
    print(f"{'='*60}")
    
    # Load panel
    panel_df = load_panel()
    
    # Aggregate signals
    agg_signals = aggregate_signals(panel_df, frequency=frequency)
    
    # Form portfolios
    portfolio_df = form_portfolios(
        agg_signals, 
        long_pct=LONG_PERCENTILE, 
        short_pct=SHORT_PERCENTILE,
        min_tickers=MIN_TICKERS_PER_REBALANCE
    )
    
    # Assign weights
    portfolio_df = assign_weights(portfolio_df, weighting=weighting)
    
    # Compute portfolio returns
    daily_returns = compute_portfolio_returns(portfolio_df, panel_df)
    
    # Calculate performance metrics
    metrics = calculate_performance_metrics(daily_returns, rf_annual=RISK_FREE_RATE)
    
    # Calculate turnover
    turnover = calculate_turnover(portfolio_df)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"PERFORMANCE SUMMARY: {frequency.upper()} / {weighting.upper()}-WEIGHT")
    print(f"{'='*60}")
    for portfolio_type in ['long', 'short', 'long_short']:
        m = metrics[portfolio_type]
        print(f"\n{portfolio_type.upper()} Portfolio:")
        print(f"  Total Return (2024):     {m['total_return']:>8.2%}")
        print(f"  Annualized Return:       {m['annualized_return']:>8.2%}")
        print(f"  Annualized Volatility:   {m['volatility']:>8.2%}")
        print(f"  Sharpe Ratio (rf={RISK_FREE_RATE:.1%}): {m['sharpe_ratio']:>8.2f}")
        print(f"  Max Drawdown:            {m['max_drawdown']:>8.2%}")
    
    print(f"\nAverage Turnover per Rebalance: {turnover:.2%}")
    
    return daily_returns, metrics, turnover, portfolio_df


def save_results(frequency, weighting, daily_returns, metrics, turnover):
    """Save backtest results to files"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    config_name = f"{frequency}_{weighting}"
    
    # Save daily returns
    returns_file = os.path.join(OUTPUT_DIR, f"portfolio_returns_{config_name}.csv")
    daily_returns.to_csv(returns_file, index=False)
    print(f"\n  Saved daily returns to: {returns_file}")
    
    # Save summary metrics
    summary_rows = []
    for portfolio_type in ['long', 'short', 'long_short']:
        m = metrics[portfolio_type]
        summary_rows.append({
            'portfolio': portfolio_type,
            'frequency': frequency,
            'weighting': weighting,
            'total_return': m['total_return'],
            'annualized_return': m['annualized_return'],
            'volatility': m['volatility'],
            'sharpe_ratio': m['sharpe_ratio'],
            'max_drawdown': m['max_drawdown'],
            'mean_daily_return': m['mean_daily_return'],
            'n_days': m['n_days'],
            'avg_turnover': turnover
        })
    
    summary_df = pd.DataFrame(summary_rows)
    summary_file = os.path.join(OUTPUT_DIR, f"portfolio_summary_{config_name}.csv")
    summary_df.to_csv(summary_file, index=False)
    print(f"  Saved summary metrics to: {summary_file}")


def main():
    print(f"{'='*60}")
    print("PORTFOLIO BACKTEST - MULTIPLE CONFIGURATIONS")
    print(f"{'='*60}")
    print(f"\nConfigurations to run:")
    print(f"  Frequencies: {REBALANCE_FREQUENCIES}")
    print(f"  Weightings: {WEIGHTING_SCHEMES}")
    print(f"  Total backtests: {len(REBALANCE_FREQUENCIES) * len(WEIGHTING_SCHEMES)}")
    
    # Run all configurations
    all_results = {}
    
    for freq in REBALANCE_FREQUENCIES:
        for weight in WEIGHTING_SCHEMES:
            config_name = f"{freq}_{weight}"
            
            try:
                daily_returns, metrics, turnover, portfolio_df = run_backtest(freq, weight)
                save_results(freq, weight, daily_returns, metrics, turnover)
                
                all_results[config_name] = {
                    'daily_returns': daily_returns,
                    'metrics': metrics,
                    'turnover': turnover
                }
                
            except Exception as e:
                print(f"\n⚠️  Error running {config_name}: {e}")
                continue
    
    # Create comparison summary
    print(f"\n{'='*60}")
    print("CROSS-CONFIGURATION COMPARISON")
    print(f"{'='*60}")
    
    comparison_rows = []
    for config_name, results in all_results.items():
        freq, weight = config_name.split('_')
        ls_metrics = results['metrics']['long_short']
        
        comparison_rows.append({
            'configuration': config_name,
            'frequency': freq,
            'weighting': weight,
            'LS_total_return': ls_metrics['total_return'],
            'LS_annualized_return': ls_metrics['annualized_return'],
            'LS_volatility': ls_metrics['volatility'],
            'LS_sharpe_ratio': ls_metrics['sharpe_ratio'],
            'LS_max_drawdown': ls_metrics['max_drawdown'],
            'avg_turnover': results['turnover']
        })
    
    comparison_df = pd.DataFrame(comparison_rows)
    comparison_file = os.path.join(OUTPUT_DIR, "portfolio_comparison_all_configs.csv")
    comparison_df.to_csv(comparison_file, index=False)
    
    print("\nLong-Short Portfolio Comparison:")
    print(comparison_df.to_string(index=False))
    print(f"\n  Saved comparison to: {comparison_file}")
    
    print(f"\n{'='*60}")
    print("BACKTEST COMPLETE")
    print(f"{'='*60}")
    print(f"All results saved to: {OUTPUT_DIR}/")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
