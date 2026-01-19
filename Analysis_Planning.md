# Portfolio Creation & Performance Analysis — Planning (2024)

This document maps **how to implement the portfolio creation section** (Long-only + Long-Short, plus alpha via factor models and Fama–MacBeth) **using the data currently available in this repo**, and how it should integrate with the existing pipeline described in `README.md` and `Used_Statistics.md`.

Scope note: this is **planning only**. No code changes are made here.

---

## 0) Project intent (end-to-end)

Your workflow is:

1. **LLM sentiment scoring** from 2024 headlines (already implemented; multiple prompt versions).
2. **Transform sentiment → tradable signal** (daily, weekly, or monthly signal formation).
3. **Build Long and Long-Short portfolios** using that signal.
4. **Evaluate performance** over 2024: return, risk, Sharpe.
5. **Evaluate abnormal performance (alpha)** via CAPM / FF3 / FF5.
6. **Test cross-sectional predictability** via Fama–MacBeth.
7. **Conclude prompt quality**: which prompt versions produce more “investable” signals.

---

## 1) Where the repo is today (important for integration)

### 1.1 Existing code pipeline (already in `src/`)

The current pipeline is designed around:

- `src/run_analysis.py`: headline scoring via Groq LLM → CSV with `Ticker`, `Date`, `Score`.
- `src/merge_data.py`: merges daily sentiment with daily returns by **adding +1 day** to the sentiment date.
- `src/average_monthly_scores.py`: aggregates daily merged data into monthly averages.
- `src/merge_data_monthly.py`: merges monthly scores to monthly returns by **adding +1 month**.
- `src/plot_data.py` and `src/plot_data_monthly.py`: correlation/visualization statistics.

**Key design already established in the repo:**
- The merge logic enforces **causality** by shifting the sentiment date forward before merging (t → t+1 day/month).
- Daily vs monthly flows are separated cleanly.

### 1.2 New (current) data you want to use

You requested the portfolio work to use:

1) `All_RAW_Returns/Extracted Files/Extracted_file (7).csv`
- Contains headline-level sentiment outputs already (including a final `Sentiment_Score`).
- Columns observed:
  - `date_day` (YYYY-MM-DD)
  - `Ticker`
  - `Headline` (also `title`)
  - persona components like `NOVICE`, `FANATIC`, `DAY/SWING`, `LONG-TERM`, `REGIME`
  - `Sentiment_Score`

2) `All_RAW_Returns/daily_return_data_filtered.csv`
- Contains daily stock return panel for 2024.
- Columns observed:
  - `date` (YYYY-MM-DD)
  - `TICKER`
  - `PRC`
  - `RET`
  - `SHROUT`
  - `MV_USD` and `MV_USD_lag`

**Implication:** you can now build either equal-weight portfolios or value-weight portfolios using `MV_USD_lag`.

---

## 2) First critical step: define the “tradable timeline” (no look-ahead)

Portfolio backtests often fail due to subtle look-ahead mistakes. This repo already uses a +1 day/+1 month merge convention; you should keep that.

### 2.1 Daily convention (recommended baseline)

- Let the sentiment be formed on **calendar day** `date_day = t`.
- The earliest return you can attribute to that sentiment is the next trading day return `RET_{t+1}`.

**Plan for non-trading days / missing ticker days:**
- The simplest (and consistent with the repo) is to shift by +1 day and do an inner join.
- More realistic (recommended if feasible) is: for each (ticker, sentiment-date), match to the **next available trading day** in the returns panel.
  - This avoids losing observations when the sentiment date is Friday/holiday and +1 day is not a trading day.

### 2.2 Weekly/monthly conventions

If you rebalance weekly or monthly, the timeline becomes:

- Build signal using all headlines observed during the **formation window** (week or month).
- Trade in the subsequent window’s return.

Two clean options:

- **Option A (consistent with current repo logic):**
  - Compute weekly/monthly average sentiment during window W
  - Shift the period forward by 1 (W → W+1)
  - Merge to returns aggregated over W+1

- **Option B (more granular but more work):**
  - Compute daily portfolio weights during formation dates
  - Hold weights constant until next rebalance date
  - Use daily returns to compute realized performance

For your “Master” deliverables, both are acceptable; Option A is simpler.

---

## 3) Signal engineering plan (from headlines to a ranking signal)

Your extracted file is headline-level. Portfolios need a **single signal per ticker per rebalance date**.

### 3.1 Aggregation (headline → daily signal)

For each ticker on each day `t`:

- `signal_raw_{i,t} = mean(Sentiment_Score)` across all headlines for ticker i on day t.

Optional improvements (recommended as robustness checks):

- Winsorize sentiment scores within each day (reduce outlier impact).
- Cross-sectional standardization at each date:
  - `signal_{i,t} = zscore(signal_raw_{i,t} across i)`
- Rolling formation windows:
  - weekly/monthly signal could be mean of daily signals over the period.

### 3.2 What exactly is “Sentiment_Score” for trading?

Because `Extracted_file (7).csv` includes persona component scores, you can run multiple strategies:

- Strategy S0: use `Sentiment_Score` (current final score).
- Strategy S1: use `NOVICE` only (baseline retail-style view).
- Strategy S2: use `FANATIC` only.
- Strategy S3: regime-filtered (NORMAL only, MEME only).

This gives you “prompt/format diagnostics”: if one component produces stronger alpha, you can interpret it.

---

## 4) Portfolio construction plan (Long + Long-Short)

### 4.1 Rebalance frequency: weekly vs monthly (pros/cons)

**Weekly rebalance**
- Pros:
  - Better matches short-lived news sentiment effects
  - More observations for inference (more weeks than months)
  - Often higher raw signal responsiveness
- Cons:
  - Much higher turnover → transaction costs likely dominate
  - More missing data edge cases and microstructure noise
  - More “headline bursts” can cause unstable ranks

**Monthly rebalance**
- Pros:
  - Lower turnover; easier to argue implementability
  - Smoother performance; less noisy
  - Factor models are often used monthly in coursework and common empirical finance setups
- Cons:
  - Can wash out short-term sentiment effects
  - Fewer time periods → weaker statistical power in Fama–MacBeth

**Recommendation for your writeup:**
- Pick **monthly** as the primary “investable” backtest.
- Include **weekly** as a robustness test showing signal responsiveness vs turnover.

### 4.2 Portfolio formation rule (quantile long-short)

At each rebalance date (week-end or month-end):

1. Rank all available tickers by `signal`.
2. Define a long bucket and a short bucket.
   - Example: top 20% long, bottom 20% short.
3. Assign weights:
   - Equal-weight within each leg, or
   - Value-weight using `MV_USD_lag` (recommended as a second spec).
4. Construct long-only and long-short returns.

### 4.3 Handling constraints

Decide and document:

- Minimum number of tickers per rebalance (e.g., at least 30) to avoid small-sample noise.
- If fewer tickers are available, skip the rebalance period or widen quantiles.
- When using value-weight:
  - Use `MV_USD_lag` (lagged cap) to avoid look-ahead.

---

## 5) Performance metrics required (for 2024)

Compute for 2024 for:

- Long-only portfolio
- Short-only portfolio
- Long-short portfolio

### 5.1 Return

- Daily compounded return:
  - `cumret = Π(1 + r_t) - 1`

### 5.2 Risk

- Annualized volatility (daily): `vol = std(r_t) * sqrt(252)`
- Optional (good to include): maximum drawdown

### 5.3 Sharpe ratio

- Sharpe on excess returns:
  - `Sharpe = mean(r_t - rf_t) / std(r_t - rf_t) * sqrt(252)`

If you do not have `rf` in the dataset, you can:
- Use a constant `rf ≈ 0` for a simplified Sharpe (state assumption), or
- Pull daily/monthly risk-free from the factor dataset you use later.

### 5.4 “Sharpe ratios for the companies”

You can compute per-ticker 2024 metrics using `daily_return_data_filtered.csv`:

- Per ticker i:
  - annual return (compounded)
  - annualized volatility
  - Sharpe (same rf assumption)

Then show whether the tickers that your strategy tends to long have better realized Sharpe than those it tends to short.

---

## 6) Abnormal returns / alpha plan (CAPM, FF3, FF5)

### 6.1 Data requirement: factor returns + risk-free

You will need a factor dataset compatible with your frequency (daily or monthly):

- CAPM: Market excess return (MKT-RF) + RF
- FF3: MKT-RF, SMB, HML, RF
- FF5: MKT-RF, SMB, HML, RMW, CMA, RF

**Planning options to obtain factors (choose one):**

1) Download from the Kenneth French Data Library (common in coursework).
- Pros: standard, widely accepted.
- Cons: file format parsing.

2) Use a python downloader (e.g., `pandas_datareader` for Fama–French datasets).
- Pros: quick.
- Cons: may be brittle; depends on internet availability in your environment.

### 6.2 Time-series regression specification

For portfolio excess return series `R_p,t - R_f,t`:

- CAPM:
  - `R_p,t - R_f,t = α + β_m (MKT-RF)_t + ε_t`

- FF3:
  - `R_p,t - R_f,t = α + β_m (MKT-RF)_t + β_s SMB_t + β_h HML_t + ε_t`

- FF5:
  - `R_p,t - R_f,t = α + β_m (MKT-RF)_t + β_s SMB_t + β_h HML_t + β_r RMW_t + β_c CMA_t + ε_t`

**Inference requirement:** use Newey–West (HAC) standard errors to report t-stats for α.

### 6.3 Reporting

For each portfolio (Long, Long-Short):

- α (intercept)
- t-stat(α)
- betas
- R²

Also report α annualized if your returns are daily: `α_annual ≈ α_daily * 252`.

---

## 7) Fama–MacBeth regression plan

Goal: test whether your sentiment signal explains cross-sectional returns.

### 7.1 Basic setup

At each period t (week or month):

1. Run cross-sectional regression across stocks i:

- `R_{i,t+1} = a_t + b_t * Signal_{i,t} + u_{i,t+1}`

2. Save the slope estimate `b_t`.

3. Compute:
- `b̄ = mean_t(b_t)`
- Standard error of `b̄` using time-series correction (Newey–West on the `b_t` series).

### 7.2 Optional controls

If you can compute them from the returns panel, add:

- Momentum: past period return
- Volatility: past period volatility
- Size proxy: log(MV_USD_lag)

These help show the sentiment effect is incremental.

### 7.3 Interpretation

- If `b̄ > 0` and statistically significant, higher sentiment predicts higher next-period returns.
- Compare `b̄` across prompt versions to argue which prompt produces a more predictive signal.

---

## 8) How to map this into your existing repo structure (recommended additions)

This repo already has a clear separation:

- `src/` for code
- `results/` for outputs
- `prompts/` for prompt variants

To keep consistent, plan the portfolio work as new scripts/modules that consume the existing merged datasets (or create a new merge for your raw-return files).

### 8.1 Recommended new outputs (folders)

- `results/Portfolio/`
  - `portfolio_returns_daily_<strategy>.csv`
  - `portfolio_returns_weekly_<strategy>.csv`
  - `portfolio_returns_monthly_<strategy>.csv`
  - `portfolio_summary_<strategy>.csv` (return/vol/Sharpe/turnover)

- `results/Factor_Models/`
  - `alpha_CAPM_<strategy>.csv`
  - `alpha_FF3_<strategy>.csv`
  - `alpha_FF5_<strategy>.csv`

- `results/Fama_MacBeth/`
  - `fmb_slopes_<strategy>.csv`
  - `fmb_summary_<strategy>.csv`

### 8.2 Recommended new scripts (planning names)

- `src/prepare_panel_from_raw.py`
  - Input: `Extracted_file (7).csv`, `daily_return_data_filtered.csv`
  - Output: a clean merged panel with (ticker, date, signal, next-day return, market cap lag)

- `src/portfolio_backtest.py`
  - Input: merged panel
  - Output: daily/weekly/monthly portfolio return series and summary metrics

- `src/factor_alpha.py`
  - Input: portfolio return series + factor data
  - Output: CAPM/FF3/FF5 regression tables with HAC t-stats

- `src/fama_macbeth.py`
  - Input: panel with signal and next-period returns
  - Output: FMB slope series + summary (mean slope, t-stat)

**Note:** these scripts are just planning suggestions; you can also integrate them into existing `merge_data.py` and plotting flows, but separate scripts keeps the repo clean and easier to grade.

---

## 9) Concrete step-by-step execution plan (what you will run later)

### Phase A — Build a clean panel dataset

1. Load sentiment headlines file.
2. Clean dates and standardize ticker column.
3. Aggregate to daily signal per (ticker, date).
4. Load daily returns file.
5. Merge sentiment-day t to return-day t+1 using either:
   - strict +1 day merge, OR
   - next-trading-day mapping.
6. Persist as a CSV in `results/Merged Data/` (or `results/Portfolio/`).

### Phase B — Run portfolio backtests (weekly and monthly)

1. Decide rebalance dates (end of week / end of month).
2. For each rebalance date:
   - compute ranks
   - assign long/short membership
   - compute weights
3. Hold weights until next rebalance.
4. Compute daily return series for:
   - Long
   - Short
   - Long-Short
5. Summarize 2024 performance (return, vol, Sharpe, turnover).

### Phase C — Alpha tests

1. Load factor data at matching frequency.
2. Align by date.
3. Run time-series regressions for each portfolio.
4. Report α and t-stats with Newey–West.

### Phase D — Fama–MacBeth

1. Aggregate to the same frequency as the rebalance period.
2. Run cross-sectional regression each period.
3. Compute mean slope and NW t-stat.
4. Compare slopes across prompt versions.

---

## 10) How this ties back to prompt quality (what to write in the conclusion)

Your final narrative should connect:

- Prompt design choices → distribution of `Sentiment_Score` (noise, extremes, regime sensitivity)
- Signal formation → stable cross-sectional ranking power
- Portfolio performance → economically meaningful Sharpe (and after-cost robustness)
- Alpha + FMB → evidence that returns are not just market beta

A good grading-friendly summary pattern:

- “Prompt vX produces higher long-short Sharpe and significant FF3 alpha.”
- “The Fama–MacBeth slope is positive and significant under monthly formation.”
- “Weekly is higher raw return but higher turnover; monthly is more implementable.”

---

## 11) Open questions to resolve before implementation (quick checklist)

1. Portfolio universe filtering:
   - keep only tickers with at least N trading days and at least K sentiment days.
2. Rebalance definition:
   - choose end-of-week day (Fri vs ISO week) and end-of-month handling.
3. Transaction cost assumption:
   - choose a simple per-turnover bps haircut for robustness.
4. Factor dataset selection:
   - daily vs monthly factors; specify source and units (% vs decimals).
5. Risk-free handling:
   - pulled from factors vs assumed 0.

---

## 12) Decision Log (lock these before implementation)

This is the short list of decisions that determine *most* downstream results. Locking them early makes your results reproducible and makes it easier to justify choices in the final report.

### DL1 — Rebalance frequency (primary spec)
- Decision: weekly vs monthly
- Recommendation: **monthly** as primary (implementable + cleaner inference), **weekly** as robustness.

### DL2 — Signal definition (what exactly is ranked)
- Decision: which sentiment column(s) define the signal
- Recommendation:
  - Primary: daily `Sentiment_Score`, aggregated to the rebalance period by mean.
  - Robustness: run the same pipeline with `NOVICE` and `FANATIC` (and optionally `REGIME` splits).

### DL3 — Signal timing and matching (avoid look-ahead)
- Decision: strict `t + 1 day` merge vs “next trading day” merge
- Recommendation:
  - Prefer “next trading day” mapping for each (ticker, `date_day`) to avoid losing Friday/holiday headlines.
  - If you keep strict +1 day (simpler), report the match rate / dropped observations.

### DL4 — Universe filters (what stocks are eligible each rebalance)
- Decision: minimum data requirements per ticker and per rebalance date
- Recommendation (starting point; adjust after you inspect coverage):
  - Per rebalance date: require at least ~30–50 tickers with valid signals/returns.
  - Per ticker: require a minimum number of trading days in 2024 (e.g., ≥ 120) and minimum signal days (e.g., ≥ 5–10).

### DL5 — Portfolio buckets (how long/short legs are formed)
- Decision: quantile cutoffs
- Recommendation:
  - Primary: top 20% long / bottom 20% short.
  - Robustness: 10% (more extreme, higher turnover) and 30% (more diversified).

### DL6 — Weighting scheme (equal-weight vs value-weight)
- Decision: how you weight names within each leg
- Recommendation:
  - Primary: equal-weight (robust, simplest).
  - Robustness: value-weight using `MV_USD_lag`.
  - Optional safety: cap single-name weights (e.g., 5–10%) to avoid one-stock domination.

### DL7 — Missing returns during holding periods
- Decision: what to do if a constituent has a missing `RET` on a day
- Recommendation:
  - Drop the missing observation for that day and **renormalize weights** across remaining constituents (preferred).
  - Avoid filling missing returns with 0 (biases results).

### DL8 — Return definition and compounding
- Decision: how to aggregate daily returns to weekly/monthly
- Recommendation:
  - Use geometric compounding inside the period: `Π(1 + r_d) - 1`.
  - Use the same approach for portfolio and individual stock summaries.

### DL9 — Risk-free rate and Sharpe definition
- Decision: assume `rf = 0` vs use factor `RF`
- Recommendation:
  - Use `RF` from the same factor dataset used for CAPM/FF regressions.
  - If you temporarily use `rf = 0`, label the metric “Sharpe (rf≈0)” and treat as descriptive.

### DL10 — Factor data source and units (CAPM / FF3 / FF5)
- Decision: where factors come from and whether values are in % or decimals
- Recommendation:
  - Use Kenneth French factors at the matching frequency (daily if your portfolio returns are daily; monthly if you only compute monthly returns).
  - Standardize units immediately (e.g., convert percent to decimals once, then keep consistent everywhere).

### DL11 — Statistical inference settings
- Decision: standard errors for alpha and Fama–MacBeth
- Recommendation:
  - Use Newey–West (HAC) standard errors.
  - Choose a lag rule consistent with your frequency (e.g., 5–10 lags for daily; 3–6 for monthly), and report it.

### DL12 — Transaction cost / turnover robustness
- Decision: whether to report post-cost performance
- Recommendation:
  - Report at least one simple haircut based on turnover (e.g., 10–50 bps per 100% turnover per rebalance) and show weekly vs monthly sensitivity.

---

## Appendix A — Column mapping (current data files)

### A1) Sentiment source (`Extracted_file (7).csv`)

- Date: `date_day`
- Ticker: `Ticker`
- Signal candidates: `Sentiment_Score` (primary), plus `NOVICE`, `FANATIC`, `DAY/SWING`, `LONG-TERM`, `REGIME`

### A2) Returns source (`daily_return_data_filtered.csv`)

- Date: `date`
- Ticker: `TICKER`
- Return: `RET` (appears as decimal)
- Size proxy / weighting: `MV_USD_lag`

---

## Appendix B — Recommended baseline configurations

- Baseline 1 (Monthly, Equal-weight):
  - Signal: monthly mean of daily `Sentiment_Score`
  - Long: top 20%
  - Short: bottom 20%

- Baseline 2 (Weekly, Equal-weight):
  - Signal: weekly mean of daily `Sentiment_Score`
  - Long: top 20%
  - Short: bottom 20%

- Robustness 1 (Value-weight):
  - use `MV_USD_lag` inside each leg

- Robustness 2 (Regime split):
  - run the same strategy restricted to `REGIME == NORMAL` vs `REGIME == MEME`
