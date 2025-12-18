import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np
from scipy import stats

# File paths - change these variables to use different files
MERGED_DATA_FILE = "CampusChallenge-Group-15/results/Merged Data/Merged_Data_v6(Full-Test_Data)_non-adjusted.csv"
OUTPUT_DIR = "CampusChallenge-Group-15/results/Plots/plots_v6_FullData_non-adjusted"
STATS_OUTPUT_FILE = "CampusChallenge-Group-15/results/Score Statistics/Plot_Statistics_v6_FullData_non-adjusted.csv"

def plot_ticker_data(merged_file, output_dir, stats_output_file):
    """
    Create line plots for each ticker showing RET and Score over time.
    
    Args:
        merged_file: Path to the merged data CSV file
        output_dir: Directory to save the plot images
        stats_output_file: Path to save the statistics CSV file
    """
    import os
    
    # Read the merged data
    print(f"Reading {merged_file}...")
    df = pd.read_csv(merged_file)
    
    # Convert date to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Sort by date (oldest to newest)
    df = df.sort_values('Date')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get unique tickers
    tickers = df['Ticker'].unique()
    print(f"\nFound {len(tickers)} unique tickers")
    print(f"Tickers: {', '.join(sorted(tickers))}")
    
    # List to collect statistics for all tickers
    all_stats = []
    
    # Create a plot for each ticker
    for ticker in sorted(tickers):
        print(f"\nCreating plot for {ticker}...")
        
        # Filter data for this ticker
        ticker_df = df[df['Ticker'] == ticker].copy()
        ticker_df = ticker_df.sort_values('Date')
        
        # Normalize data for better comparison
        # Z-score normalization (standardize to mean=0, std=1)
        ticker_df['RET_normalized'] = (ticker_df['RET'] - ticker_df['RET'].mean()) / ticker_df['RET'].std()
        ticker_df['Score_normalized'] = (ticker_df['Score'] - ticker_df['Score'].mean()) / ticker_df['Score'].std()
        
        # Convert RET to percentage for raw display
        ticker_df['RET_pct'] = ticker_df['RET'] * 100
        
        # Calculate rolling correlation (5-day window)
        if len(ticker_df) >= 5:
            ticker_df['rolling_corr'] = ticker_df['RET'].rolling(window=5).corr(ticker_df['Score'])
        
        # Create figure with 3 subplots
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        # Subplot 1: Raw values (RET as percentage vs Score)
        ax1 = fig.add_subplot(gs[0, :])
        color1 = 'tab:blue'
        ax1.set_xlabel('Date', fontsize=11)
        ax1.set_ylabel('RET (%)', color=color1, fontsize=11)
        line1 = ax1.plot(ticker_df['Date'], ticker_df['RET_pct'], 
                         color=color1, linewidth=2, marker='o', markersize=3,
                         label='Return (%)', alpha=0.7)
        ax1.tick_params(axis='y', labelcolor=color1)
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
        
        ax1_twin = ax1.twinx()
        color2 = 'tab:red'
        ax1_twin.set_ylabel('Score', color=color2, fontsize=11)
        line2 = ax1_twin.plot(ticker_df['Date'], ticker_df['Score'], 
                              color=color2, linewidth=2, marker='s', markersize=3,
                              label='Score', alpha=0.7)
        ax1_twin.tick_params(axis='y', labelcolor=color2)
        ax1_twin.axhline(y=0, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
        ax1_twin.set_ylim(-1.1, 1.1)  # Fix Score axis
        
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        ax1.set_title(f'{ticker} - Raw Values: Returns (%) vs Sentiment Score', fontsize=12, fontweight='bold')
        
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left')
        
        # Subplot 2: Normalized values (z-scores)
        ax2 = fig.add_subplot(gs[1, :])
        ax2.plot(ticker_df['Date'], ticker_df['RET_normalized'], 
                color='tab:blue', linewidth=2, marker='o', markersize=3,
                label='Return (Normalized)', alpha=0.7)
        ax2.plot(ticker_df['Date'], ticker_df['Score_normalized'], 
                color='tab:red', linewidth=2, marker='s', markersize=3,
                label='Score (Normalized)', alpha=0.7)
        ax2.set_xlabel('Date', fontsize=11)
        ax2.set_ylabel('Z-Score (Standard Deviations from Mean)', fontsize=11)
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        ax2.set_title(f'{ticker} - Normalized Values (Z-Scores)', fontsize=12, fontweight='bold')
        ax2.legend(loc='upper left')
        
        # Subplot 3: Scatter plot with correlation
        ax3 = fig.add_subplot(gs[2, 0])
        ax3.scatter(ticker_df['Score'], ticker_df['RET_pct'], 
                   alpha=0.6, s=50, c=range(len(ticker_df)), cmap='viridis')
        
        # Add trend line
        z = np.polyfit(ticker_df['Score'], ticker_df['RET_pct'], 1)
        p = np.poly1d(z)
        ax3.plot(ticker_df['Score'], p(ticker_df['Score']), 
                "r--", linewidth=2, alpha=0.8, label=f'Trend: y={z[0]:.2f}x+{z[1]:.2f}')
        
        ax3.set_xlabel('Score', fontsize=11)
        ax3.set_ylabel('RET (%)', fontsize=11)
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=0, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
        ax3.axvline(x=0, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
        
        # Calculate correlation
        correlation = ticker_df['Score'].corr(ticker_df['RET'])
        ax3.set_title(f'Scatter Plot (Correlation: {correlation:.3f})', fontsize=12, fontweight='bold')
        ax3.legend()
        
        # Collect statistics for this ticker
        ticker_stats = {
            'Ticker': ticker,
            'Data_Points': len(ticker_df),
            'Avg_RET': ticker_df['RET'].mean(),
            'Avg_RET_Pct': ticker_df['RET'].mean() * 100,
            'Avg_Score': ticker_df['Score'].mean(),
            'Correlation': correlation,
            'Date_Start': ticker_df['Date'].min().strftime('%Y-%m-%d'),
            'Date_End': ticker_df['Date'].max().strftime('%Y-%m-%d'),
            'RET_StdDev': ticker_df['RET'].std(),
            'Score_StdDev': ticker_df['Score'].std(),
            'Min_RET': ticker_df['RET'].min(),
            'Max_RET': ticker_df['RET'].max(),
            'Min_Score': ticker_df['Score'].min(),
            'Max_Score': ticker_df['Score'].max()
        }
        all_stats.append(ticker_stats)
        
        # Subplot 4: Rolling correlation
        ax4 = fig.add_subplot(gs[2, 1])
        if 'rolling_corr' in ticker_df.columns and not ticker_df['rolling_corr'].isna().all():
            ax4.plot(ticker_df['Date'], ticker_df['rolling_corr'], 
                    color='tab:purple', linewidth=2, marker='o', markersize=3)
            ax4.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
            ax4.set_ylim(-1.1, 1.1)
            ax4.fill_between(ticker_df['Date'], 0, ticker_df['rolling_corr'], 
                            where=(ticker_df['rolling_corr'] >= 0), 
                            color='green', alpha=0.3, interpolate=True)
            ax4.fill_between(ticker_df['Date'], 0, ticker_df['rolling_corr'], 
                            where=(ticker_df['rolling_corr'] < 0), 
                            color='red', alpha=0.3, interpolate=True)
        else:
            ax4.text(0.5, 0.5, 'Insufficient data\nfor rolling correlation\n(need at least 5 points)', 
                    ha='center', va='center', fontsize=12, transform=ax4.transAxes)
        
        ax4.set_xlabel('Date', fontsize=11)
        ax4.set_ylabel('Rolling Correlation (5-day window)', fontsize=11)
        ax4.grid(True, alpha=0.3)
        ax4.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')
        ax4.set_title(f'Rolling Correlation Over Time', fontsize=12, fontweight='bold')
        
        # Add overall statistics
        stats_text = f'Statistics:\n'
        stats_text += f'Data Points: {len(ticker_df)}\n'
        stats_text += f'Avg RET: {ticker_df["RET"].mean()*100:.3f}%\n'
        stats_text += f'Avg Score: {ticker_df["Score"].mean():.3f}\n'
        stats_text += f'Correlation: {correlation:.3f}\n'
        stats_text += f'Date Range:\n{ticker_df["Date"].min().strftime("%Y-%m-%d")} to\n{ticker_df["Date"].max().strftime("%Y-%m-%d")}'
        
        fig.text(0.98, 0.02, stats_text, fontsize=9, 
                verticalalignment='bottom', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Main title
        fig.suptitle(f'{ticker} - Comprehensive Analysis: Returns vs Sentiment Score', 
                    fontsize=14, fontweight='bold', y=0.995)
        
        # Save the plot
        output_path = os.path.join(output_dir, f'{ticker}_plot.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"  ✅ Saved plot to {output_path}")
        
        # Close the figure to free memory
        plt.close(fig)
    
    # Save statistics to CSV
    print(f"\n{'='*60}")
    print(f"Saving statistics to {stats_output_file}...")
    stats_df = pd.DataFrame(all_stats)
    stats_df.to_csv(stats_output_file, index=False)
    print(f"✅ Saved statistics for {len(stats_df)} tickers")
    
    print(f"\n{'='*60}")
    print(f"✅ Successfully created {len(tickers)} plots in {output_dir}")
    print(f"✅ Statistics saved to {stats_output_file}")
    print(f"{'='*60}")

if __name__ == "__main__":
    # Create the plots
    plot_ticker_data(MERGED_DATA_FILE, OUTPUT_DIR, STATS_OUTPUT_FILE)
