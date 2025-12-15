from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


REQUIRED_COLS = {"ticker", "date", "delta_t", "sentiment"}


def fuse_group(
    group: pd.DataFrame,
    half_life_days: float,
    beta: float,
    eps: float,
) -> pd.DataFrame:
    """Fuse sentiments for a single ticker group."""
    fused_rows = []
    for _, day_rows in group.groupby("date", sort=True):
        w = np.power(2.0, -day_rows["delta_t"] / half_life_days)
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


def fuse_sentiment_monthly(
    df: pd.DataFrame,
    half_life_days: float = 5.0,
    beta: float = 3.0,
    eps: float = 1e-6,
) -> pd.DataFrame:
    """Run monthly fusion for all tickers."""
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise KeyError(f"Input missing columns: {missing}")

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    grouped = df.groupby("ticker", group_keys=False, sort=True)
    fused = grouped.apply(
        fuse_group, half_life_days=half_life_days, beta=beta, eps=eps
    )
    fused = fused.sort_values(["ticker", "date"]).reset_index(drop=True)

    # Drop heavy text/meta columns if present.
    drop_cols = ["title", "content", "link", "symbols", "tags", "o_date"]
    fused = fused.drop(columns=[c for c in drop_cols if c in fused.columns], errors="ignore")

    # Collapse date to month (YYYY-MM).
    fused["date"] = fused["date"].dt.to_period("M").astype(str)

    # Ensure no duplicate ticker-month rows remain.
    dup_mask = fused.duplicated(subset=["ticker", "date"], keep="first")
    if dup_mask.any():
        fused = fused.loc[~dup_mask].reset_index(drop=True)

    return fused


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fuse monthly sentiments with decay, disagreement penalty, and saturation."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DATA_DIR / "train_df_monthly.csv",
        help="Path to the monthly news file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_DIR / "train_df_monthly_fused.csv",
        help="Path to write the fused monthly sentiment file.",
    )
    parser.add_argument(
        "--half-life-days",
        type=float,
        default=5.0,
        help="Half-life for time decay in days (default: 5).",
    )
    parser.add_argument(
        "--beta",
        type=float,
        default=3.0,
        help="Scaling factor before tanh for multi-item months (default: 3.0).",
    )
    parser.add_argument(
        "--eps",
        type=float,
        default=1e-6,
        help="Small constant to avoid divide-by-zero in disagreement penalty.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.input)
    fused = fuse_sentiment_monthly(
        df,
        half_life_days=args.half_life_days,
        beta=args.beta,
        eps=args.eps,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fused.to_csv(args.output, index=False)

    print(f"Fused monthly sentiment written to {args.output}")
    print(f"Rows: {len(fused)}, columns: {list(fused.columns)}")
    print("Sample:")
    print(fused.head())


if __name__ == "__main__":
    main()
