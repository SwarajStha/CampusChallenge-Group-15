This directory contains all the codes, files, sample data used and the results for the Campus Challenge - Investing with AI project.

Just downloading this directory will not run the code as the Git upload is ignoring files that store the API Key.

## Directory Structure

```
CampusChallenge-Group-15/
├── .gitignore
├── .env                              ← API key (not tracked in git)
├── requirements.txt                  ← Python dependencies
├── README.md
├── walkthrough.md                    ← Step-by-step project guide
│
├── Analysis_Planning.md              ← Project planning notes
├── Criticisms.md                     ← Critical analysis and limitations
├── Data_Cleaning_Methodology.md     ← Detailed data cleaning documentation
├── Used_Statistics.md                ← Statistical methods documentation
│
├── All_RAW_Returns/                  ← Raw sentiment and return data
│   ├── Extract_Data.py               ← Parses sentiment text, validates tickers, calculates scores
│   ├── data_analysis.ipynb           ← Quality assurance and validation notebook
│   ├── sentiments_group 15.csv       ← Raw sentiment data (gitignored, 310MB)
│   ├── returned_data.csv             ← Raw return data (gitignored, 283MB)
│   ├── daily_return_data_filtered.csv ← Filtered returns (gitignored, 60MB)
│   ├── ticker_mismatches.csv         ← Ticker validation report
│   └── Extracted Files/              ← Cleaned sentiment extractions
│       └── Final Extracted File.csv  ← Validated, sorted sentiment data
│
├── data/                             ← Cleaned and processed data
│   ├── data_cleanup_returns.py       ← Filters returns by sentiment tickers, sorts by ticker+date
│   ├── prepare_signal_return_panel.py ← Creates signal-return panel structure
│   ├── clean_signal_return_panel.py  ← Cleans panel data
│   ├── validate_signal_return_panel.py ← Data validation checks
│   ├── data.ipynb                    ← Data exploration and analysis
│   ├── Notes.md                      ← Data processing notes
│   ├── daily_return_data_cleaned.csv ← Cleaned returns sorted by ticker+date
│   ├── daily_return_data_datefiltered.csv ← Date-filtered returns
│   ├── signal_return_panel.csv       ← Combined signal-return panel
│   ├── signal_return_panel_cleaned.csv ← Cleaned panel data
│   ├── train_return_data_daily.csv   ← Training data (daily frequency)
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
│   ├── merge_data.py                 ← Merges daily decision scores with returns (+1 day)
│   ├── merge_data_monthly.py         ← Merges monthly averaged scores with returns (+1 month)
│   ├── average_monthly_scores.py     ← Averages daily scores by ticker and month
│   ├── plot_data.py                  ← Generates daily correlation plots (4-panel)
│   └── plot_data_monthly.py          ← Generates monthly correlation plots (4-panel)
│
└── results/                          ← Output files
    ├── Decision Testing Scores/      ← Raw sentiment scoring results
    │   ├── Decision_Testing1.csv
    │   ├── Decision_Testing2.csv
    │   └── ... (multiple versions)
    │
    ├── Merged Data/                  ← Merged datasets (scores + returns)
    │   ├── Merged_Data_v6.csv        ← Daily merged data
    │   └── Merged_Monthly_Data_v6.csv  ← Monthly aggregated data
    │
    ├── Plots/                        ← Visualization outputs
    │   ├── plots_v6/                 ← Daily plots per ticker
    │   └── plots_monthly_v6/         ← Monthly plots per ticker
    │
    └── Score Statistics/             ← Statistical summaries
        ├── Plot_Statistics_v6.csv    ← Daily correlation stats
        └── Plot_Statistics_Monthly_v6.csv  ← Monthly correlation stats
```

## Key Components

### Data Cleaning and Extraction

#### **Extract_Data.py** (All_RAW_Returns/)
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
- See [Data_Cleaning_Methodology.md](Data_Cleaning_Methodology.md) for detailed documentation

#### **data_analysis.ipynb** (All_RAW_Returns/)
- Interactive quality assurance notebook for post-extraction validation
- **Ticker Consistency Analysis**: Identifies mismatches between original and extracted tickers
- **Score Validation**: Compares calculated Sentiment_Score vs extracted Final_Weighted (tolerance: 0.000001)
- Provides detailed reporting on data quality issues with row-level diagnostics

#### **data_cleanup_returns.py** (data/)
- Cleans daily return data to match sentiment dataset scope
- **Ticker Filtering**: Retains only tickers present in sentiment analysis
- **Date Cleaning**: Removes timestamps, standardizes to YYYY-MM-DD format
- **Sorting**: Orders data by TICKER (alphabetically), then by date (chronologically)
- Provides detailed statistics on records removed and date ranges
- Input: daily_return_data_datefiltered.csv + Final Extracted File.csv
- Output: daily_return_data_cleaned.csv (sorted and filtered)

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

#### **merge_data.py**
- Combines daily sentiment scores with daily return data
- **Key feature**: Adds +1 day to decision dates before merging
  - Rationale: Returns are measured after the headline, not same-day
  - Uses `timedelta(days=1)` for date adjustment
- Performs inner join on Ticker and adjusted Date
- Input: Decision_Testing files + Daily_Return_Matching_PTD_1.csv
- Output: Merged_Data_v6.csv with both Score and RET columns

#### **average_monthly_scores.py**
- Aggregates daily sentiment scores into monthly averages per ticker
- Groups data by `['Ticker', 'YearMonth']` where YearMonth = date.to_period('M')
- Calculates mean of Score and RET for each ticker-month combination
- Rounds values to 3 decimal places for consistency
- Input: Merged daily data (e.g., Merged_Data_v6.csv)
- Output: Monthly_Averaged_Score_v6.csv with Date in YYYY-MM format

#### **merge_data_monthly.py**
- Combines monthly averaged scores with monthly return data
- **Key feature**: Adds +1 month to decision dates before merging
  - Rationale: Monthly returns are measured the month after the sentiment period
  - Uses `DateOffset(months=1)` for month arithmetic
- Handles YYYY-MM date format (month-level precision)
- Uses `suffixes=('_daily', '_monthly')` to differentiate RET columns if both datasets have RET
- Input: Monthly_Averaged_Score_v6.csv + Monthly_Return_Data_sample.csv
- Output: Merged_Monthly_Data_v6.csv with Score and RET columns

### Visualization

#### **plot_data.py**
- Generates comprehensive 4-panel visualizations for daily data per ticker:
  1. **Raw Values (dual y-axis)**: Score and RET over time with different scales
  2. **Z-Score Normalized**: Both metrics standardized for direct comparison
  3. **Scatter Plot**: Score vs RET with Pearson correlation coefficient and trend line
  4. **Rolling 5-Day Correlation**: Time-series showing how correlation evolves
- Exports statistical summary CSV with correlations, means, std devs per ticker
- Saves plots to `results/Plots/plots_v6/` directory
- Usage: Configure input CSV path and version number in script

#### **plot_data_monthly.py**
- Same 4-panel structure as plot_data.py, adapted for monthly data:
  - Uses 'RET (monthly)' column instead of 'RET'
  - Rolling window reduced to 3 months (from 5 days)
  - YYYY-MM date formatting on x-axis
  - Larger scatter plot markers (fewer data points)
- Exports Monthly_Plot_Statistics_v6.csv with monthly correlations
- Saves plots to `results/Plots/plots_monthly_v6/` directory
- Handles lower data density typical of monthly aggregations

## Process Workflows

### Data Cleaning and Preparation Workflow

1. **Raw Sentiment Extraction**
   ```
   python CampusChallenge-Group-15/All_RAW_Returns/Extract_Data.py
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
   python CampusChallenge-Group-15/data/data_cleanup_returns.py
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
   python CampusChallenge-Group-15/data/prepare_signal_return_panel.py
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
   python src/merge_data.py
   ```
   - Input: Decision_Testing*.csv + Daily_Return_Matching_PTD_1.csv
   - Process: **Adds +1 day** to sentiment dates, then joins on Ticker and adjusted Date
   - Rationale: Stock returns are measured the day AFTER the headline publication
   - Output: `results/Merged Data/Merged_Data_v6.csv` (Score + RET columns aligned)

4. **Generate Visualizations**
   ```
   python src/plot_data.py
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
   python src/average_monthly_scores.py
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
   python src/merge_data_monthly.py
   ```
   - Input: Monthly_Averaged_Score_v6.csv + Monthly_Return_Data_sample.csv
   - Process: **Adds +1 month** to sentiment dates, then joins on Ticker and adjusted Date
   - Rationale: Monthly returns are measured the month AFTER the sentiment aggregation period
   - Output: `results/Merged Data/Merged_Monthly_Data_v6.csv` (Score + RET aligned with time offset)

5. **Generate Monthly Visualizations**
   ```
   python src/plot_data_monthly.py
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

## Usage

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

5. **Review outputs**:
   - Statistics CSV files in `results/Score Statistics/`
   - Visualization plots in `results/Plots/`
   - Portfolio backtesting results in `Portfolio/`

## Documentation

- **[Data_Cleaning_Methodology.md](Data_Cleaning_Methodology.md)**: Comprehensive documentation of data cleaning process, extraction methods, validation steps, and quality assurance procedures
- **[walkthrough.md](walkthrough.md)**: Step-by-step project walkthrough
- **[Analysis_Planning.md](Analysis_Planning.md)**: Project planning and approach
- **[Criticisms.md](Criticisms.md)**: Critical analysis and limitations
- **[Used_Statistics.md](Used_Statistics.md)**: Statistical methods documentation
- **[Portfolio/Analysis_Notes.md](Portfolio/Analysis_Notes.md)**: Portfolio construction and backtesting notes
- **[data/Notes.md](data/Notes.md)**: Data processing notes and observations

## Important Notes

### Data Sorting
- All cleaned data files are sorted by **TICKER** (alphabetically), then by **date** (chronologically)
- This ensures consistent ordering for time-series analysis and panel data operations
- Applied in both sentiment extraction (`Extract_Data.py`) and return cleaning (`data_cleanup_returns.py`)