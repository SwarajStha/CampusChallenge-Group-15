# Daily Prediction Pipeline (News → Daily Sentiment → Evaluation)

This doc summarizes the daily workflow built from:
- `Data_preprocessing.py` (daily preprocessing & return alignment)
- `sentiment_merge.py` (daily intraday fusion to one row per ticker-day)
- `evaluate_daily.py` (predictive stats & simple 3-state strategy)
- `evaluate_daily_visualization.py` (plots/diagnostics)

All commands assume `TUM/Campus Challenge` as the working directory.

## 1. Daily preprocessing
Input: `train_df.csv` (news), `train_return_data_daily.csv` (daily returns), sentiment file (`sentiment_score.csv` or `sentiment_score_simu.csv` auto-detected).

Main steps (from `Data_preprocessing.py`):
1) Merge sentiment into news on `ticker/date`.
2) Drop news rows whose `link` contains `?.tsrc=rss`.
3) Bucket timestamps: (t-1 16:00 ET, t 15:59:59 ET] → `date` (day); keep original as `o_date`; compute `delta_t` (secs to 16:00 ET of bucketed day).
4) Clean returns: drop `RET` NA; per ticker sort by `date`, set `N_RET = RET.shift(-1)`, drop tail `N_RET` NA; overwrite `train_return_data_daily.csv`.
5) Align news to returns per ticker; attach `RET/N_RET`; output `train_df_daily.csv`.

Run:
```bash
python3 Data_preprocessing.py
```
Key columns after preprocessing: `ticker`, `date`, `o_date`, `delta_t`, `sentiment`, `RET`, `N_RET`.

## 2. Daily sentiment fusion
Input: `train_df_daily.csv`.

`sentiment_merge.py`:
- Groups by `ticker/date` (intraday multiple headlines).
- Time decay: half-life = 4 hours (8-hour shift already applied), disagreement penalty `q`, saturation `tanh(beta * sentiment_bar)` (beta=3.0); single item keeps raw sentiment.
- Drops text columns; writes fused `train_df_daily_fused.csv`.

Run:
```bash
python3 sentiment_merge.py \
  --input train_df_daily.csv \
  --output train_df_daily_fused.csv
```

## 3. Daily evaluation
Input: `train_df_daily_fused.csv`.

`evaluate_daily.py` computes:
- Predictive stats: Pearson, Spearman, OLS (HAC/Newey-West) beta & t-stat.
- Quantile high–low test (default 30/70): delta, t-test CI, AUC/hit rates.
- Three-state strategy (long/short/flat via quantile thresholds): mean/std/Sharpe (√252), win rate, coverage, long/short breakdown.
- Train/test split (default 60/40) using fixed thresholds from train.

Run:
```bash
python3 evaluate_daily.py --input train_df_daily_fused.csv
```
Options: `--winsorize`, `--q-low/--q-high`, `--nw-lags`, `--split`.

## 4. Daily visualization
`evaluate_daily_visualization.py` produces plots/diagnostics:
- Scatter + fit; binned means; rolling IC (60/120/252); residual diagnostics.
- Quantile bars & High/Mid/Low box; ROC & hit-rate bars.
- Strategy: equity/drawdown/positions/P&L hist; train vs test equity; win-rate diagnostics.

Run:
```bash
python3 evaluate_daily_visualization.py \
  --input train_df_daily_fused.csv \
  --outdir plots_daily
```

## Notebook hooks
`test.ipynb` includes cells for:
- Daily evaluation (`evaluate_daily` functions).
- Daily visualization (`generate_daily_plots`) writing figures to `plots_daily/`.
