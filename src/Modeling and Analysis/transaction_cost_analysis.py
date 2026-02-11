"""
transaction_cost_analysis.py

Calculates net alpha after accounting for transaction costs.

Reads:
- Alpha estimates from factor_alpha.py output (../results/Factor_Models/)
- Turnover data from portfolio_backtest.py output (../Portfolio/)

Computes:
- Transaction cost = avg_turnover × cost_per_trade × rebalancing_frequency
- Net alpha = Gross alpha - Transaction costs

Outputs:
- Net alpha summary table
- Saved to ../results/Factor_Models/
"""

import pandas as pd
import numpy as np
import os

# File paths (relative to project root)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, '..', '..')  # Go up to project root

ALPHA_RESULTS = os.path.join(project_root, 'Statistics', 'Factor_Models Statistics', 'alpha_full_results.csv')
PORTFOLIO_DIR = os.path.join(project_root, 'Statistics', 'Portfolio Returns')
OUTPUT_DIR = os.path.join(project_root, 'Statistics', 'Factor_Models Statistics')

# Transaction cost assumptions (in bps = basis points = 0.01%)
TRANSACTION_COST_SCENARIOS = {
    'low': 10,      # 10 bps = 0.10% per round-trip (very liquid stocks, low-cost broker)
    'base': 20,     # 20 bps = 0.20% per round-trip (realistic for institutional)
    'high': 50      # 50 bps = 0.50% per round-trip (retail or illiquid stocks)
}

# Rebalancing frequencies (trades per year)
REBALANCING_FREQ = {
    'monthly': 12,  # 12 rebalances per year
    'weekly': 52    # 52 rebalances per year
}

def load_alpha_results():
    """Load alpha results from factor model analysis"""
    if not os.path.exists(ALPHA_RESULTS):
        raise FileNotFoundError(f"Alpha results not found: {ALPHA_RESULTS}")
    
    df = pd.read_csv(ALPHA_RESULTS)
    
    # Filter for long_short portfolios only
    df = df[df['portfolio'] == 'long_short'].copy()
    
    print(f"Loaded alpha results: {len(df)} portfolios × models")
    return df


def load_turnover_data():
    """Load turnover data from portfolio summary files"""
    turnover_data = []
    
    for config in ['monthly_equal', 'monthly_value', 'weekly_equal', 'weekly_value']:
        file_path = os.path.join(PORTFOLIO_DIR, f"portfolio_summary_{config}.csv")
        
        if not os.path.exists(file_path):
            print(f"  ⚠️  File not found: {file_path}")
            continue
        
        df = pd.read_csv(file_path)
        
        # Get long_short portfolio data
        ls_row = df[df['portfolio'] == 'long_short']
        
        if len(ls_row) > 0:
            turnover_data.append({
                'config': config,
                'avg_turnover': ls_row['avg_turnover'].values[0]
            })
    
    turnover_df = pd.DataFrame(turnover_data)
    print(f"Loaded turnover data: {len(turnover_df)} configurations")
    
    return turnover_df


def calculate_transaction_costs(turnover, rebal_freq, cost_bps):
    """
    Calculate annual transaction costs.
    
    Args:
        turnover: average turnover per rebalance (e.g., 0.66 = 66%)
        rebal_freq: number of rebalances per year
        cost_bps: transaction cost in basis points (e.g., 20 = 0.20%)
    
    Returns:
        Annual transaction cost (as decimal, e.g., 0.08 = 8%)
    """
    cost_per_rebalance = turnover * (cost_bps / 10000)  # Convert bps to decimal
    annual_cost = cost_per_rebalance * rebal_freq
    return annual_cost


def analyze_transaction_costs(alpha_df, turnover_df):
    """
    Analyze net alpha after transaction costs for all scenarios.
    
    Returns:
        DataFrame with gross alpha, transaction costs, and net alpha
    """
    results = []
    
    for _, alpha_row in alpha_df.iterrows():
        config = alpha_row['config']
        model = alpha_row['model']
        gross_alpha_daily = alpha_row['alpha']
        gross_alpha_annual = gross_alpha_daily * 252
        
        # Get turnover for this config
        turnover_row = turnover_df[turnover_df['config'] == config]
        
        if len(turnover_row) == 0:
            print(f"  ⚠️  No turnover data for {config}")
            continue
        
        avg_turnover = turnover_row['avg_turnover'].values[0]
        
        # Determine rebalancing frequency
        freq_key = 'monthly' if 'monthly' in config else 'weekly'
        rebal_freq = REBALANCING_FREQ[freq_key]
        
        # Calculate transaction costs for each scenario
        for scenario, cost_bps in TRANSACTION_COST_SCENARIOS.items():
            tc_annual = calculate_transaction_costs(avg_turnover, rebal_freq, cost_bps)
            net_alpha_annual = gross_alpha_annual - tc_annual
            
            results.append({
                'config': config,
                'model': model,
                'gross_alpha_annual': gross_alpha_annual,
                'avg_turnover': avg_turnover,
                'rebal_freq': rebal_freq,
                'cost_scenario': scenario,
                'cost_bps': cost_bps,
                'tc_annual': tc_annual,
                'net_alpha_annual': net_alpha_annual,
                'alpha_remains_positive': net_alpha_annual > 0
            })
    
    results_df = pd.DataFrame(results)
    return results_df


def print_summary(results_df):
    """Print formatted summary of transaction cost analysis"""
    
    print(f"\n{'='*80}")
    print("TRANSACTION COST ANALYSIS - NET ALPHA AFTER COSTS")
    print(f"{'='*80}\n")
    
    # Group by config and cost scenario
    configs = results_df['config'].unique()
    
    for config in configs:
        config_data = results_df[results_df['config'] == config]
        
        print(f"\n{'─'*80}")
        print(f"{config.upper()}")
        print(f"{'─'*80}")
        
        # Get turnover and frequency
        turnover = config_data['avg_turnover'].iloc[0]
        rebal_freq = config_data['rebal_freq'].iloc[0]
        
        print(f"Average Turnover: {turnover:.1%} per rebalance")
        print(f"Rebalancing Frequency: {rebal_freq} times per year")
        print(f"Annual Trading: {turnover * rebal_freq:.1%} of portfolio value\n")
        
        # Show results for each model and cost scenario
        models = config_data['model'].unique()
        
        for model in models:
            model_data = config_data[config_data['model'] == model]
            
            print(f"  {model}:")
            
            gross_alpha = model_data['gross_alpha_annual'].iloc[0]
            print(f"    Gross Alpha: {gross_alpha:+.2%}")
            
            for scenario in ['low', 'base', 'high']:
                scenario_row = model_data[model_data['cost_scenario'] == scenario].iloc[0]
                
                tc = scenario_row['tc_annual']
                net_alpha = scenario_row['net_alpha_annual']
                remains_positive = scenario_row['alpha_remains_positive']
                
                status = "✓" if remains_positive else "✗"
                
                print(f"    {scenario.capitalize():5} cost ({scenario_row['cost_bps']} bps): "
                      f"TC={tc:+.2%}, Net α={net_alpha:+.2%} {status}")
            
            print()
    
    # Summary table
    print(f"\n{'='*80}")
    print("SUMMARY: NET ALPHA VIABILITY (BASE CASE: 20 BPS)")
    print(f"{'='*80}\n")
    
    base_case = results_df[results_df['cost_scenario'] == 'base']
    
    summary = base_case.pivot_table(
        index='config',
        columns='model',
        values='net_alpha_annual',
        aggfunc='first'
    )
    
    print(summary.to_string(float_format=lambda x: f"{x:+.2%}"))
    
    print(f"\n{'='*80}")
    print("INTERPRETATION")
    print(f"{'='*80}\n")
    
    # Find best strategy
    best_idx = base_case['net_alpha_annual'].idxmax()
    best_row = base_case.loc[best_idx]
    
    print(f"🏆 BEST STRATEGY (Base Case):")
    print(f"   {best_row['config']} with {best_row['model']} model")
    print(f"   Gross Alpha: {best_row['gross_alpha_annual']:+.2%}")
    print(f"   Transaction Costs: {best_row['tc_annual']:.2%}")
    print(f"   Net Alpha: {best_row['net_alpha_annual']:+.2%}")
    
    # Count viable strategies
    viable_count = base_case[base_case['alpha_remains_positive']].shape[0]
    total_count = base_case.shape[0]
    
    print(f"\n📊 VIABILITY:")
    print(f"   {viable_count}/{total_count} strategies remain profitable after transaction costs")
    
    # Weekly vs Monthly comparison
    weekly_base = base_case[base_case['config'].str.contains('weekly')]
    monthly_base = base_case[base_case['config'].str.contains('monthly')]
    
    print(f"\n⚖️  FREQUENCY COMPARISON (Base Case):")
    print(f"   Weekly strategies: avg net α = {weekly_base['net_alpha_annual'].mean():+.2%}")
    print(f"   Monthly strategies: avg net α = {monthly_base['net_alpha_annual'].mean():+.2%}")
    
    if weekly_base['net_alpha_annual'].mean() > monthly_base['net_alpha_annual'].mean():
        diff = weekly_base['net_alpha_annual'].mean() - monthly_base['net_alpha_annual'].mean()
        print(f"   → Weekly outperforms by {diff:.2%} despite higher turnover costs")
    else:
        diff = monthly_base['net_alpha_annual'].mean() - weekly_base['net_alpha_annual'].mean()
        print(f"   → Monthly outperforms by {diff:.2%} due to lower turnover")
    
    print(f"\n{'='*80}\n")


def main():
    print(f"{'='*80}")
    print("TRANSACTION COST ANALYSIS")
    print(f"{'='*80}\n")
    
    # Load data
    print("Loading data...")
    alpha_df = load_alpha_results()
    turnover_df = load_turnover_data()
    
    print(f"\nTransaction cost assumptions:")
    for scenario, bps in TRANSACTION_COST_SCENARIOS.items():
        print(f"  {scenario.capitalize()}: {bps} bps = {bps/10000:.2%} per round-trip")
    
    # Analyze
    print("\nCalculating net alphas...")
    results_df = analyze_transaction_costs(alpha_df, turnover_df)
    
    # Print summary
    print_summary(results_df)
    
    # Save results
    output_file = os.path.join(OUTPUT_DIR, "net_alpha_after_costs.csv")
    results_df.to_csv(output_file, index=False)
    print(f"✅ Saved results to: {output_file}")
    
    # Also save a pivot table for easy viewing
    pivot_file = os.path.join(OUTPUT_DIR, "net_alpha_summary_table.csv")
    
    pivot = results_df.pivot_table(
        index=['config', 'model'],
        columns='cost_scenario',
        values='net_alpha_annual',
        aggfunc='first'
    )
    
    pivot.to_csv(pivot_file)
    print(f"✅ Saved summary table to: {pivot_file}")


if __name__ == "__main__":
    main()
