This directory contains all the codes, files, sample data used and the results for the Campus Challenge - Investing with AI project.

Just downloading this directory will not run the code as the Git upload is ignoring files that store the API Key.

## Key Findings

**Sentiment-Based Trading Strategy Performance (July-December 2024)**

✅ **+119% Total Return** (weekly value-weighted long-short strategy over 6 months)  
✅ **+35.48% Gross Alpha** (Fama-French 5-Factor model, annualized)  
✅ **+27.27% Net Alpha** after realistic transaction costs (20 bps per round-trip)  
✅ **t=3.50*** Cross-Sectional Significance (Fama-MacBeth monthly, p<0.01)  
✅ **Factor Independence**: Near-zero betas (Market: -0.20, SMB: -0.20, HML: 0.03), Low R² (28%)  
✅ **Asymmetric Signal Power**: Short leg drives performance (-38.70% alpha vs +1.82% long)  

**Strategic Insights:**
- Weekly rebalancing + value-weighting essential for capturing sentiment signal
- Signal excels at identifying overvalued stocks (strong short leg performance)
- Alpha survives even at high transaction costs (50 bps → +14.94% net alpha)
- Cross-sectional validation confirms time-series factor model results

See [Executive_Summary.md](Executive_Summary.md) for comprehensive analysis and [Presentation_Slides.md](Presentation_Slides.md) for presentation deck.

---

## Directory Structure

```
CampusChallenge-Group-15/
├── .gitignore
├── .env                              ← API key (not tracked in git)
├── requirements.txt                  ← Python dependencies
├── README.md
│
├── Documentations/                   ← Project documentation
│   ├── Analysis Planning (Now-Redundant).md  ← Project planning notes
│   ├── Criticisms.md                 ← Critical analysis and limitations
│   ├── Data Cleaning Methodology.md  ← Detailed data cleaning documentation
│   ├── Used_Statistics(Prompt Engineering).md  ← Statistical methods documentation
│   ├── Factoring Notes.md            ← Factor model analysis notes
│   ├── Fama_Macbeth Notes.md         ← Cross-sectional analysis notes
│   ├── Long-Short Notes.md           ← Long-short strategy notes
│   ├── walkthrough.md                ← Step-by-step project guide
│   └── Final Summaries/              ← Comprehensive reports
│       ├── Executive_Summary.md      ← Full analysis report (50+ pages)
│       └── Presentation_Slides.md    ← Presentation deck (15 slides)
│
├── All_RAW_Returns/                  ← Raw sentiment and return data
│   ├── data_analysis.ipynb           ← Quality assurance and validation notebook
│   ├── sentiments_group 15.csv       ← Raw sentiment data (gitignored, 310MB)
│   ├── returned_data.csv             ← Raw return data (gitignored, 283MB)
│   ├── daily_return_data_filtered.csv ← Filtered returns (gitignored, 60MB)
│   ├── ticker_mismatches.csv         ← Ticker validation report
│   └── Extracted Files/              ← Cleaned sentiment extractions
│       └── Final Extracted File.csv  ← Validated, sorted sentiment data
│
├── data/                             ← Cleaned and processed data
│   ├── data.ipynb                    ← Data exploration and analysis
│   ├── daily_return_data_cleaned.csv ← Cleaned returns sorted by ticker+date
│   ├── daily_return_data_datefiltered.csv ← Date-filtered returns
│   ├── signal_return_panel.csv       ← Combined signal-return panel
│   ├── signal_return_panel_cleaned.csv ← Cleaned panel data
│   ├── signal_return_panel_cleaned(2).csv ← Final cleaned panel
│   ├── train_return_data_daily.csv   ← Training data (daily frequency)
│   ├── Full Extracted File (sorted).csv ← Sorted sentiment data
│   ├── Fama_French/                  ← Fama-French factor data
│   │   ├── F-F_Research_Data_Factors_daily.csv
│   │   ├── F-F_Research_Data_5_Factors_2x3_daily.csv
│   │   └── ... (monthly versions)
│   └── Panel_Validation/             ← Panel validation outputs
│
├── Portfolio/                        ← Portfolio backtesting and analysis
│   ├── portfolio_backtest.py         ← Portfolio construction and backtesting
│   ├── Analysis_Notes.md             ← Portfolio analysis documentation
│   ├── portfolio_comparison_all_configs.csv ← Configuration comparison results
│   ├── portfolio_returns_*.csv       ← Returns by strategy (weekly/monthly, equal/value)
│   └── portfolio_summary_*.csv       ← Performance summaries by strategy
│
├── sample-data/                      ← Sample data for testing
│   ├── API_test.csv
│   ├── API_test_v2.csv
│   ├── Daily_Return_Matching_PTD_1.csv
│   ├── Full_TestData.csv
│   ├── Full_TestData_DailyReturns.csv
│   ├── Full_TestData_MonthlyReturns.csv
│   ├── Monthly_Return_Data_sample.csv
│   └── Prompt_Testing_Data_1.csv
│
├── Prompt Resources/                 ← Prompting ideas and notes
│   └── Prompting Idea Notes.txt
│
├── prompts/                          ← Prompt engineering versions
│   ├── prompt_v1.txt
│   ├── prompt_v2.txt
│   ├── prompt_v3.txt
│   ├── prompt_v4.txt                 ← Persona-based with MEME/NORMAL regime
│   ├── prompt_v5.txt                 ← Improved v4 with balanced examples
│   ├── prompt_v5(only_score_reason).txt  ← Clean output format (no intermediate reasoning)
│   ├── prompt_v5(without_Regime).txt     ← Equal weights, no regime detection
│   ├── prompt_v6.txt                 ← Includes tags for article context
│   ├── prompt_ziheng.txt
│   └── prompt_ziheng_formatted.txt
│
├── src/                              ← Source code
│   ├── api_client.py                 ← Groq API client + call logic
│   ├── prompt_engine.py              ← Loads prompts + builds messages (supports tags)
│   ├── sentiment_analysis.py         ← Flexible parser (persona + simple formats)
│   ├── run_analysis.py               ← Main pipeline runner (sentiment scoring)
│   │
│   ├── Modeling and Analysis/        ← Data processing and statistical analysis scripts
│   │   ├── Extract_Data.py           ← Parses sentiment text, validates tickers, calculates scores
│   │   ├── data_cleanup_returns.py   ← Filters returns by sentiment tickers, sorts by ticker+date
│   │   ├── prepare_signal_return_panel.py ← Creates signal-return panel structure
│   │   ├── clean_signal_return_panel.py  ← Cleans panel data
│   │   ├── validate_signal_return_panel.py ← Data validation checks
│   │   ├── factor_alpha.py           ← Factor model analysis (CAPM/FF3/FF5) with interpretations
│   │   ├── transaction_cost_analysis.py  ← Net alpha after transaction costs (10/20/50 bps)
│   │   ├── fama_macbeth.py           ← Cross-sectional predictability tests
│   │   └── create_visualizations.py  ← Comprehensive visualization suite (24 charts)
│   │
│   └── Prompt Comparison/            ← Prompt performance comparison utilities
│       ├── merge_data.py             ← Merges daily decision scores with returns (+1 day)
│       ├── merge_data_monthly.py     ← Merges monthly averaged scores with returns (+1 month)
│       ├── average_monthly_scores.py ← Averages daily scores by ticker and month
│       ├── plot_data.py              ← Generates daily correlation plots (4-panel)
│       ├── plot_data_monthly.py      ← Generates monthly correlation plots (4-panel)
│       └── aggregate_analysis.py     ← Aggregate statistics across prompt versions
│
├── results/                          ← Output files
│   ├── Decision Testing Scores/      ← Raw sentiment scoring results
│   │   ├── Decision_Testing1.csv
│   │   ├── Decision_Testing2.csv
│   │   └── ... (multiple versions)
│   │
│   ├── Merged Data/                  ← Merged datasets (scores + returns)
│   │   ├── Merged_Data_v6.csv        ← Daily merged data
│   │   └── Merged_Monthly_Data_v6.csv  ← Monthly aggregated data
│   │
│   ├── Plots/                        ← Sentiment correlation visualizations
│   │   ├── plots_v6/                 ← Daily plots per ticker
│   │   └── plots_monthly_v6/         ← Monthly plots per ticker
│   │
│   ├── Score Statistics/             ← Statistical summaries
│   │   ├── Plot_Statistics_v6.csv    ← Daily correlation stats
│   │   └── Plot_Statistics_Monthly_v6.csv  ← Monthly correlation stats
│   │
│   ├── Factor_Models/                ← Factor model analysis outputs
│   │   ├── alpha_full_results.csv    ← All 36 regressions (4 configs × 3 portfolios × 3 models)
│   │   ├── alpha_summary.csv         ← Summary table with significance stars
│   │   ├── net_alpha_after_costs.csv ← Net alpha at different cost scenarios
│   │   └── net_alpha_summary_table.csv ← Cost analysis summary
│   │
│   ├── Fama_MacBeth/                 ← Cross-sectional analysis outputs
│   │   ├── fmb_slopes_monthly.csv    ← Monthly cross-sectional slopes (6 periods)
│   │   ├── fmb_slopes_weekly.csv     ← Weekly cross-sectional slopes (27 periods)
│   │   └── fmb_summary.csv           ← Summary statistics (mean slopes, t-stats, p-values)
│   │
│   └── Figures/                      ← Publication-quality visualizations (300 DPI PNG)
│       ├── Figure Summaries.txt      ← Detailed chart documentation with conclusions
│       │
│       ├── cumulative_returns_monthly_equal.png
│       ├── cumulative_returns_monthly_value.png
│       ├── cumulative_returns_weekly_equal.png
│       ├── cumulative_returns_weekly_value.png
│       ├── cumulative_returns_comparison.png  ← Comparison of all long-short strategies
│       │
│       ├── drawdown_monthly_equal.png
│       ├── drawdown_monthly_value.png
│       ├── drawdown_weekly_equal.png
│       ├── drawdown_weekly_value.png
│       │
│       ├── rolling_sharpe_monthly_equal.png
│       ├── rolling_sharpe_monthly_value.png
│       ├── rolling_sharpe_weekly_equal.png
│       ├── rolling_sharpe_weekly_value.png
│       │
│       ├── performance_summary.png    ← Multi-panel performance dashboard
│       │
│       ├── alpha_comparison.png       ← Alpha across CAPM/FF3/FF5 models
│       ├── r_squared_comparison.png   ← Model explanatory power
│       ├── factor_exposures.png       ← Factor betas (Market/SMB/HML/RMW/CMA)
│       ├── gross_vs_net_alpha.png     ← Transaction cost impact
│       │
│       ├── fama_macbeth_slopes_monthly.png     ← Monthly cross-sectional slopes time-series
│       ├── fama_macbeth_slopes_weekly.png      ← Weekly cross-sectional slopes time-series
│       ├── fama_macbeth_distribution_monthly.png  ← Monthly slope distribution
│       ├── fama_macbeth_distribution_weekly.png   ← Weekly slope distribution
│       ├── fama_macbeth_comparison.png         ← Mean slopes and t-stats comparison
│       │
│       └── results_dashboard.png      ← Comprehensive 6-panel results dashboard
│
└── venv/                             ← Virtual environment (not tracked in git)
```

## Key Components

### Data Cleaning and Extraction

#### **Extract_Data.py** (src/Modeling and Analysis/)
- Comprehensive sentiment data extraction and validation pipeline
- Comprehensive sentiment data extraction and validation pipeline
- **Regex-Based Extraction**: Parses unstructured sentiment text using pattern matching for:
  - Headlines (with/without quotes)
  - Investor perspective scores: NOVICE, FANATIC, DAY/SWING, LONG-TERM
  - Market regime classification (MEME/NORMAL)
  - Ticker symbols embedded in sentiment text
  - Pre-calculated FINAL_WEIGHTED scores for validation
- **Sentiment Score Calculation**: 
  - NORMAL regime: `0.20×NOVICE + 0.10×FANATIC + 0.30×DAY/SWING + 0.40×LONG-TERM`
  - MEME regime: `0.40×NOVICE + 0.20×FANATIC + 0.30×DAY/SWING + 0.10×LONG-TERM`
- **Data Quality Validation**:
  - Stage 1: Filters rows with missing required fields (date, ticker, scores, regime)
  - Stage 2: Cross-validates ticker consistency (original vs extracted from sentiment)
  - Removes ~1,272 records with ticker mismatches
  - Standardizes all scores to 6 decimal places
- **Output**: Cleaned CSV with validation columns (Ticker(in_sentiment), Final_Weighted) for comparison
- See [Documentations/Data_Cleaning_Methodology.md](Documentations/Data_Cleaning_Methodology.md) for detailed documentation

#### **data_analysis.ipynb** (All_RAW_Returns/)
- Interactive quality assurance notebook for post-extraction validation
- **Ticker Consistency Analysis**: Identifies mismatches between original and extracted tickers
- **Score Validation**: Compares calculated Sentiment_Score vs extracted Final_Weighted (tolerance: 0.000001)
- Provides detailed reporting on data quality issues with row-level diagnostics

#### **data_cleanup_returns.py** (src/Modeling and Analysis/)
- Cleans daily return data to match sentiment dataset scope
- **Ticker Filtering**: Retains only tickers present in sentiment analysis
- **Date Cleaning**: Removes timestamps, standardizes to YYYY-MM-DD format
- **Sorting**: Orders data by TICKER (alphabetically), then by date (chronologically)
- Provides detailed statistics on records removed and date ranges
- Input: daily_return_data_datefiltered.csv + Final Extracted File.csv
- Output: daily_return_data_cleaned.csv (sorted and filtered)

### Factor Model Analysis & Statistical Validation

#### **factor_alpha.py** (src/Modeling and Analysis/)
- Comprehensive factor model analysis with Newey-West HAC standard errors
- Comprehensive factor model analysis with Newey-West HAC standard errors
- **Models Tested**: CAPM, Fama-French 3-Factor (FF3), Fama-French 5-Factor (FF5)
- **Key Features**:
  - Runs 36 regressions: 4 configurations × 3 portfolios (Long/Short/Long-Short) × 3 models
  - Newey-West SE with 10 lags for daily data (accounts for autocorrelation and heteroskedasticity)
  - Alpha significance testing with t-statistics and p-values
  - Comprehensive interpretations with 8 analysis sections per strategy:
    - α Alpha analysis (magnitude, direction, significance)
    - 📊 Model comparison (R² improvements across CAPM/FF3/FF5)
    - 📈 Alpha stability checks (consistency across specifications)
    - 🧬 Factor exposures (beta interpretation for all factors)
    - ⚖️ Long/short leg breakdown (identifies performance drivers)
    - 💡 Strategy insights (rebalancing frequency, weighting effects)
    - 🎯 Overall assessment with star ratings
- **Output Files**:
  - `results/Factor_Models/alpha_full_results.csv`: Detailed regression results (all 36 regressions)
  - `results/Factor_Models/alpha_summary.csv`: Summary table with significance stars (*** p<0.01, ** p<0.05, * p<0.10)
- **Key Results**: Weekly value-weighted long-short shows +35.48% alpha (FF5), driven primarily by short leg (-38.70% alpha)

#### **transaction_cost_analysis.py** (src/Modeling and Analysis/)
- Validates economic viability of strategies after implementation costs
- **Cost Scenarios**:
  - Low (10 bps): Institutional investors with high liquidity
  - Base (20 bps): Realistic case for most investors
  - High (50 bps): Retail investors or low liquidity
- **Calculation**: Annual cost = Turnover × Cost per trade × Rebalancing frequency
- **Output Files**:
  - `results/Factor_Models/net_alpha_after_costs.csv`: Net alpha under all cost scenarios
  - `results/Factor_Models/net_alpha_summary_table.csv`: Summary comparison table
- **Key Results**: Weekly value-weighted survives with +27.27% net alpha after 20 bps costs (gross alpha +35.48%, costs -8.21%)

#### **fama_macbeth.py** (src/Modeling and Analysis/)
- Cross-sectional predictability tests validating signal from different angle
- **Methodology**: 
  - For each period t, run cross-sectional regression: R_{i,t+1} = a_t + b_t × Signal_{i,t}
  - Collect time-series of slopes {b_1, b_2, ..., b_T}
  - Test if mean(b_t) ≠ 0 using Newey-West standard errors
- **Interpretations**:
  - Positive mean slope → higher sentiment predicts higher returns
  - Statistical significance (t>1.96) → systematic predictive power
  - Economic magnitude → 1-unit signal increase implies b% return change
- **Output Files**:
  - `results/Fama_MacBeth/fmb_slopes_monthly.csv`: 6 monthly cross-sectional slopes
  - `results/Fama_MacBeth/fmb_slopes_weekly.csv`: 27 weekly cross-sectional slopes
  - `results/Fama_MacBeth/fmb_summary.csv`: Mean slopes, t-statistics, p-values, significance
- **Key Results**: Highly significant predictive power (Monthly: t=3.50***, p=0.005; Weekly: t=2.87***, p=0.008)

#### **create_visualizations.py** (src/Modeling and Analysis/)
- Generates 24 publication-quality charts (300 DPI PNG) for report and presentation
- **Portfolio Performance Charts** (14 charts):
  - Cumulative returns for each config (Long/Short/Long-Short lines)
  - Comparison of all long-short strategies
  - Drawdown analysis (peak-to-trough declines)
  - Rolling Sharpe ratios (20-day window)
  - Multi-panel performance summary (returns, Sharpe, volatility, drawdown)
- **Factor Model Charts** (4 charts):
  - Alpha comparison across CAPM/FF3/FF5
  - R² comparison showing model fit
  - Factor exposures (betas for Market/SMB/HML/RMW/CMA)
  - Gross vs net alpha after transaction costs
- **Fama-MacBeth Charts** (5 charts):
  - Time-series of monthly/weekly slopes with t-statistics
  - Distribution histograms of slopes
  - Comparison of mean slopes and significance across frequencies
- **Dashboard** (1 chart):
  - Comprehensive 6-panel results dashboard integrating all key findings
- **Output**: All 24 charts saved to `results/Figures/` with detailed documentation in `Figure Summaries.txt`
- **Styling**: Professional color schemes (green/red/blue for long/short/long-short, orange/purple/teal for CAPM/FF3/FF5)

### Sentiment Analysis Pipeline

#### **api_client.py**
- Manages communication with the Groq API for LLM-based sentiment analysis
- Handles API key loading from environment variables
- Implements error handling and retry logic for API calls
- Returns raw LLM responses to be parsed by sentiment_analysis.py

#### **prompt_engine.py**
- Loads prompt templates from the `prompts/` directory
- Builds structured message payloads for the LLM (system + user messages)
- Supports optional `tags` parameter to include article context/topics
- Enables easy switching between different prompt versions without code changes

#### **sentiment_analysis.py**
- Flexible parser that supports multiple LLM response formats:
  - **Persona-based format**: Extracts NOVICE, FANATIC, DAY/SWING, LONG-TERM scores, detects MEME vs NORMAL regime, calculates weighted score in Python
  - **Simple format**: Extracts "Line 1:" score directly
  - **Fallback parsing**: Handles responses missing labels by detecting standalone numbers + text
- Returns tuple of (score, reason) for each headline
- Critical for handling different prompt versions (v4/v5 vs v6/ziheng_formatted)

#### **run_analysis.py**
- Main entry point for sentiment analysis pipeline
- Reads input CSV with columns: ID_Number, Ticker, Date, Headline, (optional) tags
- Processes each headline through the Groq API using selected prompt
- Extracts date-only format (splits on 'T' to remove timestamps)
- Outputs CSV with: ID_Number, Ticker, Date, Headline, Score, Reason
- Usage: Configure prompt file path and input/output CSV paths at bottom of script

### Data Processing

#### **merge_data.py** (src/Prompt Comparison/)
- Combines daily sentiment scores with daily return data
- **Key feature**: Adds +1 day to decision dates before merging
  - Rationale: Returns are measured after the headline, not same-day
  - Uses `timedelta(days=1)` for date adjustment
- Performs inner join on Ticker and adjusted Date
- Input: Decision_Testing files + Daily_Return_Matching_PTD_1.csv
- Output: Merged_Data_v6.csv with both Score and RET columns

#### **average_monthly_scores.py** (src/Prompt Comparison/)
- Aggregates daily sentiment scores into monthly averages per ticker
- Groups data by `['Ticker', 'YearMonth']` where YearMonth = date.to_period('M')
- Calculates mean of Score and RET for each ticker-month combination
- Rounds values to 3 decimal places for consistency
- Input: Merged daily data (e.g., Merged_Data_v6.csv)
- Output: Monthly_Averaged_Score_v6.csv with Date in YYYY-MM format

#### **merge_data_monthly.py** (src/Prompt Comparison/)
- Combines monthly averaged scores with monthly return data
- **Key feature**: Adds +1 month to decision dates before merging
  - Rationale: Monthly returns are measured the month after the sentiment period
  - Uses `DateOffset(months=1)` for month arithmetic
- Handles YYYY-MM date format (month-level precision)
- Uses `suffixes=('_daily', '_monthly')` to differentiate RET columns if both datasets have RET
- Input: Monthly_Averaged_Score_v6.csv + Monthly_Return_Data_sample.csv
- Output: Merged_Monthly_Data_v6.csv with Score and RET columns

### Visualization

#### **plot_data.py** (src/Prompt Comparison/)
- Generates comprehensive 4-panel visualizations for daily data per ticker:
  1. **Raw Values (dual y-axis)**: Score and RET over time with different scales
  2. **Z-Score Normalized**: Both metrics standardized for direct comparison
  3. **Scatter Plot**: Score vs RET with Pearson correlation coefficient and trend line
  4. **Rolling 5-Day Correlation**: Time-series showing how correlation evolves
- Exports statistical summary CSV with correlations, means, std devs per ticker
- Saves plots to `results/Plots/plots_v6/` directory
- Usage: Configure input CSV path and version number in script

#### **plot_data_monthly.py** (src/Prompt Comparison/)
- Same 4-panel structure as plot_data.py, adapted for monthly data:
  - Uses 'RET (monthly)' column instead of 'RET'
  - Rolling window reduced to 3 months (from 5 days)
  - YYYY-MM date formatting on x-axis
  - Larger scatter plot markers (fewer data points)
- Exports Monthly_Plot_Statistics_v6.csv with monthly correlations
- Saves plots to `results/Plots/plots_monthly_v6/` directory
- Handles lower data density typical of monthly aggregations

## Process Workflows

### Statistical Validation and Analysis Workflow (Factor Models & Cross-Sectional Tests)

1. **Prepare Portfolio Returns**
   - Ensure portfolio return files are in place:
     - `Portfolio/portfolio_returns_monthly_equal.csv`
     - `Portfolio/portfolio_returns_monthly_value.csv`
     - `Portfolio/portfolio_returns_weekly_equal.csv`
     - `Portfolio/portfolio_returns_weekly_value.csv`
   - Each file should contain daily returns with columns: date, Long, Short, Long_Short

2. **Prepare Fama-French Factor Data**
   - Download from Kenneth French Data Library: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
   - Required files in `data/Fama_French/`:
     - `F-F_Research_Data_Factors_daily.csv` (Market, SMB, HML, RF)
     - `F-F_Research_Data_5_Factors_2x3_daily.csv` (adds RMW, CMA)
     - Monthly versions if needed
   - Format: Date in YYYYMMDD format, factors as percentages

3. **Run Factor Model Analysis**
   ```
   python CampusChallenge-Group-15/src/Modeling\ and\ Analysis/factor_alpha.py
   ```
   - **What it does**:
     - Loads 4 portfolio configurations and Fama-French factors
     - Runs 36 regressions (4 configs × 3 portfolios × 3 models)
     - Calculates alpha with Newey-West standard errors (10 lags)
     - Provides comprehensive interpretations (8 sections per strategy)
   - **Outputs**:
     - Console: Detailed interpretations with Unicode formatting (α, β, R², ★ ratings)
     - `results/Factor_Models/alpha_full_results.csv`: All regression coefficients, t-stats, p-values
     - `results/Factor_Models/alpha_summary.csv`: Clean summary table with significance stars
   - **Key Metrics**: Alpha, t-statistics, p-values, R², factor betas (Market/SMB/HML/RMW/CMA)

4. **Run Transaction Cost Analysis**
   ```
   python CampusChallenge-Group-15/src/Modeling\ and\ Analysis/transaction_cost_analysis.py
   ```
   - **What it does**:
     - Takes gross alpha from factor models
     - Calculates annual transaction costs: Turnover × Cost × Rebalancing frequency
     - Tests 3 scenarios: 10 bps (low), 20 bps (base), 50 bps (high)
     - Computes net alpha = gross alpha - costs
   - **Outputs**:
     - Console: Net alpha tables for each cost scenario
     - `results/Factor_Models/net_alpha_after_costs.csv`: Net alpha under all scenarios
     - `results/Factor_Models/net_alpha_summary_table.csv`: Summary comparison
   - **Key Finding**: Weekly value-weighted survives with +27.27% net alpha (20 bps costs)

5. **Run Fama-MacBeth Cross-Sectional Analysis**
   ```
   python CampusChallenge-Group-15/src/Modeling\ and\ Analysis/fama_macbeth.py
   ```
   - **What it does**:
     - Loads signal-return panel data
     - Assigns rebalancing periods (monthly/weekly)
     - Runs cross-sectional regressions for each period
     - Computes mean slopes and Newey-West t-statistics
   - **Input**: `data/signal_return_panel_cleaned(2).csv`
   - **Outputs**:
     - Console: Summary statistics with t-stats and significance
     - `results/Fama_MacBeth/fmb_slopes_monthly.csv`: 6 monthly slopes
     - `results/Fama_MacBeth/fmb_slopes_weekly.csv`: 27 weekly slopes
     - `results/Fama_MacBeth/fmb_summary.csv`: Mean slopes, t-stats, p-values
   - **Key Results**: Monthly t=3.50***, Weekly t=2.87*** (both highly significant)

6. **Generate Comprehensive Visualizations**
   ```
   [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
   $env:PYTHONIOENCODING="utf-8"
   python CampusChallenge-Group-15/src/Modeling\ and\ Analysis/create_visualizations.py
   ```
   - **Prerequisites**: Install visualization libraries if needed:
     ```
     pip install matplotlib seaborn
     ```
   - **What it does**:
     - Creates 24 high-resolution charts (300 DPI PNG)
     - Portfolio performance: cumulative returns, drawdowns, rolling Sharpe, summary
     - Factor models: alpha comparison, R², factor exposures, gross vs net alpha
     - Fama-MacBeth: slope time-series, distributions, comparisons
     - Dashboard: 6-panel comprehensive overview
   - **Outputs**: All 24 charts saved to `results/Figures/`
   - **Note**: Windows PowerShell requires UTF-8 encoding for proper Unicode display

7. **Review Documentation**
   - **Chart Documentation**: `results/Figures/Figure Summaries.txt`
     - Detailed descriptions of all 24 charts
     - Metric definitions and interpretations
     - 2-3 sentence conclusions per chart
   - **Comprehensive Report**: `Documentations/Final Summaries/Executive_Summary.md` (50+ pages)
     - Full methodology, results, discussion, conclusions
     - All tables, statistics, and interpretations
   - **Presentation**: `Documentations/Final Summaries/Presentation_Slides.md` (15 slides)
     - Slide-by-slide content with speaker notes
     - Chart references and timing guidelines
     - Q&A preparation with common questions

### Data Cleaning and Preparation Workflow

1. **Raw Sentiment Extraction**
   ```
   python CampusChallenge-Group-15/src/Modeling\ and\ Analysis/Extract_Data.py
   ```
   - Input: `sentiments_group 15.csv` (raw unstructured sentiment text)
   - Process:
     - Extracts headlines, investor scores, regime, ticker, and FINAL_WEIGHTED using regex
     - Calculates Sentiment_Score using regime-specific weighted formulas
     - Validates ticker consistency (removes ~1,272 mismatches, ~7.5% of data)
     - Filters rows with missing critical fields
     - Standardizes all scores to 6 decimal places
   - Output: `All_RAW_Returns/Extracted Files/Final Extracted File.csv`
   - Statistics: Reports rows removed due to missing data and ticker mismatches

2. **Quality Assurance Validation** (optional but recommended)
   - Open `All_RAW_Returns/data_analysis.ipynb` in Jupyter
   - Run comparison cells to verify:
     - Ticker consistency between original and extracted values
     - Sentiment_Score matches Final_Weighted (within floating-point tolerance)
   - Review any flagged discrepancies before proceeding

3. **Return Data Cleaning**
   ```
   python CampusChallenge-Group-15/src/Modeling\ and\ Analysis/data_cleanup_returns.py
   ```
   - Input: 
     - `data/daily_return_data_datefiltered.csv` (returns for all tickers)
     - `All_RAW_Returns/Extracted Files/Final Extracted File.csv` (validated sentiments)
   - Process:
     - Filters returns to only include tickers with sentiment data
     - Removes timestamps from dates (standardizes to YYYY-MM-DD)
     - **Sorts by TICKER (alphabetically), then by date (chronologically)**
   - Output: `data/daily_return_data_cleaned.csv`
   - Statistics: Reports tickers and records removed, date ranges

4. **Panel Data Preparation** (optional, for advanced analysis)
   ```
   python CampusChallenge-Group-15/src/Modeling\ and\ Analysis/prepare_signal_return_panel.py
   ```
   - Combines sentiment signals with return data in panel format
   - Output: `data/signal_return_panel.csv`

### Daily Sentiment-Return Analysis Workflow

1. **Sentiment Scoring**
   ```
   python src/run_analysis.py
   ```
   - Input: CSV with headlines (ID_Number, Ticker, Date, Headline, [tags])
   - Process: Sends each headline to Groq API using selected prompt template
   - Output: `results/Decision Testing Scores/Decision_Testing*.csv` (adds Score, Reason columns)

2. **Data Preparation**
   - Extract appropriate date range from `train_df.csv` or equivalent dataset
   - Ensure dates are in YYYY-MM-DD format (use `.dt.strftime('%Y-%m-%d')` if needed)
   - Filter for desired year range (e.g., 2020-2021)

3. **Merge with Returns Data**
   ```
   python src/Prompt\ Comparison/merge_data.py
   ```
   - Input: Decision_Testing*.csv + Daily_Return_Matching_PTD_1.csv
   - Process: **Adds +1 day** to sentiment dates, then joins on Ticker and adjusted Date
   - Rationale: Stock returns are measured the day AFTER the headline publication
   - Output: `results/Merged Data/Merged_Data_v6.csv` (Score + RET columns aligned)

4. **Generate Visualizations**
   ```
   python src/Prompt\ Comparison/plot_data.py
   ```
   - Input: Merged_Data_v6.csv
   - Process: Creates 4-panel plots per ticker (raw, normalized, scatter, rolling correlation)
   - Output: 
     - Plots: `results/Plots/plots_v6/[TICKER]_v6.png`
     - Stats: `results/Score Statistics/Plot_Statistics_v6.csv`

5. **Manual Analysis** (if needed)
   - Open `Plot_Statistics_v6.csv` in Excel or pandas
   - Calculate portfolio-wide averages of correlation coefficients
   - Identify tickers with strongest sentiment-return relationships
   - Compare different prompt versions by analyzing separate stats files

### Monthly Sentiment-Return Analysis Workflow

1. **Sentiment Scoring** (same as daily)
   ```
   python src/run_analysis.py
   ```
   - Output: Daily-level sentiment scores

2. **Aggregate to Monthly Averages**
   ```
   python src/Prompt\ Comparison/average_monthly_scores.py
   ```
   - Input: `results/Merged Data/Merged_Data_v6.csv` (or direct from Decision_Testing if merging not yet done)
   - Process: Groups by Ticker and YearMonth, calculates mean Score and RET
   - Output: `results/Merged Data/Monthly_Averaged_Score_v6.csv` (dates in YYYY-MM format)

3. **Data Preparation**
   - Extract monthly return data from `train_return_data.csv` or equivalent
   - Ensure dates are in YYYY-MM format (use `.dt.strftime('%Y-%m')` after datetime conversion)
   - Filter for desired year range

4. **Merge with Monthly Returns**
   ```
   python src/Prompt\ Comparison/merge_data_monthly.py
   ```
   - Input: Monthly_Averaged_Score_v6.csv + Monthly_Return_Data_sample.csv
   - Process: **Adds +1 month** to sentiment dates, then joins on Ticker and adjusted Date
   - Rationale: Monthly returns are measured the month AFTER the sentiment aggregation period
   - Output: `results/Merged Data/Merged_Monthly_Data_v6.csv` (Score + RET aligned with time offset)

5. **Generate Monthly Visualizations**
   ```
   python src/Prompt\ Comparison/plot_data_monthly.py
   ```
   - Input: Merged_Monthly_Data_v6.csv
   - Process: Creates 4-panel plots per ticker with 3-month rolling correlation window
   - Output:
     - Plots: `results/Plots/plots_monthly_v6/[TICKER]_monthly_v6.png`
     - Stats: `results/Score Statistics/Plot_Statistics_Monthly_v6.csv`

6. **Manual Analysis** (if needed)
   - Open `Plot_Statistics_Monthly_v6.csv`
   - Calculate portfolio-wide monthly correlation averages
   - Compare monthly vs daily correlation patterns
   - Monthly data typically shows stronger, clearer trends due to noise reduction

### Important Notes on Time Adjustments

- **Daily Merge (+1 day)**: `merge_data.py` uses `timedelta(days=1)` because market returns are realized the trading day AFTER news publication. Example: Headline on 2021-06-29 is matched with returns from 2021-06-30.

- **Monthly Merge (+1 month)**: `merge_data_monthly.py` uses `DateOffset(months=1)` because monthly returns are calculated for the month FOLLOWING the sentiment period. Example: June 2021 sentiment (2021-06) is matched with July 2021 returns (2021-07).

- These time offsets are critical for causal analysis - measuring the predictive power of sentiment on future returns rather than just correlation with concurrent price movements.

## Output Files Summary

### Factor Model Outputs (`results/Factor_Models/`)

**alpha_full_results.csv**
- Complete regression results for all 36 models (4 configs × 3 portfolios × 3 factor models)
- Columns: config, portfolio, model, alpha, alpha_t, alpha_p, R2, plus coefficients/t-stats/p-values for each factor
- Use for: Detailed analysis of factor exposures and model comparisons

**alpha_summary.csv**
- Clean summary table optimized for reporting
- Columns: config, portfolio, model, alpha (annualized %), t-stat, significance stars (*** / ** / *)
- Use for: Quick reference and inclusion in reports/presentations

**net_alpha_after_costs.csv**
- Net alpha under three cost scenarios: 10 bps, 20 bps, 50 bps per round-trip
- Columns: config, portfolio, gross_alpha, turnover, rebal_freq, cost_10bps through cost_50bps, net_alpha_10bps through net_alpha_50bps
- Use for: Economic viability assessment and sensitivity analysis

**net_alpha_summary_table.csv**
- Comparison table showing which strategies survive transaction costs
- Includes: gross alpha, annual costs, net alpha, viable (Yes/No) flag
- Use for: Quick assessment of implementable strategies

### Fama-MacBeth Outputs (`results/Fama_MacBeth/`)

**fmb_slopes_monthly.csv**
- 6 monthly cross-sectional regression slopes (one per rebalancing period)
- Columns: period, period_start, period_end, slope, t_stat, n_obs
- Use for: Time-series analysis of signal predictive power by month

**fmb_slopes_weekly.csv**
- 27 weekly cross-sectional regression slopes
- Same structure as monthly version
- Use for: Higher frequency analysis of signal effectiveness

**fmb_summary.csv**
- Summary statistics for Fama-MacBeth tests
- Rows: monthly and weekly frequencies
- Columns: frequency, mean_slope, t_statistic, p_value, n_periods, significance
- Use for: Overall assessment of cross-sectional predictability

### Visualization Outputs (`results/Figures/`)

**24 PNG Charts (300 DPI):**

*Portfolio Performance (14 charts):*
- `cumulative_returns_[config].png` (4) - Long/Short/Long-Short lines
- `cumulative_returns_comparison.png` (1) - All long-short strategies
- `drawdown_[config].png` (4) - Peak-to-trough declines
- `rolling_sharpe_[config].png` (4) - 20-day rolling Sharpe ratios
- `performance_summary.png` (1) - 4-panel dashboard

*Factor Models (4 charts):*
- `alpha_comparison.png` - Alpha across CAPM/FF3/FF5
- `r_squared_comparison.png` - Model fit comparison
- `factor_exposures.png` - Betas for 5 factors
- `gross_vs_net_alpha.png` - Transaction cost impact

*Fama-MacBeth (5 charts):*
- `fama_macbeth_slopes_[frequency].png` (2) - Slope time-series with t-stats
- `fama_macbeth_distribution_[frequency].png` (2) - Slope histograms
- `fama_macbeth_comparison.png` (1) - Mean slopes and significance

*Dashboard (1 chart):*
- `results_dashboard.png` - 6-panel comprehensive overview

**Figure Summaries.txt**
- Detailed documentation for all 24 charts
- Each chart includes: filename, metric definition, 2-3 sentence conclusion
- Use for: Understanding chart interpretations and writing captions

## Usage

### Quick Start (For Reproducing Factor Model Analysis)

If you want to jump directly to the statistical validation and visualization:

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install matplotlib seaborn statsmodels
   ```

2. **Run factor model analysis** (requires portfolio returns in `Portfolio/` and Fama-French data in `data/Fama_French/`):
   ```bash
   python CampusChallenge-Group-15/src/Modeling\ and\ Analysis/factor_alpha.py
   python CampusChallenge-Group-15/src/Modeling\ and\ Analysis/transaction_cost_analysis.py
   python CampusChallenge-Group-15/src/Modeling\ and\ Analysis/fama_macbeth.py
   ```

3. **Generate visualizations** (Windows PowerShell):
   ```powershell
   [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
   $env:PYTHONIOENCODING="utf-8"
   python CampusChallenge-Group-15/src/Modeling\ and\ Analysis/create_visualizations.py
   ```

4. **Review outputs**:
   - Statistical results: `results/Factor_Models/` and `results/Fama_MacBeth/`
   - Charts: `results/Figures/` (24 PNG files)
   - Documentation: `Documentations/Final Summaries/Executive_Summary.md` and `Presentation_Slides.md`

### Full Pipeline (From Raw Data)

1. **Install dependencies**: 
   ```
   pip install -r requirements.txt
   ```

2. **Set up API key** in `.env` file:
   ```
   GROQ_API_KEY=your_api_key_here
   ```

3. **Data Cleaning Workflow** (start here for raw data):
   - Run `Extract_Data.py` to clean sentiment data
   - Run `data_cleanup_returns.py` to clean return data
   - (Optional) Validate in `data_analysis.ipynb`

4. **Analysis Workflows**:
   - **Daily analysis**: Follow "Daily Sentiment-Return Analysis Workflow" steps
   - **Monthly analysis**: Follow "Monthly Sentiment-Return Analysis Workflow" steps
   - **Factor models & validation**: Follow "Statistical Validation and Analysis Workflow" steps (NEW)

5. **Review outputs**:
   - Sentiment correlation statistics: `results/Score Statistics/`
   - Sentiment correlation plots: `results/Plots/`
   - Portfolio backtesting: `Portfolio/`
   - Factor model analysis: `results/Factor_Models/` (NEW)
   - Cross-sectional validation: `results/Fama_MacBeth/` (NEW)
   - Publication-quality charts: `results/Figures/` (NEW - 24 charts)
   - Comprehensive report: `Executive_Summary.md` (NEW)
   - Presentation deck: `Presentation_Slides.md` (NEW)

## Documentation

- **[Documentations/Final Summaries/Executive_Summary.md](Documentations/Final Summaries/Executive_Summary.md)**: Comprehensive 50+ page analysis report covering methodology, results, discussion, and conclusions with all statistical findings
- **[Documentations/Final Summaries/Presentation_Slides.md](Documentations/Final Summaries/Presentation_Slides.md)**: 15-slide presentation deck with speaker notes, chart references, and timing guidelines for 10-15 minute presentation
- **[results/Figures/Figure Summaries.txt](results/Figures/Figure Summaries.txt)**: Detailed documentation of all 24 visualizations with metric definitions and data-driven conclusions
- **[Documentations/Data_Cleaning_Methodology.md](Documentations/Data_Cleaning_Methodology.md)**: Comprehensive documentation of data cleaning process, extraction methods, validation steps, and quality assurance procedures
- **[Documentations/walkthrough.md](Documentations/walkthrough.md)**: Step-by-step project walkthrough
- **[Documentations/Analysis Planning (Now-Redundant).md](Documentations/Analysis Planning (Now-Redundant).md)**: Project planning and approach
- **[Documentations/Criticisms.md](Documentations/Criticisms.md)**: Critical analysis and limitations
- **[Documentations/Used_Statistics(Prompt Engineering).md](Documentations/Used_Statistics(Prompt Engineering).md)**: Statistical methods documentation
- **[Portfolio/Analysis_Notes.md](Portfolio/Analysis_Notes.md)**: Portfolio construction and backtesting notes

## Important Notes

### Analysis Pipeline Evolution
This project evolved through multiple stages:
1. **Sentiment Scoring**: LLM-based sentiment analysis using Groq API
2. **Data Cleaning**: Extraction, validation, and merging with returns
3. **Portfolio Construction**: Long-short strategies with 4 configurations
4. **Statistical Validation**: Factor models (CAPM/FF3/FF5) with Newey-West SE
5. **Economic Validation**: Transaction cost analysis at multiple scenarios
6. **Cross-Sectional Validation**: Fama-MacBeth regressions
7. **Visualization**: 24 publication-quality charts for report/presentation
8. **Documentation**: Comprehensive executive summary and presentation slides

The latest additions (Steps 4-8) validate the strategy through rigorous academic methods and provide professional deliverables.

### Data Sorting
- All cleaned data files are sorted by **TICKER** (alphabetically), then by **date** (chronologically)
- This ensures consistent ordering for time-series analysis and panel data operations
- Applied in both sentiment extraction (`Extract_Data.py`) and return cleaning (`data_cleanup_returns.py`)

### Windows PowerShell Unicode Display
When running analysis scripts that output Unicode characters (α, β, R², emojis):
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING="utf-8"
```
This ensures proper display of Greek letters and special characters in console output.