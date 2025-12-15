# Monthly Prediction Pipeline (News → Monthly Sentiment → Evaluation)

This guide explains the monthly workflow built from:

- `data_preprocessing_monthly.py`
- `sentiment_merge_monthly.py`
- `evaluate_monthly.py`
- `evaluate_monthly_visualization.py`

All commands assume the working directory is `TUM/Campus Challenge`.

## 1. Monthly preprocessing
Input: `train_df.csv` (news), `train_return_data.csv` (monthly returns), optional sentiment file (`sentiment_score.csv` or `sentiment_score_simu.csv`).

Steps performed:
1) Merge sentiment into news on `ticker/date` (supports semicolon/BOM headers).
2) Drop news rows whose `link` contains `?.tsrc=rss`.
3) Bucket news timestamps: (t-1 16:00 ET, t 15:59:59 ET] → `date` (day).
4) Trim monthly returns to the news date range.
5) Clean monthly returns: drop `RET` NAs; per ticker sort by `date`, set `N_RET = RET.shift(-1)`, drop tail `N_RET` NAs.
6) Align news to returns per ticker:
   - Drop news later than the last return date.
   - News earlier than the first return date: map to the first return date, store original in `o_date`, `delta_t` = day diff, attach that date’s `RET/N_RET`.
   - Otherwise map to the right endpoint of the return date interval, keep `o_date`, update `date`, `delta_t` = day diff, attach mapped `RET/N_RET`.
7) Output `train_df_monthly.csv`.

Run:
```bash
python3 data_preprocessing_monthly.py \
  --train train_df.csv \
  --returns train_return_data.csv \
  --output train_df_monthly.csv
```

Key columns after preprocessing: `ticker`, `date`, `o_date`, `delta_t` (days), `sentiment`, `RET`, `N_RET`.

## 2. Monthly sentiment fusion
Input: `train_df_monthly.csv` (optional `--input`).

Fusion rules per ticker/date (date is month-end day):
- Time decay: half-life = 5 days on `delta_t`.
- Weighted mean `sentiment_bar`, disagreement penalty `q`, saturation with `tanh(beta * sentiment_bar)` (beta=3.0).
- If only one item on a date, sentiment unchanged; if multiple, fused `sentiment = tanh(...) * q`.
- Drop text columns, collapse `date` to month string (YYYY-MM), ensure unique ticker-month.

Output: `train_df_monthly_fused.csv` (default).

Run:
```bash
python3 sentiment_merge_monthly.py \
  --input train_df_monthly.csv \
  --output train_df_monthly_fused.csv
```

## 3. Monthly evaluation
Input: `train_df_monthly_fused.csv` (drops `date == "2021-06"` before evaluation).

Metrics:
- RankIC (raw/ex, Spearman), HR, IR, t-stat.
- Quantile portfolios (K=4): average bin returns, monotonicity, LS stats (mean/std/IR/annualized Sharpe with √12, t-stat).
- Ties diagnostics (tie rates of y/f, zero-return share) with mean and quartiles.
- Portfolio (top-bottom) stats: NAV, drawdown inputs, mean/std, annualized mean/std (×12, √12), annualized Sharpe, t-stat.

Run:
```bash
python3 evaluate_monthly.py \
  --input train_df_monthly_fused.csv
```

Optional: `--output summary.json`, `--bins 4`.

## 4. Visualization
Generates plots from fused monthly data (drops 2021-06):
- RankIC time series, rolling means (6/12), histogram, cumulative sum.
- Quantile bars with error bars, quantile heatmap over time.
- LS series with rolling means.
- Ties time series + histograms + scatter vs |RankIC|.
- Portfolio: NAV, drawdown, return histogram, rolling Sharpe (12).

Run:
```bash
python3 evaluate_monthly_visualization.py \
  --input train_df_monthly_fused.csv \
  --outdir plots_monthly \
  --bins 4
```

## Notebook hooks
- Monthly preprocessing: cell added to `test.ipynb` calling `preprocess_monthly(...)`.
- Monthly fusion: cell added to run `fuse_sentiment_monthly(...)`.
- Monthly evaluation: cell added to run `evaluate(...)` on fused data.
- Monthly visualization: cell added to run `generate_plots(...)` and save PNGs to `plots_monthly/`.
