
running python CampusChallenge-Group-15/data/prepare_signal_return_panel.py
============================================================
SIGNAL-RETURN PANEL CREATION
============================================================

Loading data files...
  Sentiment records: 58136
  Sentiment date range: 2024-07-01 00:00:00 to 2024-12-31 00:00:00
  Unique tickers in sentiment: 1111

  Returns records: 142266
  Returns date range: 2024-07-01 00:00:00 to 2024-12-31 00:00:00
  Unique tickers in returns: 1111

Building per-ticker trading calendars...
  Created calendars for 1111 tickers
  Trading days per ticker: min=13, max=256, avg=128.1

Mapping sentiment signals to next trading days (max gap: 5 days)...
  Processed 10000/58136 records...
  Processed 20000/58136 records...
  Processed 30000/58136 records...
  Processed 40000/58136 records...
  Processed 50000/58136 records...

============================================================
MATCHING STATISTICS
============================================================
Total sentiment observations: 58136
Successfully matched: 57880 (99.6%)
No trading day found: 254 (0.4%)
Gap too large (>5 days): 2 (0.0%)

Gap distribution (calendar days):
days_gap
1    43900
2     4390
3     9142
4      447
5        1
Name: count, dtype: int64

Mean gap: 1.41 days
Median gap: 1 days

============================================================
SAVING OUTPUT
============================================================
Output file: CampusChallenge-Group-15\data\signal_return_panel.csv
Records in panel: 57880

Date range: 2024-07-01 00:00:00 to 2024-12-30 00:00:00
Unique tickers: 1111

First 5 rows:
  Ticker signal_date  signal_score return_date       RET        PRC    MV_USD_lag  days_gap
0      A  2024-07-01         0.160  2024-07-02 -0.010863  125.78000  3.717035e+07         1
1      A  2024-07-16         0.135  2024-07-17 -0.018815  133.50000  3.969700e+07         1
2      A  2024-07-19        -0.415  2024-07-22  0.012445  133.42000  3.844826e+07         3
3      A  2024-07-22         0.545  2024-07-23 -0.020762  130.64999  3.892675e+07         1
4      A  2024-07-23         0.225  2024-07-24  0.026866  134.16000  3.811857e+07         1

✅ Panel saved to CampusChallenge-Group-15\data\signal_return_panel.csv


running python CampusChallenge-Group-15/data/validate_signal_return_panel.py

============================================================
SIGNAL-RETURN PANEL VALIDATION
============================================================

Loading signal-return panel...
  Total records: 57880
  Date range (signals): 2024-07-01 00:00:00 to 2024-12-30 00:00:00
  Date range (returns): 2024-07-02 00:00:00 to 2024-12-31 00:00:00

============================================================
COVERAGE ANALYSIS
============================================================
Unique tickers in panel: 1111

Observations per ticker:
  Mean: 52.1
  Median: 45
  Min: 1
  Max: 180

⚠️  Warning: 8 tickers have < 5 observations
     Sample: {'AMTM': 4, 'EXE': 2, 'INGM': 1, 'LOAR': 3, 'PDI': 1}

============================================================
DAILY TICKER COUNT ANALYSIS
============================================================
Trading days with signals: 183

Tickers available per day:
  Mean: 316.3
  Median: 296
  Min: 64
  Max: 652
  Std: 152.1

✅ All days have ≥ 30 tickers (good for portfolio formation)

============================================================
GAP DISTRIBUTION (Signal → Return)
============================================================

Gap frequency:
days_gap
1    43900
2     4390
3     9142
4      447
5        1
Name: count, dtype: int64

Gap statistics:
  Mean: 1.41 days
  Median: 1 days
  Mode: 1 days
  Max: 5 days

✅ Most signals match to next-day returns (expected for weekdays)

============================================================
SIGNAL DISTRIBUTION
============================================================

Signal statistics:
  Mean: 0.2313
  Median: 0.3100
  Std: 0.3725
  Min: -0.9450
  Max: 0.9150

Signal quantiles:
  5%: -0.5300
  25%: 0.0250
  50%: 0.3100
  75%: 0.5300
  95%: 0.7050

============================================================
RETURN DISTRIBUTION
============================================================

Return statistics:
  Mean: 0.000530 (0.0530%)
  Median: 0.000796 (0.0796%)
  Std: 0.025634 (2.5634%)
  Min: -0.406583 (-40.66%)
  Max: 0.559902 (55.99%)

⚠️  1 observations with returns > 50%
     Sample (top 5):
      Ticker return_date       RET  signal_score
47735   SMMT  2024-09-09  0.559902         0.845

Return quantiles:
  1%: -0.071629 (-7.1629%)
  5%: -0.035009 (-3.5009%)
  25%: -0.009664 (-0.9664%)
  50%: 0.000796 (0.0796%)
  75%: 0.011010 (1.1010%)
  95%: 0.034319 (3.4319%)
  99%: 0.070456 (7.0456%)

============================================================
MISSING DATA CHECK
============================================================
⚠️  Missing values found:
RET           4
PRC           1
MV_USD_lag    5
dtype: int64

============================================================
GENERATING VALIDATION PLOTS
============================================================
  Saved validation plots to: ../results/Panel_Validation\panel_validation.png

============================================================
VALIDATION SUMMARY
============================================================
Total observations: 57,880
Unique tickers: 1111
Date range: 2024-07-01 00:00:00 to 2024-12-30 00:00:00
Mean tickers per day: 316.3
Signal-Return correlation: 0.0230

⚠️  Potential issues detected:
   - Extreme return values detected

   Review the detailed output above before proceeding.


+ Plot (panel_validation.png)

============================================================



python CampusChallenge-Group-15/data/clean_signal_return_panel.py   

============================================================
SIGNAL-RETURN PANEL CLEANING
============================================================

Loading signal-return panel...
  Initial records: 57880
  Initial unique tickers: 1111

============================================================
REMOVING TICKERS WITH < 5 OBSERVATIONS
============================================================
Found 8 tickers with < 5 observations:
{'AMTM': 4, 'EXE': 2, 'INGM': 1, 'LOAR': 3, 'PDI': 1, 'TLN': 4, 'TTAN': 2, 'WAY': 2, 'PRMB': 3}

Records to be removed: 22
Records after filtering: 57854
Tickers after filtering: 1102

============================================================
REMOVING ROWS WITH MISSING VALUES
============================================================

Missing values before cleaning:
RET           3
PRC           1
MV_USD_lag    3
dtype: int64

Rows with missing values in ['RET', 'PRC', 'MV_USD_lag']: 4

Sample of rows with missing values:
      Ticker signal_date return_date       RET    PRC  MV_USD_lag
22477    FUN  2024-07-01  2024-07-02       NaN    NaN  5217722.19
43081   PRMB  2024-11-07  2024-11-11       NaN  25.50         NaN
43082   PRMB  2024-11-08  2024-11-11       NaN  25.50         NaN
52509   TXNM  2024-07-31  2024-08-05 -0.036629  40.24         NaN

Records after removing missing values: 57857
Records removed: 4

✅ All missing values removed from critical columns

============================================================
CLEANING SUMMARY
============================================================

Original dataset:
  Records: 57,880
  Unique tickers: 1111
  Date range: 2024-07-01 00:00:00 to 2024-12-30 00:00:00

Cleaned dataset:
  Records: 57,857
  Unique tickers: 1102
  Date range: 2024-07-01 00:00:00 to 2024-12-30 00:00:00

Data removed:
  Records: 26 (0.04%)
  Tickers: 9

Daily ticker counts:
  Original - Mean: 316.3, Min: 64
  Cleaned  - Mean: 316.2, Min: 64

Observations per ticker (cleaned):
  Mean: 52.5
  Median: 45
  Min: 3
  Max: 180

============================================================
SAVING CLEANED PANEL
============================================================
✅ Cleaned panel saved to: CampusChallenge-Group-15\data\signal_return_panel_cleaned.csv
   Records: 57,857
   Tickers: 1102

============================================================
NEXT STEPS
============================================================
1. Run validate_signal_return_panel.py on the cleaned file
   (update PANEL_FILE to 'signal_return_panel_cleaned.csv')
2. Proceed to portfolio construction if validation passes
============================================================


python CampusChallenge-Group-15/Portfolio/portfolio_backtest.py     

============================================================
PORTFOLIO BACKTEST - MULTIPLE CONFIGURATIONS
============================================================

Configurations to run:
  Frequencies: ['monthly', 'weekly']
  Weightings: ['equal', 'value']
  Total backtests: 4

============================================================
RUNNING BACKTEST: MONTHLY / EQUAL-WEIGHT
============================================================
Loading cleaned signal-return panel...
  Records: 57,854
  Tickers: 1102
  Date range: 2024-07-01 00:00:00 to 2024-12-30 00:00:00

Aggregating signals to monthly frequency...
  Rebalance periods: 6
  Total (ticker, period) pairs: 6465

Forming portfolios (top 20% long, bottom 20% short)...
  Valid rebalance periods: 6
  Skipped periods (< 20 tickers): 0
  Total portfolio memberships: 2586

  Average tickers per position:
    Long:  216.2
    Short: 214.8

Assigning equal-weights...
  Weights assigned successfully
  Sample weights (first period):
  Ticker position    weight  signal_score
0   ACIW     long  0.004545      0.498333
1   ACLS     long  0.004545      0.532727
2    AJG     long  0.004545      0.431053
3     AL     long  0.004545      0.426500
4   ALSN     long  0.004545      0.509333

Computing daily portfolio returns...
  Weighted return observations: 18514
C:\Users\swara\OneDrive - TUM\Sem 1\Campus Challenge - Investing with AI\CampusChallenge-Group-15\Portfolio\portfolio_backtest.py:255: FutureWarning: DataFrameGroupBy.apply operated on the grouping columns. This behavior is deprecated, and in a future version of pandas the grouping columns will be excluded from the operation. Either pass `include_groups=False` to exclude the groupings or explicitly select the grouping columns after groupby to silence this warning.
  daily_portfolio_returns = weighted_returns.groupby(['return_date', 'position']).apply(
  Daily return series length: 107
  Date range: 2024-07-31 00:00:00 to 2024-12-31 00:00:00

Calculating performance metrics...

Calculating turnover...
  Average turnover per rebalance: 66.23%

============================================================
PERFORMANCE SUMMARY: MONTHLY / EQUAL-WEIGHT
============================================================

LONG Portfolio:
  Total Return (2024):       -0.99%
  Annualized Return:         -2.31%
  Annualized Volatility:      6.50%
  Sharpe Ratio (rf=0.0%):    -0.33
  Max Drawdown:              -3.68%

SHORT Portfolio:
  Total Return (2024):        0.40%
  Annualized Return:          0.94%
  Annualized Volatility:      8.85%
  Sharpe Ratio (rf=0.0%):     0.15
  Max Drawdown:              -4.43%

LONG_SHORT Portfolio:
  Total Return (2024):       -1.50%
  Annualized Return:         -3.49%
  Annualized Volatility:      4.32%
  Sharpe Ratio (rf=0.0%):    -0.80
  Max Drawdown:              -4.39%

Average Turnover per Rebalance: 66.23%

  Saved daily returns to: CampusChallenge-Group-15\Portfolio\portfolio_returns_monthly_equal.csv
  Saved summary metrics to: CampusChallenge-Group-15\Portfolio\portfolio_summary_monthly_equal.csv

============================================================
RUNNING BACKTEST: MONTHLY / VALUE-WEIGHT
============================================================
Loading cleaned signal-return panel...
  Records: 57,854
  Tickers: 1102
  Date range: 2024-07-01 00:00:00 to 2024-12-30 00:00:00

Aggregating signals to monthly frequency...
  Rebalance periods: 6
  Total (ticker, period) pairs: 6465

Forming portfolios (top 20% long, bottom 20% short)...
  Valid rebalance periods: 6
  Skipped periods (< 20 tickers): 0
  Total portfolio memberships: 2586

  Average tickers per position:
    Long:  216.2
    Short: 214.8

Assigning value-weights...
  Weights assigned successfully
  Sample weights (first period):
  Ticker position    weight  signal_score
0   ACIW     long  0.000852      0.498333
1   ACLS     long  0.000781      0.532727
2    AJG     long  0.011776      0.431053
3     AL     long  0.001035      0.426500
4   ALSN     long  0.001463      0.509333

Computing daily portfolio returns...
  Weighted return observations: 18514
C:\Users\swara\OneDrive - TUM\Sem 1\Campus Challenge - Investing with AI\CampusChallenge-Group-15\Portfolio\portfolio_backtest.py:255: FutureWarning: DataFrameGroupBy.apply operated on the grouping columns. This behavior is deprecated, and in a future version of pandas the grouping columns will be excluded from the operation. Either pass `include_groups=False` to exclude the groupings or explicitly select the grouping columns after groupby to silence this warning.
  daily_portfolio_returns = weighted_returns.groupby(['return_date', 'position']).apply(
  Daily return series length: 107
  Date range: 2024-07-31 00:00:00 to 2024-12-31 00:00:00

Calculating performance metrics...

Calculating turnover...
  Average turnover per rebalance: 69.12%

============================================================
PERFORMANCE SUMMARY: MONTHLY / VALUE-WEIGHT
============================================================

LONG Portfolio:
  Total Return (2024):       -0.40%
  Annualized Return:         -0.94%
  Annualized Volatility:      8.41%
  Sharpe Ratio (rf=0.0%):    -0.07
  Max Drawdown:              -4.33%

SHORT Portfolio:
  Total Return (2024):       -3.12%
  Annualized Return:         -7.20%
  Annualized Volatility:     17.41%
  Sharpe Ratio (rf=0.0%):    -0.34
  Max Drawdown:             -10.73%

LONG_SHORT Portfolio:
  Total Return (2024):        2.00%
  Annualized Return:          4.77%
  Annualized Volatility:     11.85%
  Sharpe Ratio (rf=0.0%):     0.45
  Max Drawdown:              -8.37%

Average Turnover per Rebalance: 69.12%

  Saved daily returns to: CampusChallenge-Group-15\Portfolio\portfolio_returns_monthly_value.csv
  Saved summary metrics to: CampusChallenge-Group-15\Portfolio\portfolio_summary_monthly_value.csv

============================================================
RUNNING BACKTEST: WEEKLY / EQUAL-WEIGHT
============================================================
Loading cleaned signal-return panel...
  Records: 57,854
  Tickers: 1102
  Date range: 2024-07-01 00:00:00 to 2024-12-30 00:00:00

Aggregating signals to weekly frequency...
  Rebalance periods: 27
  Total (ticker, period) pairs: 22190

Forming portfolios (top 20% long, bottom 20% short)...
  Valid rebalance periods: 27
  Skipped periods (< 20 tickers): 0
  Total portfolio memberships: 8881

  Average tickers per position:
    Long:  164.7
    Short: 164.2

Assigning equal-weights...
  Weights assigned successfully
  Sample weights (first period):
  Ticker position    weight  signal_score
0   ACIW     long  0.005848        0.5850
1   ACLS     long  0.005848        0.5925
2    ACM     long  0.005848        0.6100
3   ADSK     long  0.005848        0.5325
4    AEO     long  0.005848        0.6550

Computing daily portfolio returns...
  Weighted return observations: 19765
C:\Users\swara\OneDrive - TUM\Sem 1\Campus Challenge - Investing with AI\CampusChallenge-Group-15\Portfolio\portfolio_backtest.py:255: FutureWarning: DataFrameGroupBy.apply operated on the grouping columns. This behavior is deprecated, and in a future version of pandas the grouping columns will be excluded from the operation. Either pass `include_groups=False` to exclude the groupings or explicitly select the grouping columns after groupby to silence this warning.
  daily_portfolio_returns = weighted_returns.groupby(['return_date', 'position']).apply(
  Daily return series length: 124
  Date range: 2024-07-08 00:00:00 to 2024-12-31 00:00:00

Calculating performance metrics...

Calculating turnover...
  Average turnover per rebalance: 77.99%

============================================================
PERFORMANCE SUMMARY: WEEKLY / EQUAL-WEIGHT
============================================================

LONG Portfolio:
  Total Return (2024):        3.58%
  Annualized Return:          7.41%
  Annualized Volatility:      7.41%
  Sharpe Ratio (rf=0.0%):     1.00
  Max Drawdown:              -3.84%

SHORT Portfolio:
  Total Return (2024):        3.91%
  Annualized Return:          8.11%
  Annualized Volatility:      9.95%
  Sharpe Ratio (rf=0.0%):     0.83
  Max Drawdown:              -5.93%

LONG_SHORT Portfolio:
  Total Return (2024):       -0.48%
  Annualized Return:         -0.97%
  Annualized Volatility:      4.84%
  Sharpe Ratio (rf=0.0%):    -0.18
  Max Drawdown:              -4.15%

Average Turnover per Rebalance: 77.99%

  Saved daily returns to: CampusChallenge-Group-15\Portfolio\portfolio_returns_weekly_equal.csv
  Saved summary metrics to: CampusChallenge-Group-15\Portfolio\portfolio_summary_weekly_equal.csv

============================================================
RUNNING BACKTEST: WEEKLY / VALUE-WEIGHT
============================================================
Loading cleaned signal-return panel...
  Records: 57,854
  Tickers: 1102
  Date range: 2024-07-01 00:00:00 to 2024-12-30 00:00:00

Aggregating signals to weekly frequency...
  Rebalance periods: 27
  Total (ticker, period) pairs: 22190

Forming portfolios (top 20% long, bottom 20% short)...
  Valid rebalance periods: 27
  Skipped periods (< 20 tickers): 0
  Total portfolio memberships: 8881

  Average tickers per position:
    Long:  164.7
    Short: 164.2

Assigning value-weights...
  Weights assigned successfully
  Sample weights (first period):
  Ticker position    weight  signal_score
0   ACIW     long  0.000758        0.5850
1   ACLS     long  0.000853        0.5925
2    ACM     long  0.002120        0.6100
3   ADSK     long  0.009872        0.5325
4    AEO     long  0.000696        0.6550

Computing daily portfolio returns...
  Weighted return observations: 19765
C:\Users\swara\OneDrive - TUM\Sem 1\Campus Challenge - Investing with AI\CampusChallenge-Group-15\Portfolio\portfolio_backtest.py:255: FutureWarning: DataFrameGroupBy.apply operated on the grouping columns. This behavior is deprecated, and in a future version of pandas the grouping columns will be excluded from the operation. Either pass `include_groups=False` to exclude the groupings or explicitly select the grouping columns after groupby to silence this warning.
  daily_portfolio_returns = weighted_returns.groupby(['return_date', 'position']).apply(
  Daily return series length: 124
  Date range: 2024-07-08 00:00:00 to 2024-12-31 00:00:00

Calculating performance metrics...

Calculating turnover...
  Average turnover per rebalance: 78.98%

============================================================
PERFORMANCE SUMMARY: WEEKLY / VALUE-WEIGHT
============================================================

LONG Portfolio:
  Total Return (2024):        5.38%
  Annualized Return:         11.23%
  Annualized Volatility:     12.98%
  Sharpe Ratio (rf=0.0%):     0.88
  Max Drawdown:              -5.67%

SHORT Portfolio:
  Total Return (2024):      -10.88%
  Annualized Return:        -20.87%
  Annualized Volatility:     26.89%
  Sharpe Ratio (rf=0.0%):    -0.73
  Max Drawdown:             -21.92%

LONG_SHORT Portfolio:
  Total Return (2024):       14.95%
  Annualized Return:         32.73%
  Annualized Volatility:     24.07%
  Sharpe Ratio (rf=0.0%):     1.29
  Max Drawdown:              -6.16%

Average Turnover per Rebalance: 78.98%

  Saved daily returns to: CampusChallenge-Group-15\Portfolio\portfolio_returns_weekly_value.csv
  Saved summary metrics to: CampusChallenge-Group-15\Portfolio\portfolio_summary_weekly_value.csv

============================================================
CROSS-CONFIGURATION COMPARISON
============================================================

Long-Short Portfolio Comparison:
configuration frequency weighting  LS_total_return  LS_annualized_return  LS_volatility  LS_sharpe_ratio  LS_max_drawdown  avg_turnover
monthly_equal   monthly     equal        -0.014967             -0.034892       0.043215        -0.800326        -0.043922      0.662341
monthly_value   monthly     value         0.019963              0.047652       0.118462         0.450909        -0.083662      0.691188
 weekly_equal    weekly     equal        -0.004805             -0.009741       0.048380        -0.178331        -0.041462      0.779938
 weekly_value    weekly     value         0.149494              0.327288       0.240694         1.292444        -0.061639      0.789752

  Saved comparison to: CampusChallenge-Group-15\Portfolio\portfolio_comparison_all_configs.csv

============================================================
BACKTEST COMPLETE
============================================================
All results saved to: CampusChallenge-Group-15\Portfolio/
============================================================