"""
factor_alpha.py

Performs factor model regressions (CAPM, FF3, FF5) on portfolio returns to estimate alpha.

Uses Fama-French factor data from Kenneth French's data library.
Applies Newey-West (HAC) standard errors for robust inference.

Inputs:
- Portfolio return series from portfolio_backtest.py (../Portfolio/)
- Fama-French factor data (./Fama_French/)

Outputs:
- Alpha tables for all portfolios and models
- Saved to ../results/Factor Models/
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS
import os
import warnings

warnings.filterwarnings('ignore')

# File paths
PORTFOLIO_DIR = "../Portfolio"
FACTOR_DIR = "./Fama_French"
OUTPUT_DIR = "../results/Factor_Models"

# Factor data files (downloaded from Kenneth French's data library)
FACTOR_FILES = {
    'daily_3': 'F-F_Research_Data_Factors_daily.csv',
    'daily_5': 'F-F_Research_Data_5_Factors_2x3_daily.csv',
    'monthly_3': 'F-F_Research_Data_Factors.csv',
    'monthly_5': 'F-F_Research_Data_5_Factors_2x3.csv'
}

# Portfolio configurations
CONFIGS = ['monthly_equal', 'monthly_value', 'weekly_equal', 'weekly_value']
PORTFOLIO_TYPES = ['long', 'short', 'long_short']

# Newey-West lag selection
HAC_LAGS = {
    'daily': 10,   # ~2 weeks of autocorrelation
    'monthly': 3   # ~3 months of autocorrelation
}


def load_fama_french_factors(file_path, frequency='daily'):
    """
    Load Fama-French factor data from Kenneth French's data library format.
    
    The CSV files have a specific format:
    - Header rows to skip
    - Dates in YYYYMMDD format (daily) or YYYYMM (monthly)
    - Values in percentage (need to divide by 100)
    
    Args:
        file_path: path to CSV file
        frequency: 'daily' or 'monthly'
    
    Returns:
        DataFrame with date index and factor columns (in decimal format)
    """
    print(f"  Loading {os.path.basename(file_path)}...")
    
    # Read the file, skipping header rows (usually first few rows are description)
    # The actual data starts after a blank line
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Find the line where column headers are (look for 'Mkt-RF')
    header_line = None
    for i, line in enumerate(lines):
        if 'Mkt-RF' in line:
            header_line = i
            break
    
    if header_line is None:
        raise ValueError(f"Could not find header line with 'Mkt-RF' in {file_path}")
    
    # Find where data ends (look for blank line or copyright text)
    data_end = None
    for i in range(header_line + 1, len(lines)):
        line = lines[i].strip()
        if not line or 'Copyright' in line or not lines[i].split(',')[0].strip().replace('.', '').isdigit():
            data_end = i
            break
    
    # Read from header line
    if data_end:
        df = pd.read_csv(file_path, skiprows=header_line, nrows=data_end - header_line - 1)
    else:
        df = pd.read_csv(file_path, skiprows=header_line)
    
    # First column is date (unnamed or called 'Unnamed: 0')
    date_col = df.columns[0]
    
    # Convert date format
    if frequency == 'daily':
        # YYYYMMDD format
        df['date'] = pd.to_datetime(df[date_col].astype(str).str.strip(), format='%Y%m%d')
    else:
        # YYYYMM format  
        df['date'] = pd.to_datetime(df[date_col].astype(str).str.strip(), format='%Y%m')
    
    df = df.set_index('date')
    df = df.drop(columns=[date_col])
    
    # Strip whitespace from column names and convert to numeric
    df.columns = df.columns.str.strip()
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Convert percentage to decimal (divide by 100)
    df = df.astype(float) / 100.0
    
    # Filter for 2024 only
    df = df[(df.index >= '2024-01-01') & (df.index <= '2024-12-31')]
    
    print(f"    Date range: {df.index.min()} to {df.index.max()}")
    print(f"    Observations: {len(df)}")
    print(f"    Columns: {df.columns.tolist()}")
    
    return df


def load_portfolio_returns(config):
    """Load portfolio returns for a specific configuration"""
    file_path = os.path.join(PORTFOLIO_DIR, f"portfolio_returns_{config}.csv")
    
    if not os.path.exists(file_path):
        print(f"  ⚠️  Portfolio file not found: {file_path}")
        return None
    
    df = pd.read_csv(file_path)
    df['return_date'] = pd.to_datetime(df['return_date'])
    df = df.set_index('return_date')
    
    print(f"  Loaded {config}: {len(df)} observations")
    
    return df


def merge_portfolio_and_factors(portfolio_returns, factors, portfolio_type='long_short'):
    """
    Merge portfolio returns with factor data.
    
    Args:
        portfolio_returns: DataFrame with portfolio returns
        factors: DataFrame with factor returns and RF
        portfolio_type: which portfolio to analyze ('long', 'short', or 'long_short')
    
    Returns:
        DataFrame with merged data
    """
    # Extract the specific portfolio return
    portfolio_col = portfolio_type
    
    if portfolio_col not in portfolio_returns.columns:
        raise ValueError(f"Portfolio type '{portfolio_type}' not found in returns data")
    
    # Merge on date index
    merged = portfolio_returns[[portfolio_col]].merge(
        factors,
        left_index=True,
        right_index=True,
        how='inner'
    )
    
    # Rename portfolio column for clarity
    merged = merged.rename(columns={portfolio_col: 'portfolio_return'})
    
    # Compute excess return
    merged['excess_return'] = merged['portfolio_return'] - merged['RF']
    
    print(f"    Merged observations: {len(merged)}")
    print(f"    Mean portfolio return: {merged['portfolio_return'].mean():.6f} ({merged['portfolio_return'].mean()*100:.4f}%)")
    print(f"    Mean excess return: {merged['excess_return'].mean():.6f}")
    
    return merged


def run_capm_regression(data, hac_lags=10):
    """
    Run CAPM regression: R_p - R_f = α + β × (R_m - R_f) + ε
    
    Args:
        data: DataFrame with 'excess_return' and 'Mkt-RF'
        hac_lags: number of lags for Newey-West standard errors
    
    Returns:
        Dictionary with regression results
    """
    # Prepare regression data
    y = data['excess_return']
    X = data[['Mkt-RF']]
    X = sm.add_constant(X)  # Add intercept
    
    # Run OLS
    model = OLS(y, X)
    results = model.fit()
    
    # Get Newey-West (HAC) standard errors
    results_hac = results.get_robustcov_results(cov_type='HAC', maxlags=hac_lags)
    
    # Extract results
    alpha = results_hac.params[0]  # const is first parameter
    alpha_tstat = results_hac.tvalues[0]
    beta_mkt = results_hac.params[1]  # Mkt-RF is second parameter
    r_squared = results.rsquared
    
    return {
        'model': 'CAPM',
        'alpha': alpha,
        'alpha_tstat': alpha_tstat,
        'beta_MKT': beta_mkt,
        'beta_SMB': np.nan,
        'beta_HML': np.nan,
        'beta_RMW': np.nan,
        'beta_CMA': np.nan,
        'r_squared': r_squared,
        'n_obs': len(data)
    }


def run_ff3_regression(data, hac_lags=10):
    """
    Run Fama-French 3-factor regression: R_p - R_f = α + β_MKT × (R_m - R_f) + β_SMB × SMB + β_HML × HML + ε
    """
    # Prepare regression data
    y = data['excess_return']
    X = data[['Mkt-RF', 'SMB', 'HML']]
    X = sm.add_constant(X)
    
    # Run OLS
    model = OLS(y, X)
    results = model.fit()
    
    # Get Newey-West (HAC) standard errors
    results_hac = results.get_robustcov_results(cov_type='HAC', maxlags=hac_lags)
    
    # Extract results
    alpha = results_hac.params[0]
    alpha_tstat = results_hac.tvalues[0]
    
    return {
        'model': 'FF3',
        'alpha': alpha,
        'alpha_tstat': alpha_tstat,
        'beta_MKT': results_hac.params[1],
        'beta_SMB': results_hac.params[2],
        'beta_HML': results_hac.params[3],
        'beta_RMW': np.nan,
        'beta_CMA': np.nan,
        'r_squared': results.rsquared,
        'n_obs': len(data)
    }


def run_ff5_regression(data, hac_lags=10):
    """
    Run Fama-French 5-factor regression: R_p - R_f = α + β_MKT × (R_m - R_f) + β_SMB × SMB + β_HML × HML + β_RMW × RMW + β_CMA × CMA + ε
    """
    # Prepare regression data
    y = data['excess_return']
    X = data[['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA']]
    X = sm.add_constant(X)
    
    # Run OLS
    model = OLS(y, X)
    results = model.fit()
    
    # Get Newey-West (HAC) standard errors
    results_hac = results.get_robustcov_results(cov_type='HAC', maxlags=hac_lags)
    
    # Extract results
    alpha = results_hac.params[0]
    alpha_tstat = results_hac.tvalues[0]
    
    return {
        'model': 'FF5',
        'alpha': alpha,
        'alpha_tstat': alpha_tstat,
        'beta_MKT': results_hac.params[1],
        'beta_SMB': results_hac.params[2],
        'beta_HML': results_hac.params[3],
        'beta_RMW': results_hac.params[4],
        'beta_CMA': results_hac.params[5],
        'r_squared': results.rsquared,
        'n_obs': len(data)
    }


def interpret_portfolio_results(config, results_list):
    """
    Provide detailed interpretation of portfolio regression results.
    
    Args:
        config: configuration name
        results_list: list of result dictionaries from regressions
    """
    print(f"\n  {'─'*56}")
    print(f"  INTERPRETATION FOR {config.upper()}:")
    print(f"  {'─'*56}")
    
    if not results_list:
        print("  WARNING: No results to interpret.")
        return
    
    # Extract long-short results
    ls_results = [r for r in results_list if r['portfolio'] == 'long_short']
    
    if not ls_results:
        print("  WARNING: No long-short results available.")
        return
    
    # Get CAPM, FF3, FF5 results
    capm = next((r for r in ls_results if r['model'] == 'CAPM'), None)
    ff3 = next((r for r in ls_results if r['model'] == 'FF3'), None)
    ff5 = next((r for r in ls_results if r['model'] == 'FF5'), None)
    
    # Analyze alpha significance and direction
    if capm:
        alpha_annual = capm['alpha'] * 252
        t_stat = capm['alpha_tstat']
        
        # Interpret alpha direction and magnitude
        if abs(alpha_annual) < 0.01:
            magnitude = "negligible"
        elif abs(alpha_annual) < 0.05:
            magnitude = "small"
        elif abs(alpha_annual) < 0.15:
            magnitude = "moderate"
        else:
            magnitude = "large"
        
        direction = "positive" if alpha_annual > 0 else "negative"
        
        # Interpret statistical significance
        if abs(t_stat) >= 2.576:
            sig_level = "highly significant (p<0.01, 99% confidence)"
        elif abs(t_stat) >= 1.96:
            sig_level = "statistically significant (p<0.05, 95% confidence)"
        elif abs(t_stat) >= 1.645:
            sig_level = "marginally significant (p<0.10, 90% confidence)"
        else:
            sig_level = "not statistically significant"
        
        print(f"\n  📊 ALPHA ANALYSIS:")
        print(f"     • Annualized alpha: {alpha_annual:+.2%} ({magnitude} {direction} return)")
        print(f"     • T-statistic: {t_stat:.2f} → {sig_level}")
        
        if direction == "positive":
            if abs(t_stat) >= 1.645:
                print(f"     ✓ Strategy generates excess returns beyond risk factors")
            else:
                print(f"     ⚠ Positive alpha but not statistically reliable")
        else:
            if abs(t_stat) >= 1.645:
                print(f"     ✗ Strategy underperforms risk-adjusted expectations")
            else:
                print(f"     ⚠ Negative alpha but not statistically significant")
    
    # Compare models
    if capm and ff3 and ff5:
        print(f"\n  📈 MODEL COMPARISON:")
        print(f"     • CAPM R²: {capm['r_squared']:.1%} (explains market risk only)")
        print(f"     • FF3 R²:  {ff3['r_squared']:.1%} (adds size & value factors)")
        print(f"     • FF5 R²:  {ff5['r_squared']:.1%} (adds profitability & investment)")
        
        r2_improvement_ff3 = ff3['r_squared'] - capm['r_squared']
        r2_improvement_ff5 = ff5['r_squared'] - ff3['r_squared']
        
        if r2_improvement_ff3 > 0.05:
            print(f"     ✓ Size/Value factors explain {r2_improvement_ff3:.1%} additional variance")
        else:
            print(f"     → Size/Value factors add minimal explanatory power ({r2_improvement_ff3:+.1%})")
        
        if r2_improvement_ff5 > 0.05:
            print(f"     ✓ Profitability/Investment factors add {r2_improvement_ff5:.1%} more")
        else:
            print(f"     → Profitability/Investment factors have limited impact ({r2_improvement_ff5:+.1%})")
        
        # Alpha stability across models
        alpha_capm = capm['alpha'] * 252
        alpha_ff3 = ff3['alpha'] * 252
        alpha_ff5 = ff5['alpha'] * 252
        
        alpha_change_ff3 = abs(alpha_ff3 - alpha_capm)
        alpha_change_ff5 = abs(alpha_ff5 - alpha_ff3)
        
        print(f"\n  🔍 ALPHA STABILITY:")
        if alpha_change_ff3 > 0.05:
            print(f"     ⚠ Alpha changes by {alpha_change_ff3:.2%} with FF3 (sensitive to size/value)")
        else:
            print(f"     ✓ Alpha stable with FF3 adjustment (change: {alpha_change_ff3:.2%})")
        
        if alpha_change_ff5 > 0.05:
            print(f"     ⚠ Alpha changes by {alpha_change_ff5:.2%} with FF5 (sensitive to RMW/CMA)")
        else:
            print(f"     ✓ Alpha stable with FF5 adjustment (change: {alpha_change_ff5:.2%})")
    
    # Factor exposure analysis (beta interpretation)
    if ff5:
        print(f"\n  🧬 FACTOR EXPOSURES - FF5 Model:")
        
        beta_mkt = ff5['beta_MKT']
        beta_smb = ff5['beta_SMB']
        beta_hml = ff5['beta_HML']
        beta_rmw = ff5['beta_RMW']
        beta_cma = ff5['beta_CMA']
        
        # Market beta
        if beta_mkt > 1.2:
            mkt_interp = "High market sensitivity (aggressive)"
        elif beta_mkt > 0.8:
            mkt_interp = "Market-neutral exposure"
        else:
            mkt_interp = "Low market sensitivity (defensive)"
        print(f"     • Market (β={beta_mkt:.2f}): {mkt_interp}")
        
        # Size factor (SMB - Small Minus Big)
        if abs(beta_smb) < 0.2:
            smb_interp = "No size tilt"
        elif beta_smb > 0:
            smb_interp = f"Small-cap bias (β={beta_smb:+.2f}) - may explain alpha as size premium"
        else:
            smb_interp = f"Large-cap bias (β={beta_smb:+.2f}) - tilts toward bigger, liquid stocks"
        print(f"     • Size: {smb_interp}")
        
        # Value factor (HML - High Minus Low book-to-market)
        if abs(beta_hml) < 0.2:
            hml_interp = "No value/growth tilt"
        elif beta_hml > 0:
            hml_interp = f"Value bias (β={beta_hml:+.2f}) - may explain alpha as value premium"
        else:
            hml_interp = f"Growth bias (β={beta_hml:+.2f}) - tilts toward growth stocks"
        print(f"     • Value: {hml_interp}")
        
        # Profitability factor (RMW - Robust Minus Weak)
        if abs(beta_rmw) < 0.2:
            rmw_interp = "No profitability tilt"
        elif beta_rmw > 0:
            rmw_interp = f"Quality bias (β={beta_rmw:+.2f}) - prefers profitable firms"
        else:
            rmw_interp = f"Distress bias (β={beta_rmw:+.2f}) - tilts toward unprofitable firms"
        print(f"     • Profitability: {rmw_interp}")
        
        # Investment factor (CMA - Conservative Minus Aggressive)
        if abs(beta_cma) < 0.2:
            cma_interp = "No investment tilt"
        elif beta_cma > 0:
            cma_interp = f"Conservative bias (β={beta_cma:+.2f}) - prefers low-investment firms"
        else:
            cma_interp = f"Growth bias (β={beta_cma:+.2f}) - tilts toward high-investment firms"
        print(f"     • Investment: {cma_interp}")
        
        # Overall factor assessment
        print(f"\n     📌 Factor Loading Summary:")
        if abs(beta_smb) < 0.3 and abs(beta_hml) < 0.3:
            print(f"        ✓ Low size/value exposure → Alpha NOT driven by factor tilts")
        else:
            print(f"        ⚠ Moderate size/value exposure → Part of alpha may be factor premium")
    
    # Long vs Short leg analysis
    long_results = [r for r in results_list if r['portfolio'] == 'long']
    short_results = [r for r in results_list if r['portfolio'] == 'short']
    
    if long_results and short_results:
        print(f"\n  ⚖️ LONG vs SHORT LEG BREAKDOWN:")
        
        # Get FF5 or FF3 results for comparison
        long_best = next((r for r in long_results if r['model'] == 'FF5'), 
                        next((r for r in long_results if r['model'] == 'FF3'), None))
        short_best = next((r for r in short_results if r['model'] == 'FF5'), 
                         next((r for r in short_results if r['model'] == 'FF3'), None))
        
        if long_best and short_best:
            long_alpha_annual = long_best['alpha'] * 252
            short_alpha_annual = short_best['alpha'] * 252
            
            print(f"     Long Leg:  α={long_alpha_annual:+.2%} (t={long_best['alpha_tstat']:.2f})")
            print(f"     Short Leg: α={short_alpha_annual:+.2%} (t={short_best['alpha_tstat']:.2f})")
            
            # Determine which leg drives performance
            if abs(long_alpha_annual) > abs(short_alpha_annual) * 1.5:
                print(f"     → Performance driven by LONG leg (winner selection)")
            elif abs(short_alpha_annual) > abs(long_alpha_annual) * 1.5:
                print(f"     → Performance driven by SHORT leg (loser identification)")
            else:
                print(f"     → Both legs contribute to performance")
            
            # Check if alphas have opposite signs (ideal)
            if long_alpha_annual > 0 and short_alpha_annual < 0:
                print(f"     ✓ Long positive, Short negative → Clean signal on both sides")
            elif long_alpha_annual < 0 and short_alpha_annual > 0:
                print(f"     ✗ Long negative, Short positive → Signal inverted (counterintuitive)")
            elif long_alpha_annual < 0 and short_alpha_annual < 0:
                print(f"     ⚠ Both legs negative → Overall underperformance")
            else:
                print(f"     ⚠ Both legs positive → Short leg problematic")
    
    # Strategy-specific insights
    print(f"\n  💡 STRATEGY INSIGHTS:")
    
    rebal_freq = "monthly" if "monthly" in config else "weekly"
    weight_scheme = "equal-weighted" if "equal" in config else "value-weighted"
    
    print(f"     • Rebalancing: {rebal_freq.capitalize()} (balance between turnover & signal freshness)")
    print(f"     • Weighting: {weight_scheme.capitalize()}")
    
    if "equal" in config:
        print(f"       → Treats all stocks equally regardless of market cap")
        if capm and capm['alpha'] < 0:
            print(f"       → May be overweight in small-cap stocks with higher transaction costs")
    else:
        print(f"       → Tilts toward larger, more liquid stocks")
        if capm and capm['alpha'] > 0:
            print(f"       → Benefits from liquidity and lower implementation costs")
    
    # Overall assessment
    print(f"\n  🎯 OVERALL ASSESSMENT:")
    if capm:
        if capm['alpha'] * 252 > 0.10 and abs(capm['alpha_tstat']) >= 1.645:
            print(f"     ★★★ STRONG: Significant positive alpha suggests sentiment signal has predictive power")
        elif capm['alpha'] * 252 > 0.05 and abs(capm['alpha_tstat']) >= 1.0:
            print(f"     ★★☆ PROMISING: Positive alpha approaching significance, worth further investigation")
        elif abs(capm['alpha'] * 252) < 0.05:
            print(f"     ★☆☆ NEUTRAL: Alpha is economically small, strategy has limited practical value")
        else:
            print(f"     ☆☆☆ WEAK: Negative or insignificant alpha, strategy not recommended as-is")
    
    print(f"  {'─'*56}\n")


def analyze_portfolio_config(config, factors_daily, factors_monthly):
    """
    Analyze one portfolio configuration with all factor models.
    
    Args:
        config: configuration name (e.g., 'monthly_equal')
        factors_daily: daily factor data
        factors_monthly: monthly factor data
    
    Returns:
        List of result dictionaries
    """
    print(f"\n{'='*60}")
    print(f"ANALYZING: {config.upper()}")
    print(f"{'='*60}")
    
    # Load portfolio returns
    portfolio_returns = load_portfolio_returns(config)
    
    if portfolio_returns is None:
        return []
    
    # ALL portfolios use daily factors since all return files contain daily returns
    # (The monthly/weekly in config name refers to rebalancing frequency, not return frequency)
    factors = factors_daily
    hac_lags = HAC_LAGS['daily']
    
    print(f"  Using daily factors with {hac_lags} HAC lags")
    print(f"  Note: '{config}' refers to rebalancing frequency, returns are daily")
    
    results = []
    
    # Analyze each portfolio type (long, short, long_short)
    for portfolio_type in PORTFOLIO_TYPES:
        print(f"\n  Portfolio: {portfolio_type.upper()}")
        
        # Merge with factors
        try:
            merged_data = merge_portfolio_and_factors(portfolio_returns, factors, portfolio_type)
        except Exception as e:
            print(f"    ⚠️  Error merging data: {e}")
            continue
        
        # Run CAPM
        try:
            capm_result = run_capm_regression(merged_data, hac_lags)
            capm_result.update({'config': config, 'portfolio': portfolio_type, 'frequency': 'daily'})
            results.append(capm_result)
            print(f"    CAPM: α={capm_result['alpha']:.6f}, t={capm_result['alpha_tstat']:.2f}, R²={capm_result['r_squared']:.3f}")
        except Exception as e:
            print(f"    ⚠️  CAPM error: {e}")
        
        # Run FF3
        try:
            ff3_result = run_ff3_regression(merged_data, hac_lags)
            ff3_result.update({'config': config, 'portfolio': portfolio_type, 'frequency': 'daily'})
            results.append(ff3_result)
            print(f"    FF3:  α={ff3_result['alpha']:.6f}, t={ff3_result['alpha_tstat']:.2f}, R²={ff3_result['r_squared']:.3f}")
        except Exception as e:
            print(f"    ⚠️  FF3 error: {e}")
        
        # Run FF5 (only if RMW and CMA are available)
        if 'RMW' in merged_data.columns and 'CMA' in merged_data.columns:
            try:
                ff5_result = run_ff5_regression(merged_data, hac_lags)
                ff5_result.update({'config': config, 'portfolio': portfolio_type, 'frequency': 'daily'})
                results.append(ff5_result)
                print(f"    FF5:  α={ff5_result['alpha']:.6f}, t={ff5_result['alpha_tstat']:.2f}, R²={ff5_result['r_squared']:.3f}")
            except Exception as e:
                print(f"    ⚠️  FF5 error: {e}")
        else:
            print(f"    ⚠️  FF5 skipped (factors not available)")
    
    # Provide detailed interpretation
    interpret_portfolio_results(config, results)
    
    return results


def create_alpha_summary_table(results_df):
    """Create a clean summary table focusing on alpha estimates"""
    
    # Annualize alpha based on frequency
    results_df['alpha_annualized'] = results_df.apply(
        lambda row: row['alpha'] * 252 if row['frequency'] == 'daily' else row['alpha'] * 12,
        axis=1
    )
    
    # Create significance stars
    def significance_stars(tstat):
        if abs(tstat) >= 2.576:
            return '***'
        elif abs(tstat) >= 1.96:
            return '**'
        elif abs(tstat) >= 1.645:
            return '*'
        else:
            return ''
    
    results_df['significance'] = results_df['alpha_tstat'].apply(significance_stars)
    
    # Select columns for summary
    summary = results_df[[
        'config', 'portfolio', 'model', 
        'alpha', 'alpha_annualized', 'alpha_tstat', 'significance',
        'beta_MKT', 'beta_SMB', 'beta_HML', 'r_squared', 'n_obs'
    ]].copy()
    
    return summary


def main():
    print(f"{'='*60}")
    print("FACTOR MODEL ALPHA ANALYSIS")
    print(f"{'='*60}\n")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load Fama-French factor data
    print("Loading Fama-French factor data...")
    
    factors_daily_3 = load_fama_french_factors(
        os.path.join(FACTOR_DIR, FACTOR_FILES['daily_3']), 
        frequency='daily'
    )
    
    factors_daily_5 = load_fama_french_factors(
        os.path.join(FACTOR_DIR, FACTOR_FILES['daily_5']), 
        frequency='daily'
    )
    
    factors_monthly_3 = load_fama_french_factors(
        os.path.join(FACTOR_DIR, FACTOR_FILES['monthly_3']), 
        frequency='monthly'
    )
    
    factors_monthly_5 = load_fama_french_factors(
        os.path.join(FACTOR_DIR, FACTOR_FILES['monthly_5']), 
        frequency='monthly'
    )
    
    # Merge 3-factor and 5-factor data (5-factor includes all columns from 3-factor)
    factors_daily = factors_daily_5.copy()
    factors_monthly = factors_monthly_5.copy()
    
    # Run analysis for all configurations
    all_results = []
    
    for config in CONFIGS:
        results = analyze_portfolio_config(config, factors_daily, factors_monthly)
        all_results.extend(results)
    
    # Convert to DataFrame
    results_df = pd.DataFrame(all_results)
    
    # Save full results
    full_results_file = os.path.join(OUTPUT_DIR, "alpha_full_results.csv")
    results_df.to_csv(full_results_file, index=False)
    print(f"\n✅ Saved full results to: {full_results_file}")
    
    # Create and save summary table
    summary_df = create_alpha_summary_table(results_df)
    summary_file = os.path.join(OUTPUT_DIR, "alpha_summary.csv")
    summary_df.to_csv(summary_file, index=False)
    print(f"✅ Saved alpha summary to: {summary_file}")
    
    # Print key findings
    print(f"\n{'='*60}")
    print("KEY FINDINGS - LONG-SHORT PORTFOLIOS")
    print(f"{'='*60}\n")
    
    ls_results = summary_df[summary_df['portfolio'] == 'long_short'].copy()
    
    for config in CONFIGS:
        config_results = ls_results[ls_results['config'] == config]
        if len(config_results) > 0:
            print(f"\n{config.upper()}:")
            for _, row in config_results.iterrows():
                sig = row['significance']
                print(f"  {row['model']}: α(annual)={row['alpha_annualized']:>7.2%} (t={row['alpha_tstat']:>5.2f}{sig}), R²={row['r_squared']:.3f}")
    
    print(f"\n{'='*60}")
    print("Significance: * p<0.10, ** p<0.05, *** p<0.01")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
