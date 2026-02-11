"""
create_visualizations.py

Creates comprehensive visualizations for the Campus Challenge report:
1. Portfolio performance (cumulative returns, drawdowns)
2. Factor model analysis (alpha comparison, R² evolution)
3. Fama-MacBeth results (slope time-series)
4. Summary comparison charts

Outputs: PNG files saved to ../results/Figures/
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# File paths (relative to project root)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, '..', '..')  # Go up to project root

PORTFOLIO_DIR = os.path.join(project_root, 'Statistics', 'Portfolio Returns')
FACTOR_DIR = os.path.join(project_root, 'Statistics', 'Factor_Models Statistics')
FAMA_MACBETH_DIR = os.path.join(project_root, 'Statistics', 'Fama_MacBeth Statistics')
OUTPUT_DIR = os.path.join(project_root, 'Figures and Tables', 'Figures')

# Portfolio configurations
CONFIGS = ['monthly_equal', 'monthly_value', 'weekly_equal', 'weekly_value']
CONFIG_LABELS = {
    'monthly_equal': 'Monthly Equal-Weighted',
    'monthly_value': 'Monthly Value-Weighted',
    'weekly_equal': 'Weekly Equal-Weighted',
    'weekly_value': 'Weekly Value-Weighted'
}

# Color scheme
COLORS = {
    'long': '#2E7D32',      # Green
    'short': '#C62828',     # Red
    'long_short': '#1565C0', # Blue
    'CAPM': '#FF6F00',      # Orange
    'FF3': '#6A1B9A',       # Purple
    'FF5': '#00838F'        # Teal
}


def ensure_output_dir():
    """Create output directory if it doesn't exist"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_portfolio_returns(config):
    """Load portfolio returns for a configuration"""
    file_path = os.path.join(PORTFOLIO_DIR, f"portfolio_returns_{config}.csv")
    df = pd.read_csv(file_path)
    df['return_date'] = pd.to_datetime(df['return_date'])
    df = df.set_index('return_date')
    return df


def calculate_cumulative_returns(returns_series):
    """Calculate cumulative returns from daily returns"""
    return (1 + returns_series).cumprod() - 1


def calculate_drawdown(cumulative_returns):
    """Calculate drawdown series"""
    cum_ret_series = 1 + cumulative_returns
    running_max = cum_ret_series.cummax()
    drawdown = (cum_ret_series - running_max) / running_max
    return drawdown


def calculate_rolling_sharpe(returns_series, window=20):
    """Calculate rolling Sharpe ratio (annualized)"""
    rolling_mean = returns_series.rolling(window).mean()
    rolling_std = returns_series.rolling(window).std()
    # Annualize: sqrt(252) for daily data
    rolling_sharpe = (rolling_mean / rolling_std) * np.sqrt(252)
    return rolling_sharpe


# ============================================================
# 1. PORTFOLIO PERFORMANCE VISUALIZATIONS
# ============================================================

def plot_cumulative_returns_single_config(config):
    """Plot cumulative returns for long, short, long-short for one config"""
    df = load_portfolio_returns(config)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Calculate cumulative returns
    for portfolio_type in ['long', 'short', 'long_short']:
        if portfolio_type in df.columns:
            cum_returns = calculate_cumulative_returns(df[portfolio_type])
            ax.plot(cum_returns.index, cum_returns * 100, 
                   label=portfolio_type.replace('_', '-').upper(),
                   linewidth=2, color=COLORS[portfolio_type])
    
    ax.set_title(f'Cumulative Returns - {CONFIG_LABELS[config]}', fontsize=14, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Cumulative Return (%)', fontsize=12)
    ax.legend(loc='best', frameon=True, shadow=True)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='black', linestyle='--', linewidth=0.8, alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f'cumulative_returns_{config}.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Created cumulative returns chart for {config}")


def plot_cumulative_returns_all_configs():
    """Plot long-short cumulative returns for all configs on one chart"""
    fig, ax = plt.subplots(figsize=(14, 7))
    
    config_colors = {
        'monthly_equal': '#E64A19',
        'monthly_value': '#F57C00', 
        'weekly_equal': '#1976D2',
        'weekly_value': '#0288D1'
    }
    
    for config in CONFIGS:
        df = load_portfolio_returns(config)
        if 'long_short' in df.columns:
            cum_returns = calculate_cumulative_returns(df['long_short'])
            ax.plot(cum_returns.index, cum_returns * 100,
                   label=CONFIG_LABELS[config],
                   linewidth=2.5, color=config_colors[config])
    
    ax.set_title('Long-Short Cumulative Returns - All Strategies', fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=13)
    ax.set_ylabel('Cumulative Return (%)', fontsize=13)
    ax.legend(loc='best', frameon=True, shadow=True, fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'cumulative_returns_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Created comparison chart for all configurations")


def plot_drawdown(config):
    """Plot drawdown chart for long-short portfolio"""
    df = load_portfolio_returns(config)
    
    if 'long_short' not in df.columns:
        return
    
    cum_returns = calculate_cumulative_returns(df['long_short'])
    drawdown = calculate_drawdown(cum_returns)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.fill_between(drawdown.index, drawdown * 100, 0, 
                    color=COLORS['long_short'], alpha=0.3)
    ax.plot(drawdown.index, drawdown * 100, 
           color=COLORS['long_short'], linewidth=2)
    
    # Mark maximum drawdown
    max_dd = drawdown.min()
    max_dd_date = drawdown.idxmin()
    ax.scatter([max_dd_date], [max_dd * 100], color='red', s=100, zorder=5, 
              label=f'Max Drawdown: {max_dd*100:.2f}%')
    
    ax.set_title(f'Drawdown - {CONFIG_LABELS[config]} Long-Short', fontsize=14, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Drawdown (%)', fontsize=12)
    ax.legend(loc='best', frameon=True, shadow=True)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f'drawdown_{config}.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Created drawdown chart for {config}")


def plot_rolling_sharpe(config, window=20):
    """Plot rolling Sharpe ratio"""
    df = load_portfolio_returns(config)
    
    if 'long_short' not in df.columns:
        return
    
    rolling_sharpe = calculate_rolling_sharpe(df['long_short'], window)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(rolling_sharpe.index, rolling_sharpe,
           color=COLORS['long_short'], linewidth=2)
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax.axhline(y=1, color='green', linestyle=':', linewidth=1, alpha=0.5, label='Sharpe = 1')
    
    ax.set_title(f'Rolling Sharpe Ratio ({window}-day) - {CONFIG_LABELS[config]} Long-Short', 
                fontsize=14, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Annualized Sharpe Ratio', fontsize=12)
    ax.legend(loc='best', frameon=True, shadow=True)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f'rolling_sharpe_{config}.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Created rolling Sharpe chart for {config}")


# ============================================================
# 2. FACTOR MODEL VISUALIZATIONS
# ============================================================

def plot_alpha_comparison():
    """Plot alpha comparison across models and configs"""
    # Load alpha summary
    summary_file = os.path.join(FACTOR_DIR, "alpha_summary.csv")
    df = pd.read_csv(summary_file)
    
    # Filter for long-short portfolios
    df = df[df['portfolio'] == 'long_short']
    
    # Pivot for plotting
    pivot_df = df.pivot(index='config', columns='model', values='alpha_annualized')
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    x = np.arange(len(pivot_df))
    width = 0.25
    
    models = ['CAPM', 'FF3', 'FF5']
    for i, model in enumerate(models):
        if model in pivot_df.columns:
            values = pivot_df[model] * 100  # Convert to percentage
            ax.bar(x + i*width, values, width, label=model, color=COLORS[model])
    
    # Add horizontal line at y=0
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
    
    # Formatting
    ax.set_xlabel('Configuration', fontsize=13, fontweight='bold')
    ax.set_ylabel('Annualized Alpha (%)', fontsize=13, fontweight='bold')
    ax.set_title('Alpha Estimates by Factor Model', fontsize=15, fontweight='bold')
    ax.set_xticks(x + width)
    ax.set_xticklabels([CONFIG_LABELS[cfg] for cfg in pivot_df.index], rotation=15, ha='right')
    ax.legend(title='Model', frameon=True, shadow=True)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'alpha_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Created alpha comparison chart")


def plot_r_squared_comparison():
    """Plot R² comparison across models"""
    summary_file = os.path.join(FACTOR_DIR, "alpha_summary.csv")
    df = pd.read_csv(summary_file)
    
    df = df[df['portfolio'] == 'long_short']
    pivot_df = df.pivot(index='config', columns='model', values='r_squared')
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    x = np.arange(len(pivot_df))
    width = 0.25
    
    models = ['CAPM', 'FF3', 'FF5']
    for i, model in enumerate(models):
        if model in pivot_df.columns:
            values = pivot_df[model] * 100
            ax.bar(x + i*width, values, width, label=model, color=COLORS[model])
    
    ax.set_xlabel('Configuration', fontsize=13, fontweight='bold')
    ax.set_ylabel('R² (%)', fontsize=13, fontweight='bold')
    ax.set_title('Model Explanatory Power (R²)', fontsize=15, fontweight='bold')
    ax.set_xticks(x + width)
    ax.set_xticklabels([CONFIG_LABELS[cfg] for cfg in pivot_df.index], rotation=15, ha='right')
    ax.legend(title='Model', frameon=True, shadow=True)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'r_squared_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Created R² comparison chart")


def plot_factor_exposures():
    """Plot factor exposures (betas) for FF5 model"""
    summary_file = os.path.join(FACTOR_DIR, "alpha_summary.csv")
    df = pd.read_csv(summary_file)
    
    # Filter for long-short portfolios and FF5 model
    df = df[(df['portfolio'] == 'long_short') & (df['model'] == 'FF5')]
    
    if len(df) == 0:
        return
    
    # Prepare data
    factors = ['beta_MKT', 'beta_SMB', 'beta_HML']
    factor_labels = ['Market', 'Size (SMB)', 'Value (HML)']
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    x = np.arange(len(df))
    width = 0.2
    
    for i, (factor, label) in enumerate(zip(factors, factor_labels)):
        if factor in df.columns:
            values = df[factor].values
            ax.bar(x + i*width, values, width, label=label)
    
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax.axhline(y=1, color='gray', linestyle='--', linewidth=0.8, alpha=0.5, label='β=1')
    
    ax.set_xlabel('Configuration', fontsize=13, fontweight='bold')
    ax.set_ylabel('Factor Loading (Beta)', fontsize=13, fontweight='bold')
    ax.set_title('Factor Exposures - FF5 Model', fontsize=15, fontweight='bold')
    ax.set_xticks(x + width)
    ax.set_xticklabels([CONFIG_LABELS[cfg] for cfg in df['config']], rotation=15, ha='right')
    ax.legend(frameon=True, shadow=True)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'factor_exposures.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Created factor exposures chart")


def plot_alpha_vs_transaction_costs():
    """Plot gross alpha vs net alpha after transaction costs"""
    tc_file = os.path.join(FACTOR_DIR, "net_alpha_after_costs.csv")
    
    if not os.path.exists(tc_file):
        print("  ⚠ Transaction cost file not found, skipping")
        return
    
    df = pd.read_csv(tc_file)
    
    # Filter for base case (20 bps) and FF5 model
    df = df[(df['cost_scenario'] == 'base') & (df['model'] == 'FF5')]
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    x = np.arange(len(df))
    width = 0.35
    
    ax.bar(x - width/2, df['gross_alpha_annual'] * 100, width, 
           label='Gross Alpha', color='#1976D2', alpha=0.8)
    ax.bar(x + width/2, df['net_alpha_annual'] * 100, width,
           label='Net Alpha (after 20 bps)', color='#388E3C', alpha=0.8)
    
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    
    ax.set_xlabel('Configuration', fontsize=13, fontweight='bold')
    ax.set_ylabel('Annualized Alpha (%)', fontsize=13, fontweight='bold')
    ax.set_title('Gross vs Net Alpha (After Transaction Costs)', fontsize=15, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([CONFIG_LABELS[cfg] for cfg in df['config']], rotation=15, ha='right')
    ax.legend(frameon=True, shadow=True)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for i, (gross, net) in enumerate(zip(df['gross_alpha_annual'] * 100, df['net_alpha_annual'] * 100)):
        ax.text(i - width/2, gross + 1, f'{gross:.1f}%', ha='center', va='bottom', fontsize=9)
        ax.text(i + width/2, net + 1, f'{net:.1f}%', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'gross_vs_net_alpha.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Created gross vs net alpha chart")


# ============================================================
# 3. FAMA-MACBETH VISUALIZATIONS
# ============================================================

def plot_fama_macbeth_slopes(config):
    """Plot time-series of Fama-MacBeth slopes"""
    slopes_file = os.path.join(FAMA_MACBETH_DIR, f"fmb_slopes_{config}.csv")
    
    if not os.path.exists(slopes_file):
        print(f"  ⚠ Slopes file not found for {config}")
        return
    
    df = pd.read_csv(slopes_file)
    df['date'] = pd.to_datetime(df['date'])
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Plot 1: Slope time-series
    ax1.plot(df['date'], df['slope'], marker='o', linewidth=2, 
            markersize=6, color='#1565C0', label='Cross-sectional slope')
    ax1.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax1.axhline(y=df['slope'].mean(), color='red', linestyle='-', linewidth=2, 
               alpha=0.7, label=f'Mean = {df["slope"].mean():.6f}')
    
    ax1.set_title(f'Fama-MacBeth Slopes Over Time - {config.upper()}', 
                 fontsize=14, fontweight='bold')
    ax1.set_xlabel('Period', fontsize=12)
    ax1.set_ylabel('Slope Coefficient', fontsize=12)
    ax1.legend(frameon=True, shadow=True)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: T-statistics
    ax2.bar(df['date'], df['t_stat'], color=['green' if t > 1.96 else 'lightcoral' for t in df['t_stat']], 
           alpha=0.7, edgecolor='black', linewidth=0.5)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax2.axhline(y=1.96, color='green', linestyle='--', linewidth=1, alpha=0.7, label='95% significance')
    ax2.axhline(y=-1.96, color='green', linestyle='--', linewidth=1, alpha=0.7)
    
    ax2.set_title('T-Statistics by Period', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Period', fontsize=12)
    ax2.set_ylabel('T-Statistic', fontsize=12)
    ax2.legend(frameon=True, shadow=True)
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f'fama_macbeth_slopes_{config}.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Created Fama-MacBeth slopes chart for {config}")


def plot_fama_macbeth_distribution(config):
    """Plot distribution of Fama-MacBeth slopes"""
    slopes_file = os.path.join(FAMA_MACBETH_DIR, f"fmb_slopes_{config}.csv")
    
    if not os.path.exists(slopes_file):
        return
    
    df = pd.read_csv(slopes_file)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Histogram
    n, bins, patches = ax.hist(df['slope'], bins=15, alpha=0.7, color='#1565C0', 
                               edgecolor='black', linewidth=1)
    
    # Add mean line
    mean_slope = df['slope'].mean()
    ax.axvline(x=mean_slope, color='red', linestyle='--', linewidth=2, 
              label=f'Mean = {mean_slope:.6f}')
    
    # Add zero line
    ax.axvline(x=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
    
    ax.set_xlabel('Slope Coefficient', fontsize=12, fontweight='bold')
    ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
    ax.set_title(f'Distribution of Cross-Sectional Slopes - {config.upper()}', 
                fontsize=14, fontweight='bold')
    ax.legend(frameon=True, shadow=True)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f'fama_macbeth_distribution_{config}.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Created Fama-MacBeth distribution chart for {config}")


def plot_fama_macbeth_comparison():
    """Compare Fama-MacBeth results across configurations"""
    summary_file = os.path.join(FAMA_MACBETH_DIR, "fmb_summary.csv")
    
    if not os.path.exists(summary_file):
        return
    
    df = pd.read_csv(summary_file)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Mean slopes
    colors = ['#1976D2' if t > 1.96 else '#F57C00' for t in df['t_stat']]
    ax1.bar(df['config'], df['mean_slope'], color=colors, alpha=0.8, edgecolor='black', linewidth=1)
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=1)
    
    # Add significance stars
    for i, (config, slope, sig) in enumerate(zip(df['config'], df['mean_slope'], df['significance'])):
        if sig:
            ax1.text(i, slope + 0.0001, sig, ha='center', va='bottom', fontsize=14, fontweight='bold')
    
    ax1.set_xlabel('Configuration', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Mean Slope Coefficient', fontsize=12, fontweight='bold')
    ax1.set_title('Average Predictive Power', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Plot 2: T-statistics
    ax2.bar(df['config'], df['t_stat'], color=['green' if t > 1.96 else 'orange' for t in df['t_stat']], 
           alpha=0.8, edgecolor='black', linewidth=1)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax2.axhline(y=1.96, color='green', linestyle='--', linewidth=1, alpha=0.7, label='5% significance')
    ax2.axhline(y=2.576, color='darkgreen', linestyle='--', linewidth=1, alpha=0.7, label='1% significance')
    
    ax2.set_xlabel('Configuration', fontsize=12, fontweight='bold')
    ax2.set_ylabel('T-Statistic', fontsize=12, fontweight='bold')
    ax2.set_title('Statistical Significance', fontsize=13, fontweight='bold')
    ax2.legend(frameon=True, shadow=True)
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fama_macbeth_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Created Fama-MacBeth comparison chart")


# ============================================================
# 4. SUMMARY VISUALIZATIONS
# ============================================================

def plot_performance_summary():
    """Create a comprehensive performance summary table/chart"""
    summary_file = os.path.join(PORTFOLIO_DIR, "portfolio_summary_monthly_value.csv")
    
    # Load summaries for all configs
    summaries = []
    for config in CONFIGS:
        file_path = os.path.join(PORTFOLIO_DIR, f"portfolio_summary_{config}.csv")
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df['config'] = config
            summaries.append(df)
    
    if not summaries:
        return
    
    all_summaries = pd.concat(summaries, ignore_index=True)
    
    # Filter for long-short
    ls_summary = all_summaries[all_summaries['portfolio'] == 'long_short']
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot 1: Total Returns
    ax1.bar(ls_summary['config'], ls_summary['total_return'] * 100, 
           color='#1565C0', alpha=0.8, edgecolor='black', linewidth=1)
    ax1.set_ylabel('Total Return (%)', fontsize=11, fontweight='bold')
    ax1.set_title('Total Returns', fontsize=12, fontweight='bold')
    ax1.set_xticklabels([CONFIG_LABELS[cfg] for cfg in ls_summary['config']], rotation=15, ha='right')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Plot 2: Sharpe Ratios
    ax2.bar(ls_summary['config'], ls_summary['sharpe_ratio'],
           color='#388E3C', alpha=0.8, edgecolor='black', linewidth=1)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax2.set_ylabel('Sharpe Ratio', fontsize=11, fontweight='bold')
    ax2.set_title('Risk-Adjusted Returns', fontsize=12, fontweight='bold')
    ax2.set_xticklabels([CONFIG_LABELS[cfg] for cfg in ls_summary['config']], rotation=15, ha='right')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Plot 3: Volatility
    ax3.bar(ls_summary['config'], ls_summary['volatility'] * 100,
           color='#F57C00', alpha=0.8, edgecolor='black', linewidth=1)
    ax3.set_ylabel('Volatility (%)', fontsize=11, fontweight='bold')
    ax3.set_title('Annualized Volatility', fontsize=12, fontweight='bold')
    ax3.set_xticklabels([CONFIG_LABELS[cfg] for cfg in ls_summary['config']], rotation=15, ha='right')
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Plot 4: Maximum Drawdown
    ax4.bar(ls_summary['config'], ls_summary['max_drawdown'] * 100,
           color='#D32F2F', alpha=0.8, edgecolor='black', linewidth=1)
    ax4.set_ylabel('Max Drawdown (%)', fontsize=11, fontweight='bold')
    ax4.set_title('Maximum Drawdown', fontsize=12, fontweight='bold')
    ax4.set_xticklabels([CONFIG_LABELS[cfg] for cfg in ls_summary['config']], rotation=15, ha='right')
    ax4.grid(True, alpha=0.3, axis='y')
    
    plt.suptitle('Portfolio Performance Summary - Long-Short Strategies', 
                fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'performance_summary.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Created performance summary chart")


def create_results_dashboard():
    """Create a comprehensive dashboard with key results"""
    # Load key metrics
    factor_summary = pd.read_csv(os.path.join(FACTOR_DIR, "alpha_summary.csv"))
    fmb_summary = pd.read_csv(os.path.join(FAMA_MACBETH_DIR, "fmb_summary.csv"))
    
    factor_ls = factor_summary[(factor_summary['portfolio'] == 'long_short') & 
                               (factor_summary['model'] == 'FF5')]
    
    fig = plt.figure(figsize=(18, 10))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # Title
    fig.suptitle('Sentiment Signal Analysis - Key Results Dashboard', 
                fontsize=18, fontweight='bold', y=0.98)
    
    # Panel 1: Alpha by config (FF5)
    ax1 = fig.add_subplot(gs[0, :2])
    x1 = np.arange(len(factor_ls))
    bars1 = ax1.bar(x1, factor_ls['alpha_annualized'] * 100, 
                   color=['green' if a > 0 else 'red' for a in factor_ls['alpha_annualized']], 
                   alpha=0.7, edgecolor='black', linewidth=1.5)
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax1.set_ylabel('Alpha (%)', fontsize=11, fontweight='bold')
    ax1.set_title('Factor Model Alpha (FF5)', fontsize=13, fontweight='bold')
    ax1.set_xticks(x1)
    ax1.set_xticklabels([CONFIG_LABELS[cfg] for cfg in factor_ls['config']], rotation=15, ha='right')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Add significance stars
    for i, (alpha, sig) in enumerate(zip(factor_ls['alpha_annualized'] * 100, factor_ls['significance'])):
        if sig:
            ax1.text(i, alpha + 2, sig, ha='center', va='bottom', fontsize=14, fontweight='bold')
    
    # Panel 2: Key statistics table
    ax2 = fig.add_subplot(gs[0, 2])
    ax2.axis('off')
    
    best_config = factor_ls.loc[factor_ls['alpha_annualized'].idxmax()]
    best_fmb = fmb_summary.loc[fmb_summary['t_stat'].idxmax()]
    
    stats_text = f"""
    📊 KEY FINDINGS
    ───────────────────
    
    Best Alpha Strategy:
    {CONFIG_LABELS[best_config['config']]}
    α = {best_config['alpha_annualized']*100:.2f}%
    t = {best_config['alpha_tstat']:.2f}{best_config['significance']}
    
    Best FM Predictability:
    {best_fmb['config'].upper()}
    slope = {best_fmb['mean_slope']:.6f}
    t = {best_fmb['t_stat']:.2f}{best_fmb['significance']}
    
    R² Range:
    {factor_ls['r_squared'].min():.1%} - {factor_ls['r_squared'].max():.1%}
    """
    
    ax2.text(0.1, 0.5, stats_text, fontsize=11, verticalalignment='center',
            family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    # Panel 3: Fama-MacBeth t-stats
    ax3 = fig.add_subplot(gs[1, :])
    x3 = np.arange(len(fmb_summary))
    bars3 = ax3.bar(x3, fmb_summary['t_stat'],
                   color=['darkgreen' if t > 2.576 else 'green' if t > 1.96 else 'orange' 
                         for t in fmb_summary['t_stat']], 
                   alpha=0.7, edgecolor='black', linewidth=1.5)
    ax3.axhline(y=1.96, color='green', linestyle='--', linewidth=1.5, alpha=0.7, label='5% sig')
    ax3.axhline(y=2.576, color='darkgreen', linestyle='--', linewidth=1.5, alpha=0.7, label='1% sig')
    ax3.set_ylabel('T-Statistic', fontsize=11, fontweight='bold')
    ax3.set_title('Fama-MacBeth Cross-Sectional Predictability', fontsize=13, fontweight='bold')
    ax3.set_xticks(x3)
    ax3.set_xticklabels([c.upper() for c in fmb_summary['config']])
    ax3.legend(frameon=True, shadow=True)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Panel 4: R² comparison
    ax4 = fig.add_subplot(gs[2, 0])
    models_data = factor_summary[(factor_summary['portfolio'] == 'long_short') & 
                                 (factor_summary['config'] == 'weekly_value')]
    ax4.bar(['CAPM', 'FF3', 'FF5'], models_data['r_squared'] * 100,
           color=[COLORS['CAPM'], COLORS['FF3'], COLORS['FF5']], alpha=0.7)
    ax4.set_ylabel('R² (%)', fontsize=10, fontweight='bold')
    ax4.set_title('Model Fit\n(Weekly Value)', fontsize=11, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')
    
    # Panel 5: Alpha stability
    ax5 = fig.add_subplot(gs[2, 1])
    wv_data = factor_summary[(factor_summary['portfolio'] == 'long_short') & 
                             (factor_summary['config'] == 'weekly_value')]
    ax5.plot(['CAPM', 'FF3', 'FF5'], wv_data['alpha_annualized'] * 100,
            marker='o', linewidth=2.5, markersize=10, color='#1565C0')
    ax5.set_ylabel('Alpha (%)', fontsize=10, fontweight='bold')
    ax5.set_title('Alpha Stability\n(Weekly Value)', fontsize=11, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    
    # Panel 6: Economic magnitude
    ax6 = fig.add_subplot(gs[2, 2])
    spread_data = fmb_summary['mean_slope'] * 2 * 100  # Long-short spread in %
    ax6.bar(fmb_summary['config'], spread_data,
           color='#F57C00', alpha=0.7, edgecolor='black', linewidth=1.5)
    ax6.set_ylabel('L-S Spread (%)', fontsize=10, fontweight='bold')
    ax6.set_title('Economic Magnitude\n(FM Implied)', fontsize=11, fontweight='bold')
    ax6.grid(True, alpha=0.3, axis='y')
    
    plt.savefig(os.path.join(OUTPUT_DIR, 'results_dashboard.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Created results dashboard")


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    print("\n" + "="*60)
    print("CREATING VISUALIZATIONS FOR CAMPUS CHALLENGE")
    print("="*60 + "\n")
    
    ensure_output_dir()
    
    # 1. Portfolio Performance Charts
    print("📊 Creating portfolio performance charts...")
    for config in CONFIGS:
        plot_cumulative_returns_single_config(config)
        plot_drawdown(config)
        plot_rolling_sharpe(config)
    
    plot_cumulative_returns_all_configs()
    plot_performance_summary()
    
    # 2. Factor Model Charts
    print("\n📈 Creating factor model charts...")
    plot_alpha_comparison()
    plot_r_squared_comparison()
    plot_factor_exposures()
    plot_alpha_vs_transaction_costs()
    
    # 3. Fama-MacBeth Charts
    print("\n🔍 Creating Fama-MacBeth charts...")
    for config in ['monthly', 'weekly']:
        plot_fama_macbeth_slopes(config)
        plot_fama_macbeth_distribution(config)
    
    plot_fama_macbeth_comparison()
    
    # 4. Summary Dashboard
    print("\n🎯 Creating summary dashboard...")
    create_results_dashboard()
    
    print(f"\n{'='*60}")
    print("✅ ALL VISUALIZATIONS CREATED SUCCESSFULLY!")
    print(f"{'='*60}")
    print(f"\nFigures saved to: {OUTPUT_DIR}")
    print("\nGenerated files:")
    
    # List all created files
    for file in sorted(os.listdir(OUTPUT_DIR)):
        if file.endswith('.png'):
            print(f"  • {file}")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
