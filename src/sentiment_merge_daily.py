from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def fuse_group(
    group: pd.DataFrame,
    half_life_seconds: float,
    beta: float,
    eps: float,
) -> pd.DataFrame:
    """
    Apply sentiment fusion for a single ticker group.
    """
    group = group.sort_values("date")
    fused_rows: list[pd.Series] = []

    for _, day_rows in group.groupby("date", sort=True):
        w = np.power(2.0, -day_rows["delta_t"] / half_life_seconds)
        num = (w * day_rows["sentiment"]).sum()
        den = w.sum()
        sentiment_bar = num / den if den != 0 else np.nan
        q = abs(num) / ((w * day_rows["sentiment"].abs()).sum() + eps)

        if len(day_rows) == 1:
            sentiment_t = day_rows["sentiment"].iloc[0]
        else:
            sentiment_t = np.tanh(beta * sentiment_bar) * q

        fused = day_rows.iloc[0].copy()
        fused["sentiment_bar"] = sentiment_bar
        fused["q"] = q
        fused["sentiment"] = sentiment_t
        fused_rows.append(fused)

    return pd.DataFrame(fused_rows)


def fuse_sentiment(
    df: pd.DataFrame,
    half_life_seconds: float = 14_400,
    beta: float = 3.0,
    eps: float = 1e-6,
) -> pd.DataFrame:
    """
    Run fusion for all tickers and return the fused DataFrame.
    """
    if not {"ticker", "date", "delta_t", "sentiment"}.issubset(df.columns):
        missing = {"ticker", "date", "delta_t", "sentiment"} - set(df.columns)
        raise KeyError(f"Input missing columns: {missing}")

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    grouped = df.groupby("ticker", group_keys=False, sort=True)
    fused = grouped.apply(
        fuse_group,
        half_life_seconds=half_life_seconds,
        beta=beta,
        eps=eps,
    )

    fused = fused.sort_values(["ticker", "date"]).reset_index(drop=True)
    # Drop text-heavy columns not needed downstream.
    drop_cols = [
        "title",
        "content",
        "link",
        "symbols",
        "tags",
        "o_date",
    ]
    fused = fused.drop(columns=[c for c in drop_cols if c in fused.columns], errors="ignore")

    # Guard against accidental duplicates.
    dup_mask = fused.duplicated(subset=["ticker", "date"], keep="first")
    if dup_mask.any():
        fused = fused.loc[~dup_mask].reset_index(drop=True)

    return fused


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fuse intraday sentiments into daily scores with decay and disagreement penalty."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DATA_DIR / "train_df_daily.csv",
        help="Path to the preprocessed train_df_daily CSV.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_DIR / "train_df_daily_fused.csv",
        help="Path to write the fused daily sentiment CSV.",
    )
    parser.add_argument(
        "--half-life-seconds",
        type=float,
        default=14_400,
        help="Half-life for time decay in seconds (default: 14400 = 4 hours).",
    )
    parser.add_argument(
        "--beta",
        type=float,
        default=3.0,
        help="Scaling factor before tanh for multi-headline days (default: 3.0).",
    )
    parser.add_argument(
        "--eps",
        type=float,
        default=1e-6,
        help="Small constant to avoid divide-by-zero in disagreement penalty (default: 1e-6).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.input)
    fused = fuse_sentiment(
        df,
        half_life_seconds=args.half_life_seconds,
        beta=args.beta,
        eps=args.eps,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fused.to_csv(args.output, index=False)

    print(f"Fused sentiment written to {args.output}")
    print(f"Rows: {len(fused)}, columns: {list(fused.columns)}")
    print("Sample:")
    print(fused.head())


if __name__ == "__main__":
    main()
