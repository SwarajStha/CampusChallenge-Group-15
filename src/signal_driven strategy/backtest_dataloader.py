from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def _date_range(path: Path, date_col: str = "date") -> tuple[pd.Timestamp, pd.Timestamp]:
    df = pd.read_csv(path, usecols=[date_col])
    dt = pd.to_datetime(df[date_col], errors="coerce")
    dt = dt.dropna()
    if dt.empty:
        raise ValueError(f"No valid dates in {path}")
    return dt.min(), dt.max()


def _prepare_direction(direction_path: Path) -> pd.DataFrame:
    direction = pd.read_csv(direction_path, usecols=["date", "ticker", "sentiment", "news_count"])
    direction["date"] = pd.to_datetime(direction["date"], errors="coerce").dt.date
    direction["ticker"] = direction["ticker"].astype(str)
    direction["sentiment"] = pd.to_numeric(direction["sentiment"], errors="coerce")
    direction["news_count"] = pd.to_numeric(direction["news_count"], errors="coerce")
    direction = direction.dropna(subset=["date", "ticker"])

    dup_count = int(direction.duplicated(subset=["date", "ticker"]).sum())
    if dup_count:
        print(f"[direction] found {dup_count} duplicate (date,ticker) rows, aggregating.")
        direction = (
            direction.groupby(["date", "ticker"], as_index=False)
            .agg(sentiment=("sentiment", "mean"), news_count=("news_count", "sum"))
        )
    return direction


def build_backtest_daily(
    returns_path: Path,
    news_path: Path,
    direction_path: Path,
    output_path: Path,
) -> pd.DataFrame:
    returns_min, returns_max = _date_range(returns_path, "date")
    news_min, news_max = _date_range(news_path, "date")
    print(f"[range] train_return_data_daily.csv: {returns_min.date()} -> {returns_max.date()}")
    print(f"[range] train_df.csv: {news_min.date()} -> {news_max.date()}")

    returns = pd.read_csv(returns_path)
    required_returns = {"date", "ticker", "N_RET"}
    missing_returns = required_returns - set(returns.columns)
    if missing_returns:
        raise KeyError(f"train_return_data_daily missing required columns: {missing_returns}")

    returns["date"] = pd.to_datetime(returns["date"], errors="coerce").dt.date
    returns["ticker"] = returns["ticker"].astype(str)
    before_rows = len(returns)
    returns = returns.dropna(subset=["date", "ticker"])
    dropped_bad = before_rows - len(returns)
    if dropped_bad:
        print(f"[returns] dropped {dropped_bad} rows with invalid date/ticker.")

    news_min_date = news_min.date()
    news_max_date = news_max.date()
    returns = returns[(returns["date"] >= news_min_date) & (returns["date"] <= news_max_date)].copy()
    returns = returns.sort_values(["date", "ticker"]).reset_index(drop=True)
    if returns.empty:
        raise ValueError("No rows left in returns after clipping to train_df date range.")
    print(f"[returns] rows after clipping to train_df range: {len(returns)}")

    if "N_RET" in returns.columns and pd.isna(returns.iloc[-1]["N_RET"]):
        returns = returns.iloc[:-1].reset_index(drop=True)
        print("[returns] last row had N_RET=NaN after clipping, removed last row.")

    direction = _prepare_direction(direction_path)
    merged = returns.merge(direction, on=["date", "ticker"], how="left")

    nan_before = int(merged.isna().sum().sum())
    numeric_cols = merged.select_dtypes(include=["number"]).columns
    merged[numeric_cols] = merged[numeric_cols].fillna(0)
    nan_after = int(merged.isna().sum().sum())
    print(f"[merge] total NaN before fill: {nan_before}, after fill: {nan_after}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False, float_format="%.8f")
    return merged


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build backtest_daily.csv by clipping return dates and merging daily sentiment/news count."
    )
    parser.add_argument(
        "--returns",
        type=Path,
        default=DATA_DIR / "train_return_data_daily.csv",
        help="Path to train_return_data_daily.csv",
    )
    parser.add_argument(
        "--news",
        type=Path,
        default=DATA_DIR / "train_df.csv",
        help="Path to train_df.csv (used for date range clipping).",
    )
    parser.add_argument(
        "--direction",
        type=Path,
        default=DATA_DIR / "train_df_daily_direction.csv",
        help="Path to train_df_daily_direction.csv (sentiment/news_count source).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_DIR / "backtest_daily.csv",
        help="Path to output backtest_daily.csv",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out = build_backtest_daily(
        returns_path=args.returns,
        news_path=args.news,
        direction_path=args.direction,
        output_path=args.output,
    )
    print(f"[done] saved {len(out)} rows to {args.output}")
    print(out.head())


if __name__ == "__main__":
    main()
