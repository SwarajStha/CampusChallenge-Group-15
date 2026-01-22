# Project Criticisms and Limitations

## Table of Contents
1. [LLM-Related Criticisms](#llm-related-criticisms)
2. [Methodological Limitations](#methodological-limitations)
3. [Data Quality Issues](#data-quality-issues)
4. [Statistical Concerns](#statistical-concerns)
5. [Prompt Engineering Challenges](#prompt-engineering-challenges)
6. [Market Dynamics Concerns](#market-dynamics-concerns)
7. [Mitigation Strategies](#mitigation-strategies)

---

## LLM-Related Criticisms

### 1. **Positivity/Neutrality Bias in LLM Outputs**

#### The Problem:
Large Language Models (LLMs) exhibit a systematic bias toward positive and neutral sentiment scores, producing far fewer negative scores than would be statistically expected or appropriate for balanced financial sentiment analysis.

#### Evidence from Our Project:
- Despite explicit instructions to use negative examples (bankruptcy: -0.93, FDA rejection: -0.72, meme stock collapse: -0.81), the model still defaults to positive/neutral scores
- Multiple prompt iterations (v4, v5, v5 variants, v6) failed to fully eliminate this bias
- Even with balanced examples (3 positive, 3 negative) in prompt_v5.txt, negative predictions remain rare

#### Root Causes:

**a) RLHF Training Bias**
- Reinforcement Learning from Human Feedback (RLHF) trains models to be "helpful, harmless, and honest"
- Human evaluators often prefer optimistic, encouraging responses over critical/negative ones
- Models learn to avoid strong negative language to maximize reward signals
- Result: Conservative scoring that gravitates toward neutral/positive

**b) Financial Language Euphemisms**
- Corporate communications inherently use euphemistic language:
  - "Challenges" instead of "problems"
  - "Restructuring" instead of "layoffs"
  - "Below expectations" instead of "failure"
- LLMs trained on this corpus internalize the euphemistic framing
- Models may interpret genuinely negative news through a softened lens

**c) Lack of Financial Domain Specialization**
- General-purpose LLMs lack specific training on financial sentiment nuances
- May not recognize subtle negative signals that financial experts would catch
- Overly literal interpretation of headlines rather than reading between the lines

#### Impact on Results:
- **Correlation underestimation**: If true negative sentiment is scored as neutral (0) instead of negative (-0.7), correlation with negative returns is artificially weakened
- **Trading strategy failures**: A system that rarely predicts negative sentiment cannot effectively signal short positions or risk avoidance
- **Skewed distribution**: Score distribution clustered around +0.2 to +0.5, rather than symmetric around 0
- **Reduced predictive power**: If 80% of scores are positive but only 60% of returns are positive, the signal is diluted

---

### 2. **Lack of Financial Context Understanding**

#### The Problem:
LLMs may lack deep understanding of financial market mechanics, making scores superficial rather than reflecting true market impact.

#### Examples:
- "Stock rises 5%" might be scored positively, but if the sector rose 10%, it's actually underperformance (negative)
- "Earnings beat estimates by 2%" scored positively, but if guidance is lowered, net sentiment should be negative
- "CEO resignation" could be positive (removing incompetent leadership) or negative (instability)

#### Our Approach:
- We attempted to address this with persona-based prompts (NOVICE, FANATIC, DAY/SWING, LONG-TERM)
- Regime detection (MEME vs NORMAL) tries to contextualize market conditions
- However, LLM still lacks real-time market data, historical context, and cross-asset correlations

---

### 3. **Inconsistency Across Prompt Formats**

#### The Problem:
Different prompt structures yield different sentiment distributions, making results sensitive to prompt engineering choices.

#### Evidence:
- Persona-based prompts (v4, v5) produce different score ranges than simple prompts (ziheng_formatted)
- Internal reasoning prompts (v5_only_score_reason) may score differently than explicit persona breakdown
- Regime detection (with/without) changes weighting dramatically (40/20/30/10% vs 20/10/30/40%)

#### Implications:
- Difficult to compare results across prompt versions objectively
- No ground truth to validate which prompt is "correct"
- Results are artifacts of prompt design as much as genuine sentiment

---

## Methodological Limitations

### 4. **Correlation vs. Causation**

#### The Problem:
Even strong correlation between sentiment and returns does not prove that sentiment *causes* returns.

#### Confounding Factors:
- **Mutual causation**: Both sentiment and returns might be driven by underlying fundamentals (e.g., actual earnings)
- **Reverse causality**: Rising stock prices might generate positive news coverage, not vice versa
- **Omitted variables**: Macroeconomic conditions, sector trends, market-wide sentiment affect both

#### Our Time-Lag Approach:
- Adding +1 day/month before merging attempts to establish temporal precedence
- However, this doesn't eliminate confounders or prove causal mechanism
- **Example**: If earnings are announced on Day 0, headlines on Day 0 and returns on Day 1 are both caused by the earnings, not each other

---

### 5. **Look-Ahead Bias Potential**

#### The Problem:
If headlines are published after market close or intraday, using next-day returns may not reflect predictive power.

#### Scenarios:
- **Headline at 4:30 PM (after close)** → Day+1 returns might already be stale if pre-market trading prices it in
- **Headline at 10:00 AM** → Same-day returns already incorporate the information by close
- **Time zone issues**: Global markets react before US markets open

#### Our Approach:
- Blanket +1 day/month adjustment assumes headlines are available before the next trading period
- No timestamp filtering to ensure headlines precede returns measurement
- Could lead to overestimating predictive power if information is already reflected in prices

---

### 6. **Survivorship Bias**

#### The Problem:
Dataset may exclude delisted stocks (bankruptcies, acquisitions), biasing results toward survivors.

#### Impact:
- Missing the most extreme negative sentiment events (companies that failed)
- Correlation estimates skewed toward successful companies
- Underestimating downside risk signals

#### Mitigation:
- Not fully addressed in current methodology
- Would require comprehensive historical database including delisted tickers

---

## Data Quality Issues

### 7. **Headline Selection Bias**

#### The Problem:
Not all headlines are equally important or market-moving.

#### Issues:
- **Media coverage bias**: More headlines for large-cap, popular stocks (TSLA, AAPL) vs small-cap
- **Relevance filtering**: Some headlines are tangential (CEO tweet, office relocation) vs material (earnings, FDA approval)
- **Duplicate information**: Multiple articles covering the same event create redundant sentiment signals

#### Our Approach:
- No weighting by headline importance or source credibility
- All headlines treated equally in averaging (average_monthly_scores.py)
- Could dilute strong signals with noise

---

### 8. **Limited Date Range**

#### The Problem:
Analysis constrained to 2020-2021 period in some cases.

#### Concerns:
- **COVID-19 distortion**: 2020 had extreme volatility, may not generalize
- **Small sample**: ~2 years of monthly data = 24 data points per ticker (minimal for robust statistics)
- **Regime dependence**: Correlation might hold in bull markets but fail in bear markets

---

### 9. **Incomplete Return Data**

#### The Problem:
+1 day/month lag means last headline in dataset has no corresponding return.

#### Impact:
- Data loss at the end of each time series
- If most recent data is most relevant (recency), losing it hurts predictive models

---

## Statistical Concerns

### 10. **Multiple Testing Problem**

#### The Problem:
Testing correlation for many tickers without multiple testing correction inflates false discovery rate.

#### Example:
- If analyzing 50 tickers, expect 2-3 to show "significant" correlation (p < 0.05) by pure chance
- No Bonferroni correction or FDR control applied

#### Implication:
- Some "significant" results may be statistical flukes
- Need to aggregate across tickers or use cross-validation

---

### 11. **Small Rolling Window Issues**

#### The Problem:
Rolling correlation with small windows (5 days, 3 months) is noisy and unstable.

#### Statistical Properties:
- **High variance**: Correlation estimates with n=5 have huge confidence intervals
- **Endpoint effects**: First 5/3 observations have no rolling correlation
- **Sensitivity**: Single outlier can dominate a 5-point window

#### Trade-off:
- Larger windows (20 days, 12 months) = more stable but lag true changes
- Smaller windows = responsive but noisy
- No clear optimal choice

---

### 12. **Non-Normality of Returns**

#### The Problem:
Stock returns have fat tails (extreme events more common than normal distribution predicts).

#### Implications for Our Methods:
- **Pearson correlation** assumes roughly linear relationship, may miss non-linear effects
- **Z-score normalization** assumes normality; outliers can distort
- **Linear regression** sensitive to outliers in fat-tailed data

#### Better Approaches (Not Implemented):
- Spearman rank correlation (robust to outliers)
- Quantile regression
- Robust regression methods

---

## Prompt Engineering Challenges

### 13. **Persona Weight Arbitrariness**

#### The Problem:
Persona weights (NOVICE 20-40%, FANATIC 10-20%, etc.) are subjectively chosen, not empirically validated.

#### Questions:
- Why 20% for NOVICE in NORMAL regime vs 40% in MEME regime?
- Should DAY/SWING always be 30%?
- Do these weights reflect actual investor proportions or importance?

#### Impact:
- Different weight schemes would produce different aggregated scores
- No ground truth to optimize weights against
- Weights are essentially hyperparameters tuned by intuition

---

### 14. **Regime Detection Simplicity**

#### The Problem:
MEME vs NORMAL detection based on keyword matching is crude.

#### Issues:
- **Binary classification**: Reality is continuous spectrum
- **Keyword list completeness**: May miss new slang or evolving terminology
- **Context-free**: "moon" in "moonshot drug trial" vs "stock to the moon" treated identically
- **No temporal evolution**: Meme status changes over time (e.g., GME in 2021 vs 2024)

#### Better Approach (Not Implemented):
- Supervised classification trained on labeled meme/normal stocks
- Sentiment classifier specifically for meme detection
- Incorporating social media metrics (Reddit mentions, Twitter volume)

---

### 15. **Prompt Length and Cost**

#### The Problem:
Detailed persona-based prompts with examples consume many tokens.

#### Trade-offs:
- **Longer prompts** = better instructions but higher API costs and slower inference
- **Shorter prompts** = cheaper but potentially less accurate
- **Example count**: 6 examples (v5) vs 4 examples (ziheng_formatted) - is more always better?

#### Efficiency Concerns:
- For large datasets (thousands of headlines), token costs add up
- Need to balance accuracy vs cost

---

## Market Dynamics Concerns

### 16. **Efficient Market Hypothesis Challenge**

#### The Problem:
If markets are semi-strong efficient, public headline sentiment should already be priced in immediately.

#### Implication:
- Any exploitable sentiment-return correlation should be arbitraged away quickly
- Persistent correlation might indicate:
  - Market inefficiency (unlikely for large-cap stocks)
  - Our sentiment captures something beyond public headlines
  - Data snooping / overfitting to historical period

#### Reality Check:
- High-frequency traders process news in milliseconds
- By the time headlines are published and scored, alpha is likely gone
- Strategy would need real-time scoring, not batch processing

---

### 17. **Transaction Costs Ignored**

#### The Problem:
Correlation analysis doesn't account for real-world trading frictions.

#### Unmodeled Costs:
- Bid-ask spreads
- Commissions
- Market impact (slippage)
- Short borrowing costs
- Taxes

#### Feasibility:
- A strategy showing 0.3 correlation might be unprofitable after costs
- Need to simulate actual trading with transaction costs to validate

---

### 18. **Signal Decay Over Time**

#### The Problem:
If sentiment-return relationship exists, it may weaken as more traders adopt similar strategies.

#### Adaptive Markets:
- Early adopters of sentiment analysis profit
- Others notice and copy
- Alpha decays as strategy becomes crowded
- By the time academic papers publish results, edge is gone

#### Our Static Analysis:
- Assumes relationship is stable across entire date range
- Doesn't test for time-varying strategy effectiveness
- Rolling correlation attempts this but doesn't model strategic adaptation

---

## Mitigation Strategies

### Addressing LLM Bias:
1. **Stronger negative calibration**: Require minimum % of negative scores in prompt
2. **Flip default assumption**: Instruct to assume negative unless clearly positive
3. **Separate negative detection**: Two-stage scoring (detect negativity, then score magnitude)
4. **Different models**: Test Anthropic Claude, GPT-4, or finance-specific models
5. **Ensemble methods**: Average scores from multiple models to reduce individual biases

### Improving Methodology:
1. **Propensity score matching**: Match sentiment events to control periods to isolate causal effects
2. **Event study methodology**: Measure abnormal returns around specific sentiment events
3. **Lead-lag analysis**: Test sentiment at t-1, t-2, t-3, etc. to find optimal lag
4. **Cross-validation**: Out-of-sample testing to avoid overfitting

### Enhancing Data Quality:
1. **Source weighting**: Give more weight to reputable financial news sources
2. **Deduplication**: Cluster similar headlines covering same event
3. **Importance filtering**: Score headlines by market relevance (use tags, article length, source)
4. **Expand date range**: Include multiple market cycles (bull, bear, sideways)

### Statistical Robustness:
1. **Bootstrapping**: Generate confidence intervals for correlation estimates
2. **Multiple testing correction**: Bonferroni, Benjamini-Hochberg FDR control
3. **Robust statistics**: Spearman correlation, median absolute deviation
4. **Cross-sectional analysis**: Pool data across tickers with fixed effects

### Practical Validation:
1. **Paper trading**: Simulate strategy on out-of-sample period
2. **Transaction cost modeling**: Estimate realistic net returns
3. **Risk-adjusted metrics**: Sharpe ratio, maximum drawdown
4. **Comparison to benchmarks**: Does sentiment beat simple momentum?

---

## Conclusion

This project represents a valuable exploration of sentiment-return relationships, but multiple limitations must be acknowledged:

1. **LLM positivity bias** is the most significant technical challenge, partially addressed but not solved
2. **Causal interpretation** is limited despite time-lagged analysis
3. **Statistical power** constrained by sample size and methodological choices
4. **Market efficiency** questions practical exploitability
5. **Prompt engineering** involves subjective design choices affecting results

These criticisms don't invalidate the project—they provide context for interpreting results and directions for future improvement. Correlation findings should be viewed as descriptive statistics about historical relationships rather than guaranteed predictive signals for live trading.

**Key Takeaway**: Use this analysis as a starting point for understanding sentiment-return dynamics, but implement substantial additional validation before deploying capital based on these signals.
