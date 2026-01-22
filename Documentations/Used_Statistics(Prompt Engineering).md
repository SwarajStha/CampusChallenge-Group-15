# Statistical Methods and Data Flow Documentation

## Table of Contents
1. [Overview](#overview)
2. [Statistical Methods Used](#statistical-methods-used)
3. [Relevance to Project](#relevance-to-project)
4. [Data Flow for Statistical Analysis](#data-flow-for-statistical-analysis)
5. [plot_data_monthly.py Differences](#plot_data_monthlypy-differences)

---

## Overview

This document provides comprehensive documentation of all statistical methods and mathematical operations used in the Campus Challenge - Investing with AI project. The analysis focuses on quantifying the relationship between sentiment scores (derived from financial headlines) and stock returns to determine if sentiment has predictive power for future market movements.

---

## Statistical Methods Used

### 1. **Z-Score Normalization (Standardization)**

#### Formula:
$$z = \frac{x - \mu}{\sigma}$$

Where:
- $x$ = individual data point
- $\mu$ = mean of the dataset
- $\sigma$ = standard deviation of the dataset
- $z$ = standardized value (z-score)

#### Implementation:
```python
ticker_df['RET_normalized'] = (ticker_df['RET'] - ticker_df['RET'].mean()) / ticker_df['RET'].std()
ticker_df['Score_normalized'] = (ticker_df['Score'] - ticker_df['Score'].mean()) / ticker_df['Score'].std()
```

#### Purpose:
- Transforms both RET and Score to have mean=0 and standard deviation=1
- Allows direct visual comparison of variables with different scales
- Reveals which variable fluctuates more relative to its own baseline
- Essential for comparing sentiment scores (-1 to +1 range) with returns (varying percentage ranges)

#### Interpretation:
- Z-score of 0 = data point is at the mean
- Z-score of +1 = data point is 1 standard deviation above mean
- Z-score of -2 = data point is 2 standard deviations below mean
- Enables identification of outliers (typically |z| > 2 or 3)

---

### 2. **Pearson Correlation Coefficient**

#### Formula:
$$r = \frac{\sum_{i=1}^{n}(x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum_{i=1}^{n}(x_i - \bar{x})^2} \cdot \sqrt{\sum_{i=1}^{n}(y_i - \bar{y})^2}}$$

Where:
- $x_i$ = individual Score values
- $y_i$ = individual RET values  
- $\bar{x}$ = mean of Score
- $\bar{y}$ = mean of RET
- $n$ = number of data points
- $r$ = correlation coefficient (ranges from -1 to +1)

#### Implementation:
```python
correlation = ticker_df['Score'].corr(ticker_df['RET'])
```

#### Purpose:
- Measures linear relationship strength between sentiment and returns
- Quantifies whether positive sentiment tends to coincide with positive returns
- Core metric for evaluating sentiment predictive power

#### Interpretation:
- $r = +1$: Perfect positive correlation (sentiment and returns move together)
- $r = 0$: No linear relationship
- $r = -1$: Perfect negative correlation (sentiment and returns move opposite)
- $|r| > 0.7$: Strong correlation
- $0.3 < |r| < 0.7$: Moderate correlation
- $|r| < 0.3$: Weak correlation

---

### 3. **Rolling Correlation**

#### Formula:
For each window of $w$ consecutive time periods:
$$r_t = \text{Pearson}(X_{t-w+1:t}, Y_{t-w+1:t})$$

Where:
- $X_{t-w+1:t}$ = Score values in the window
- $Y_{t-w+1:t}$ = RET values in the window
- $w$ = window size (5 days for daily, 3 months for monthly)
- $r_t$ = correlation at time $t$

#### Implementation:
```python
# Daily (5-day window)
ticker_df['rolling_corr'] = ticker_df['RET'].rolling(window=5).corr(ticker_df['Score'])

# Monthly (3-month window)
ticker_df['rolling_corr'] = ticker_df['RET'].rolling(window=3).corr(ticker_df['Score'])
```

#### Purpose:
- Captures time-varying relationship between sentiment and returns
- Reveals if correlation strengthens or weakens over time
- Identifies regime changes (e.g., periods where sentiment becomes more/less predictive)
- Useful for detecting structural breaks in the relationship

#### Interpretation:
- Positive rolling correlation: Sentiment and returns moving together in that period
- Negative rolling correlation: Inverse relationship in that period
- Volatile rolling correlation: Unstable/inconsistent relationship
- Stable rolling correlation: Robust relationship across time

---

### 4. **Linear Regression (Trend Line)**

#### Formula:
$$y = mx + b$$

Where:
- $y$ = predicted RET value
- $x$ = Score value
- $m$ = slope (calculated via least squares)
- $b$ = intercept

#### Slope Calculation (Least Squares):
$$m = \frac{\sum_{i=1}^{n}(x_i - \bar{x})(y_i - \bar{y})}{\sum_{i=1}^{n}(x_i - \bar{x})^2}$$

$$b = \bar{y} - m\bar{x}$$

#### Implementation:
```python
z = np.polyfit(ticker_df['Score'], ticker_df['RET_pct'], 1)  # Degree 1 polynomial (linear)
p = np.poly1d(z)  # Create polynomial function
ax3.plot(ticker_df['Score'], p(ticker_df['Score']), "r--", linewidth=2)
```

#### Purpose:
- Visualizes the average relationship between sentiment and returns
- Slope indicates magnitude: how much returns change per unit change in sentiment
- Provides regression equation for prediction

#### Interpretation:
- Positive slope: Higher sentiment → higher expected returns
- Negative slope: Higher sentiment → lower expected returns (contrarian signal)
- Steep slope: Strong sensitivity to sentiment changes
- Flat slope: Weak/no relationship (similar to correlation ≈ 0)

---

### 5. **Descriptive Statistics**

#### Mean (Average):
$$\bar{x} = \frac{1}{n}\sum_{i=1}^{n}x_i$$

#### Standard Deviation:
$$\sigma = \sqrt{\frac{1}{n}\sum_{i=1}^{n}(x_i - \bar{x})^2}$$

#### Implementation:
```python
Avg_RET = ticker_df['RET'].mean()
Avg_Score = ticker_df['Score'].mean()
RET_StdDev = ticker_df['RET'].std()
Score_StdDev = ticker_df['Score'].std()
Min_RET = ticker_df['RET'].min()
Max_RET = ticker_df['RET'].max()
```

#### Purpose:
- Characterize central tendency and dispersion of each variable
- Identify typical sentiment levels and return ranges per ticker
- Detect volatility (high std dev = volatile)
- Provide context for correlation interpretation

---

## Relevance to Project

### **Why These Statistics Matter for Sentiment-Return Analysis**

#### 1. **Correlation as Predictive Power Measure**
- **Core Question**: Can sentiment scores predict future stock returns?
- **Statistical Answer**: Pearson correlation quantifies if sentiment and returns move together
- **Time Offset Logic**: By adding +1 day/month before merging, we test if today's sentiment predicts tomorrow's returns (causal direction)
- **Practical Value**: Positive correlation suggests sentiment could inform trading decisions

#### 2. **Normalization for Fair Comparison**
- **Problem**: Returns vary wildly across tickers (tech stock: ±15%, utility: ±3%)
- **Solution**: Z-scores put all tickers on same scale
- **Benefit**: Can compare correlation strength across different stocks fairly
- **Example**: TSLA's 0.5 correlation with normalized data is comparable to AAPL's 0.5 correlation

#### 3. **Rolling Correlation for Strategy Timing**
- **Problem**: Static correlation might miss changing market dynamics
- **Solution**: Rolling windows show when sentiment becomes more/less useful
- **Application**: Trade more aggressively when rolling correlation is high (sentiment is "working")
- **Example**: Sentiment might be predictive during earnings season but not during macroeconomic crises

#### 4. **Linear Regression for Magnitude Estimation**
- **Problem**: Correlation shows direction but not magnitude
- **Solution**: Slope coefficient shows how much return change per sentiment unit
- **Trading Application**: If slope = 5%, then 0.5 sentiment score → +2.5% expected return
- **Risk Assessment**: Intercept shows baseline return independent of sentiment

#### 5. **Descriptive Statistics for Context**
- **Mean Sentiment**: Indicates overall media tone (positive/negative bias)
- **Mean Return**: Baseline performance (bull/bear market context)
- **Standard Deviations**: Volatility metrics (high std = risky)
- **Min/Max**: Identifies extreme events for outlier analysis

---

## Data Flow for Statistical Analysis

### **Daily Analysis Pipeline**

```
[1] run_analysis.py
    ↓
    Input: Raw headlines CSV (ID, Ticker, Date, Headline, [Tags])
    Process: LLM sentiment scoring via Groq API
    Output: Decision_Testing*.csv (adds Score, Reason)
    
[2] merge_data.py
    ↓
    Input: Decision_Testing*.csv + Daily_Return_Matching_PTD_1.csv
    Process: Add +1 day to sentiment dates → Inner join on (Ticker, Date_adjusted)
    Statistical Rationale: Creates time-lagged dataset for predictive analysis
    Output: Merged_Data_v6.csv (Score_t, RET_t+1 aligned)
    
[3] plot_data.py
    ↓
    Input: Merged_Data_v6.csv
    
    Statistical Operations:
    a) Z-Score Normalization
       - RET_normalized = (RET - mean(RET)) / std(RET)
       - Score_normalized = (Score - mean(Score)) / std(Score)
       - Purpose: Standardize for visual comparison
       
    b) Pearson Correlation
       - correlation = Score.corr(RET)
       - Purpose: Quantify overall linear relationship strength
       
    c) Rolling 5-Day Correlation
       - rolling_corr[t] = corr(Score[t-4:t], RET[t-4:t])
       - Purpose: Track time-varying relationship
       
    d) Linear Regression (OLS)
       - RET_pct = slope * Score + intercept
       - Purpose: Model predictive relationship
       
    e) Descriptive Statistics
       - mean(RET), mean(Score), std(RET), std(Score)
       - min/max for both variables
       - Purpose: Characterize distributions
    
    Output: 
    - Plots/plots_v6/[TICKER]_plot.png (4-panel visualization)
    - Score Statistics/Plot_Statistics_v6.csv (correlation, means, std devs per ticker)
    
[4] Manual Analysis
    ↓
    Input: Plot_Statistics_v6.csv
    
    Statistical Calculations:
    - Portfolio-wide average correlation
    - Identify high-correlation tickers (|r| > threshold)
    - Compare correlation distributions across prompt versions
    - Hypothesis testing (e.g., t-test if mean correlation > 0)
    
    Purpose: Aggregate individual ticker results to portfolio-level insights
```

### **Monthly Analysis Pipeline**

```
[1] run_analysis.py
    ↓
    (Same as daily)
    
[2] average_monthly_scores.py
    ↓
    Input: Decision_Testing*.csv or Merged_Data_v6.csv
    Process: Group by (Ticker, YearMonth) → Calculate mean(Score), mean(RET)
    Statistical Rationale: Aggregation reduces daily noise, reveals longer-term patterns
    Output: Monthly_Averaged_Score_v6.csv (monthly averages)
    
[3] merge_data_monthly.py
    ↓
    Input: Monthly_Averaged_Score_v6.csv + Monthly_Return_Data_sample.csv
    Process: Add +1 month to sentiment dates → Inner join on (Ticker, Date_adjusted)
    Statistical Rationale: Tests if month M sentiment predicts month M+1 returns
    Output: Merged_Monthly_Data_v6.csv (Score_M, RET_M+1 aligned)
    
[4] plot_data_monthly.py
    ↓
    Input: Merged_Monthly_Data_v6.csv
    
    Statistical Operations: (Same as daily but adapted)
    a) Z-Score Normalization (same formula)
    b) Pearson Correlation (same formula)
    c) Rolling 3-Month Correlation (window=3 instead of 5)
       - Rationale: Fewer monthly data points, smaller window appropriate
    d) Linear Regression (same method)
    e) Descriptive Statistics (same metrics)
    
    Key Difference: Monthly aggregation typically yields:
    - Stronger correlations (noise reduction)
    - Smoother rolling correlation curves
    - More stable regression coefficients
    
    Output:
    - Plots/plots_monthly_v6/[TICKER]_monthly_plot.png
    - Score Statistics/Plot_Statistics_Monthly_v6.csv
    
[5] Manual Analysis (Same approach as daily)
```

### **Statistical Data Transformations Summary**

| Stage | Input Data | Statistical Operation | Output Data | Purpose |
|-------|-----------|----------------------|-------------|---------|
| Scoring | Headlines | LLM → Score ∈ [-1,1] | Sentiment values | Quantify qualitative news |
| Time Lag | Score_t, RET_t | Date shift: Score_t → RET_t+1 | Lagged pairs | Enable predictive testing |
| Normalization | Score, RET (raw) | Z = (X - μ)/σ | Z-scores | Comparable scales |
| Correlation | Score, RET pairs | Pearson's r | Single value ∈ [-1,1] | Relationship strength |
| Rolling Corr | Time series | Sliding window corr | Time series of r values | Temporal dynamics |
| Regression | Score (X), RET (Y) | OLS fitting | y = mx + b | Predictive model |
| Aggregation | Daily data | Mean by month | Monthly averages | Noise reduction |

---

## plot_data_monthly.py Differences

### **Key Modifications from Daily Version (plot_data.py)**

#### 1. **Rolling Correlation Window**
- **Daily**: 5-day window
  ```python
  ticker_df['rolling_corr'] = ticker_df['RET'].rolling(window=5).corr(ticker_df['Score'])
  ```
- **Monthly**: 3-month window
  ```python
  ticker_df['rolling_corr'] = ticker_df['RET'].rolling(window=3).corr(ticker_df['Score'])
  ```
- **Rationale**: Monthly data has fewer points; 3-month window balances smoothing with responsiveness
- **Statistical Impact**: Shorter window = more volatile rolling correlation, but necessary to avoid excessive data loss at window edges

#### 2. **Date Formatting**
- **Daily**: `'%Y-%m-%d'` format (e.g., 2021-06-29)
  ```python
  ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
  ```
- **Monthly**: `'%Y-%m'` format (e.g., 2021-06)
  ```python
  ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
  ```
- **Purpose**: Cleaner x-axis labels for month-level granularity

#### 3. **Marker Size**
- **Daily**: `markersize=3`, `scatter s=50`
  ```python
  marker='o', markersize=3
  ax3.scatter(..., s=50)
  ```
- **Monthly**: `markersize=4`, `scatter s=80`
  ```python
  marker='o', markersize=4
  ax3.scatter(..., s=80)
  ```
- **Rationale**: Fewer monthly data points → larger markers improve visibility

#### 4. **Column Handling**
- **Daily**: Uses `'RET'` column directly
- **Monthly**: Explicitly maps to `'RET (monthly)'`
  ```python
  ticker_df['RET'] = ticker_df['RET (monthly)']
  ```
- **Purpose**: Handles merged monthly data with multiple RET columns (from different sources)

#### 5. **Axis Labels**
- **Daily**: "RET (%)" and "5-day window"
- **Monthly**: "Monthly RET (%)" and "3-month window"
- **Purpose**: Clarity about temporal aggregation level

#### 6. **Statistics CSV Columns**
- **Daily**: `'Avg_RET'`, `'Date_Start': ...strftime('%Y-%m-%d')`
- **Monthly**: `'Avg_Monthly_RET'`, `'Date_Start': ...strftime('%Y-%m')`
- **Purpose**: Distinguish monthly vs daily metrics in output files

#### 7. **Insufficient Data Message**
- **Daily**: "need at least 5 points"
- **Monthly**: "need at least 3 months"
- **Purpose**: Adjusted minimum data requirement for rolling correlation

### **Why These Differences Matter**

#### Statistical Perspective:
- **Time Scale Alignment**: Rolling window must match data frequency (can't use 5-unit window on 3-month dataset)
- **Signal-to-Noise**: Monthly aggregation reduces noise but also reduces sample size, requiring careful parameter tuning
- **Seasonal Effects**: Monthly data better captures longer-term trends; daily data captures short-term reactions

#### Practical Application:
- **Daily Analysis**: For day-trading strategies, event studies, immediate sentiment impact
- **Monthly Analysis**: For swing trading, portfolio rebalancing, longer-term sentiment trends
- **Complementary Use**: Strong daily correlation + strong monthly correlation = robust signal across timeframes

### **Statistical Power Considerations**

| Aspect | Daily Analysis | Monthly Analysis |
|--------|---------------|------------------|
| Sample Size | Large (n ≈ 250 trading days/year) | Small (n = 12 months/year) |
| Noise Level | High (daily volatility) | Low (averaging smooths) |
| Correlation Stability | More variable | More stable |
| Rolling Window | 5 days ≈ 2% of annual data | 3 months = 25% of annual data |
| Statistical Significance | Easier to achieve (larger n) | Harder (smaller n) |
| Outlier Impact | Diluted by many points | Amplified by few points |

### **When to Use Each**

- **Use Daily (`plot_data.py`)**: 
  - Testing immediate market reactions to news
  - High-frequency trading research
  - Event studies (earnings, FDA approvals)
  - Need large sample size for statistical power

- **Use Monthly (`plot_data_monthly.py`)**:
  - Fundamental analysis timeframes
  - Smoothing out market noise
  - Identifying persistent sentiment trends
  - Aligning with monthly portfolio reporting

---

## Conclusion

The statistical methods employed in this project form a comprehensive framework for quantifying the sentiment-return relationship:

1. **Z-scores** enable fair comparison across tickers with different volatilities
2. **Pearson correlation** quantifies predictive relationship strength
3. **Rolling correlation** reveals temporal dynamics and regime changes
4. **Linear regression** models magnitude of sentiment impact
5. **Descriptive statistics** provide essential context

The data flows through sentiment scoring → time-lagged merging → statistical analysis → visualization, with each step grounded in rigorous mathematical operations. The dual daily/monthly pipelines provide complementary perspectives on different investment horizons, with `plot_data_monthly.py` appropriately adapted for lower-frequency data through smaller rolling windows and visual adjustments.

These statistics directly address the core research question: **Does sentiment have predictive power for stock returns?** The answer is quantified through correlation coefficients, with time-lagged analysis ensuring causal interpretation rather than mere association.
