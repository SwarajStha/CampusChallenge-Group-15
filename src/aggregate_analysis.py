import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import seaborn as sns

# File paths - change these variables to use different files
MERGED_DATA_FILE = "CampusChallenge-Group-15/results/Merged Data/Merged_Data_v6(Full-Test_Data).csv"
OUTPUT_DIR = "CampusChallenge-Group-15/results/Plots/Aggregate Analysis"
STATS_OUTPUT_FILE = "CampusChallenge-Group-15/results/Score Statistics/Aggregate_Statistics.csv"

def create_aggregate_analysis(merged_file, output_dir, stats_output_file):
    """
    Create aggregate visualizations showing how Score moves with RET across all tickers.
    
    Args:
        merged_file: Path to the merged data CSV file
        output_dir: Directory to save the plot images
        stats_output_file: Path to save the statistics CSV file
    """
    import os
    
    # Read the merged data
    print(f"Reading {merged_file}...")
    df = pd.read_csv(merged_file)
    
    print(f"Total data points: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")
    
    # Clean data: remove NaN and infinite values
    print(f"\nCleaning data...")
    original_len = len(df)
    df = df.dropna(subset=['Score', 'RET'])
    df = df[np.isfinite(df['Score']) & np.isfinite(df['RET'])]
    print(f"Removed {original_len - len(df)} rows with NaN/infinite values")
    print(f"Remaining data points: {len(df)}")
    
    if len(df) == 0:
        print("ERROR: No valid data remaining after cleaning!")
        return
    
    # Convert RET to percentage for display
    df['RET_pct'] = df['RET'] * 100
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate overall statistics
    overall_corr = df['Score'].corr(df['RET'])
    print(f"\nOverall Pearson Correlation: {overall_corr:.4f}")
    print(f"Mean Score: {df['Score'].mean():.4f}")
    print(f"Mean RET: {df['RET_pct'].mean():.4f}%")
    print(f"Std Score: {df['Score'].std():.4f}")
    print(f"Std RET: {df['RET_pct'].std():.4f}%")
    
    # ===== VISUALIZATION 1: Binned Scatter Plot =====
    # Group returns into bins and show average score for each bin
    print("\n" + "="*60)
    print("Creating Figure 1: Binned Analysis...")
    
    # Create return bins (every 2.5% or 0.025 in decimal)
    bin_size = 0.025
    min_ret = df['RET'].min()
    max_ret = df['RET'].max()
    bins = np.arange(np.floor(min_ret/bin_size)*bin_size, 
                     np.ceil(max_ret/bin_size)*bin_size + bin_size, 
                     bin_size)
    
    df['RET_bin'] = pd.cut(df['RET'], bins=bins)
    
    # Calculate statistics for each bin
    bin_stats = df.groupby('RET_bin', observed=True).agg({
        'Score': ['mean', 'std', 'count'],
        'RET': 'mean'
    }).reset_index()
    bin_stats.columns = ['RET_bin', 'Score_mean', 'Score_std', 'Count', 'RET_mean']
    bin_stats['Score_sem'] = bin_stats['Score_std'] / np.sqrt(bin_stats['Count'])  # Standard error
    bin_stats['RET_mean_pct'] = bin_stats['RET_mean'] * 100
    
    # Remove bins with too few observations
    bin_stats = bin_stats[bin_stats['Count'] >= 5]
    
    fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Top panel: Binned scatter with error bars
    ax1.errorbar(bin_stats['RET_mean_pct'], bin_stats['Score_mean'], 
                 yerr=bin_stats['Score_sem'], 
                 fmt='o', markersize=8, capsize=5, capthick=2,
                 color='blue', ecolor='lightblue', alpha=0.7,
                 label='Avg Score ± SE')
    
    # Add trend line
    z = np.polyfit(bin_stats['RET_mean_pct'], bin_stats['Score_mean'], 1)
    p = np.poly1d(z)
    x_trend = np.linspace(bin_stats['RET_mean_pct'].min(), 
                          bin_stats['RET_mean_pct'].max(), 100)
    ax1.plot(x_trend, p(x_trend), 'r--', linewidth=2, alpha=0.8,
            label=f'Trend: Score = {z[0]:.4f}×RET + {z[1]:.4f}')
    
    ax1.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax1.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax1.set_xlabel('Return (%)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Average Sentiment Score', fontsize=12, fontweight='bold')
    ax1.set_title('How Sentiment Score Changes with Return Magnitude (Binned by 2.5%)', 
                  fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10)
    
    # Bottom panel: Count per bin (histogram overlay)
    ax2.bar(bin_stats['RET_mean_pct'], bin_stats['Count'], 
            width=2.3, color='lightgreen', alpha=0.6, edgecolor='darkgreen')
    ax2.set_xlabel('Return (%)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Number of Observations', fontsize=12, fontweight='bold')
    ax2.set_title('Data Distribution Across Return Bins', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    output_path1 = os.path.join(output_dir, 'aggregate_binned_analysis.png')
    plt.savefig(output_path1, dpi=150, bbox_inches='tight')
    print(f"✅ Saved: {output_path1}")
    plt.close()
    
    # ===== VISUALIZATION 2: 2D Density Heatmap =====
    print("\nCreating Figure 2: Density Heatmap...")
    
    fig2, ax = plt.subplots(figsize=(12, 10))
    
    # Create 2D histogram (heatmap)
    ret_bins = np.linspace(df['RET_pct'].min(), df['RET_pct'].max(), 40)
    score_bins = np.linspace(-1, 1, 40)
    
    h, xedges, yedges = np.histogram2d(df['RET_pct'], df['Score'], 
                                        bins=[ret_bins, score_bins])
    
    # Plot heatmap
    im = ax.imshow(h.T, origin='lower', aspect='auto', cmap='YlOrRd',
                   extent=[ret_bins.min(), ret_bins.max(), -1, 1],
                   interpolation='nearest')
    
    plt.colorbar(im, ax=ax, label='Frequency (Number of Observations)')
    
    # Add diagonal reference line (perfect correlation)
    # Normalize returns to -1 to 1 range for comparison
    ret_range = df['RET_pct'].max() - df['RET_pct'].min()
    if ret_range > 0:
        x_diag = np.array([df['RET_pct'].min(), df['RET_pct'].max()])
        y_diag = 2 * (x_diag - df['RET_pct'].min()) / ret_range - 1
        ax.plot(x_diag, y_diag, 'b--', linewidth=2, alpha=0.5, 
                label='Perfect Correlation Reference')
    
    ax.axhline(y=0, color='white', linestyle='--', linewidth=1, alpha=0.7)
    ax.axvline(x=0, color='white', linestyle='--', linewidth=1, alpha=0.7)
    ax.set_xlabel('Return (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Sentiment Score', fontsize=12, fontweight='bold')
    ax.set_title(f'2D Density: Return vs Score Distribution\n(Correlation: {overall_corr:.3f})',
                fontsize=13, fontweight='bold')
    ax.legend(fontsize=10, loc='upper left')
    ax.grid(True, alpha=0.3, color='white', linewidth=0.5)
    
    output_path2 = os.path.join(output_dir, 'aggregate_density_heatmap.png')
    plt.savefig(output_path2, dpi=150, bbox_inches='tight')
    print(f"✅ Saved: {output_path2}")
    plt.close()
    
    # ===== VISUALIZATION 3: Sorted Line Plot =====
    print("\nCreating Figure 3: Sorted Relationship...")
    
    # Sort by return and apply moving average to see trend
    df_sorted = df.sort_values('RET').reset_index(drop=True)
    window = max(50, len(df) // 100)  # Adaptive window size
    
    df_sorted['Score_MA'] = df_sorted['Score'].rolling(window=window, center=True).mean()
    df_sorted['RET_pct_MA'] = df_sorted['RET_pct'].rolling(window=window, center=True).mean()
    
    fig3, ax = plt.subplots(figsize=(14, 8))
    
    # Plot raw data as scatter (semi-transparent)
    ax.scatter(range(len(df_sorted)), df_sorted['RET_pct'], 
              alpha=0.1, s=10, color='blue', label='Raw Returns')
    ax.scatter(range(len(df_sorted)), df_sorted['Score'] * 10,  # Scale score for visibility
              alpha=0.1, s=10, color='red', label='Raw Score (×10)')
    
    # Plot moving averages
    ax.plot(df_sorted['RET_pct_MA'], linewidth=2.5, color='darkblue', 
           label=f'Return MA ({window}-point)', alpha=0.9)
    ax.plot(df_sorted['Score_MA'] * 10, linewidth=2.5, color='darkred',
           label=f'Score MA (×10, {window}-point)', alpha=0.9)
    
    ax.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.set_xlabel('Observations (sorted by return magnitude)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Value', fontsize=12, fontweight='bold')
    ax.set_title('Score and Return Movement Patterns (Sorted by Return)\nNote: Score scaled ×10 for visibility',
                fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    output_path3 = os.path.join(output_dir, 'aggregate_sorted_movement.png')
    plt.savefig(output_path3, dpi=150, bbox_inches='tight')
    print(f"✅ Saved: {output_path3}")
    plt.close()
    
    # ===== VISUALIZATION 4: Joint Distribution with Marginals =====
    print("\nCreating Figure 4: Joint Distribution...")
    
    fig4 = plt.figure(figsize=(12, 10))
    gs = fig4.add_gridspec(3, 3, hspace=0.05, wspace=0.05,
                           height_ratios=[1, 3, 0.2], width_ratios=[0.2, 3, 1])
    
    # Main scatter plot
    ax_main = fig4.add_subplot(gs[1, 1])
    scatter = ax_main.scatter(df['RET_pct'], df['Score'], 
                             alpha=0.3, s=20, c=df['RET_pct'], 
                             cmap='coolwarm', edgecolors='none')
    
    # Add trend line (with error handling)
    try:
        # Remove any remaining NaN values for polyfit
        valid_mask = np.isfinite(df['RET_pct']) & np.isfinite(df['Score'])
        ret_valid = df.loc[valid_mask, 'RET_pct'].values
        score_valid = df.loc[valid_mask, 'Score'].values
        
        if len(ret_valid) > 2 and np.std(ret_valid) > 0 and np.std(score_valid) > 0:
            z = np.polyfit(ret_valid, score_valid, 1)
            p = np.poly1d(z)
            x_trend = np.linspace(ret_valid.min(), ret_valid.max(), 100)
            ax_main.plot(x_trend, p(x_trend), 'r--', linewidth=2, alpha=0.8,
                        label=f'ρ={overall_corr:.3f}')
        else:
            ax_main.text(0.5, 0.5, f'ρ={overall_corr:.3f}\n(Insufficient variance for trend line)',
                        transform=ax_main.transAxes, ha='center', va='center',
                        fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    except Exception as e:
        print(f"Warning: Could not fit trend line: {e}")
        ax_main.text(0.5, 0.5, f'ρ={overall_corr:.3f}',
                    transform=ax_main.transAxes, ha='center', va='center',
                    fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    ax_main.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.3)
    ax_main.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.3)
    ax_main.set_xlabel('Return (%)', fontsize=12, fontweight='bold')
    ax_main.set_ylabel('Sentiment Score', fontsize=12, fontweight='bold')
    ax_main.legend(fontsize=10)
    ax_main.grid(True, alpha=0.2)
    
    # Top histogram (Return distribution)
    ax_top = fig4.add_subplot(gs[0, 1], sharex=ax_main)
    ax_top.hist(df['RET_pct'], bins=50, color='steelblue', alpha=0.7, edgecolor='black')
    ax_top.set_ylabel('Frequency', fontsize=10)
    ax_top.set_title('Joint Distribution: Return vs Score with Marginals', 
                     fontsize=13, fontweight='bold', pad=10)
    ax_top.tick_params(labelbottom=False)
    ax_top.grid(True, alpha=0.3, axis='y')
    
    # Right histogram (Score distribution)
    ax_right = fig4.add_subplot(gs[1, 2], sharey=ax_main)
    ax_right.hist(df['Score'], bins=50, orientation='horizontal', 
                 color='coral', alpha=0.7, edgecolor='black')
    ax_right.set_xlabel('Frequency', fontsize=10)
    ax_right.tick_params(labelleft=False)
    ax_right.grid(True, alpha=0.3, axis='x')
    
    # Colorbar
    ax_cbar = fig4.add_subplot(gs[2, 1])
    plt.colorbar(scatter, cax=ax_cbar, orientation='horizontal', 
                label='Return (%) - Color Coding')
    
    output_path4 = os.path.join(output_dir, 'aggregate_joint_distribution.png')
    plt.savefig(output_path4, dpi=150, bbox_inches='tight')
    print(f"✅ Saved: {output_path4}")
    plt.close()
    
    # ===== VISUALIZATION 5: Quantile Analysis =====
    print("\nCreating Figure 5: Quantile Analysis...")
    
    # Divide returns into quantiles and compare scores
    df['RET_quintile'] = pd.qcut(df['RET'], q=10, labels=False, duplicates='drop')
    quintile_stats = df.groupby('RET_quintile').agg({
        'RET': ['mean', 'min', 'max'],
        'Score': ['mean', 'std', 'count']
    }).reset_index()
    quintile_stats.columns = ['Quintile', 'RET_mean', 'RET_min', 'RET_max', 
                              'Score_mean', 'Score_std', 'Count']
    quintile_stats['RET_mean_pct'] = quintile_stats['RET_mean'] * 100
    quintile_stats['Score_sem'] = quintile_stats['Score_std'] / np.sqrt(quintile_stats['Count'])
    
    fig5, ax = plt.subplots(figsize=(14, 8))
    
    x_pos = range(len(quintile_stats))
    
    # Bar plot with error bars
    bars = ax.bar(x_pos, quintile_stats['Score_mean'], 
                  yerr=quintile_stats['Score_sem'],
                  capsize=5, alpha=0.7, color='teal', edgecolor='black')
    
    # Color bars by value (gradient)
    colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(quintile_stats)))
    for bar, color in zip(bars, colors):
        bar.set_color(color)
    
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1.5)
    ax.set_xlabel('Return Decile (1=Lowest Returns, 10=Highest Returns)', 
                 fontsize=12, fontweight='bold')
    ax.set_ylabel('Average Sentiment Score', fontsize=12, fontweight='bold')
    ax.set_title('Sentiment Score Distribution Across Return Deciles\n(Error bars show standard error)',
                fontsize=13, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f'{int(q)+1}\n({m:.2f}%)' for q, m in 
                        zip(quintile_stats['Quintile'], quintile_stats['RET_mean_pct'])],
                       fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add text annotations
    for i, (score, ret) in enumerate(zip(quintile_stats['Score_mean'], 
                                          quintile_stats['RET_mean_pct'])):
        ax.text(i, score + 0.05, f'{score:.3f}', ha='center', fontsize=9, fontweight='bold')
    
    output_path5 = os.path.join(output_dir, 'aggregate_quantile_analysis.png')
    plt.savefig(output_path5, dpi=150, bbox_inches='tight')
    print(f"✅ Saved: {output_path5}")
    plt.close()
    
    # ===== Save Statistics =====
    print("\n" + "="*60)
    print("Calculating and saving aggregate statistics...")
    
    stats_dict = {
        'Metric': ['Total_Observations', 'Unique_Tickers', 'Pearson_Correlation',
                   'Spearman_Correlation', 'Mean_Score', 'Median_Score', 'Std_Score',
                   'Mean_RET_pct', 'Median_RET_pct', 'Std_RET_pct',
                   'Score_Min', 'Score_Max', 'RET_Min_pct', 'RET_Max_pct',
                   'Positive_Scores_pct', 'Negative_Scores_pct', 'Neutral_Scores_pct',
                   'Positive_Returns_pct', 'Negative_Returns_pct'],
        'Value': [
            len(df),
            df['Ticker'].nunique() if 'Ticker' in df.columns else 'N/A',
            overall_corr,
            df['Score'].corr(df['RET'], method='spearman'),
            df['Score'].mean(),
            df['Score'].median(),
            df['Score'].std(),
            df['RET_pct'].mean(),
            df['RET_pct'].median(),
            df['RET_pct'].std(),
            df['Score'].min(),
            df['Score'].max(),
            df['RET_pct'].min(),
            df['RET_pct'].max(),
            (df['Score'] > 0).sum() / len(df) * 100,
            (df['Score'] < 0).sum() / len(df) * 100,
            (df['Score'] == 0).sum() / len(df) * 100,
            (df['RET'] > 0).sum() / len(df) * 100,
            (df['RET'] < 0).sum() / len(df) * 100
        ]
    }
    
    stats_df = pd.DataFrame(stats_dict)
    stats_df.to_csv(stats_output_file, index=False)
    print(f"✅ Saved statistics to: {stats_output_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("AGGREGATE ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total Observations: {len(df):,}")
    if 'Ticker' in df.columns:
        print(f"Unique Tickers: {df['Ticker'].nunique()}")
    print(f"\nPearson Correlation: {overall_corr:.4f}")
    print(f"Spearman Correlation: {df['Score'].corr(df['RET'], method='spearman'):.4f}")
    print(f"\nScore Distribution:")
    print(f"  Mean: {df['Score'].mean():.4f}")
    print(f"  Median: {df['Score'].median():.4f}")
    print(f"  Std Dev: {df['Score'].std():.4f}")
    print(f"  Range: [{df['Score'].min():.4f}, {df['Score'].max():.4f}]")
    print(f"  Positive: {(df['Score'] > 0).sum() / len(df) * 100:.2f}%")
    print(f"  Negative: {(df['Score'] < 0).sum() / len(df) * 100:.2f}%")
    print(f"  Neutral: {(df['Score'] == 0).sum() / len(df) * 100:.2f}%")
    print(f"\nReturn Distribution:")
    print(f"  Mean: {df['RET_pct'].mean():.4f}%")
    print(f"  Median: {df['RET_pct'].median():.4f}%")
    print(f"  Std Dev: {df['RET_pct'].std():.4f}%")
    print(f"  Range: [{df['RET_pct'].min():.4f}%, {df['RET_pct'].max():.4f}%]")
    print(f"  Positive: {(df['RET'] > 0).sum() / len(df) * 100:.2f}%")
    print(f"  Negative: {(df['RET'] < 0).sum() / len(df) * 100:.2f}%")
    print("="*60)
    
    print(f"\n✅ Successfully created 5 aggregate visualizations")
    print(f"   1. Binned Analysis (2.5% bins)")
    print(f"   2. 2D Density Heatmap")
    print(f"   3. Sorted Movement Pattern")
    print(f"   4. Joint Distribution with Marginals")
    print(f"   5. Quantile/Decile Analysis")
    print("="*60)

if __name__ == "__main__":
    # Create the aggregate analysis
    create_aggregate_analysis(MERGED_DATA_FILE, OUTPUT_DIR, STATS_OUTPUT_FILE)
