from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from data_preprocessing_daily import preprocess_train_df
from sentiment_merge_daily import fuse_sentiment as fuse_sentiment_daily
from evaluate_daily import (
    load_data,
    predictive_metrics,
    quantile_test,
    three_state_strategy,
    train_test_split_strategy,
)
from evaluate_daily_visualization import generate_daily_plots

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PLOTS_DIR = BASE_DIR / "outputs" / "plots_daily"


def run_pipeline(
    train_path: Path,
    returns_path: Path,
    output_daily: Path,
    output_fused: Path,
    plots_dir: Path,
    winsorize: bool,
    q_low: float,
    q_high: float,
) -> None:
    # Step 1: preprocessing (writes train_df_daily.csv)
    daily = preprocess_train_df(train_path, output_daily)
    print(f"[daily] saved {len(daily)} rows to {output_daily}")

    # Step 2: fuse intraday sentiments to daily
    fused = fuse_sentiment_daily(pd.read_csv(output_daily))
    fused.to_csv(output_fused, index=False)
    print(f"[fused] saved {len(fused)} rows to {output_fused}")

    # Step 3: evaluation
    df_eval = load_data(output_fused, winsorize=winsorize)
    print(f"[eval] loaded {len(df_eval)} rows after cleaning")
    metrics = predictive_metrics(df_eval)
    qtest = quantile_test(df_eval, q_low=q_low, q_high=q_high)
    strat = three_state_strategy(df_eval, q_low=q_low, q_high=q_high)
    oos = train_test_split_strategy(df_eval, q_low=q_low, q_high=q_high)
    print("[eval] predictive metrics:", metrics)
    print("[eval] quantile test:", qtest)
    print("[eval] three-state strategy:", strat)
    print("[eval] train/test strategy:", oos)

    # Step 4: visualization
    generate_daily_plots(
        input_path=output_fused,
        outdir=plots_dir,
        winsorize=winsorize,
        q_low=q_low,
        q_high=q_high,
        bins=10,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Daily pipeline: preprocess -> fuse -> evaluate -> visualize.")
    parser.add_argument("--train", type=Path, default=DATA_DIR / "train_df.csv", help="Path to train_df.csv")
    parser.add_argument("--returns", type=Path, default=DATA_DIR / "train_return_data_daily.csv", help="Path to daily returns CSV")
    parser.add_argument("--daily-out", type=Path, default=DATA_DIR / "train_df_daily.csv", help="Output daily processed file")
    parser.add_argument("--fused-out", type=Path, default=DATA_DIR / "train_df_daily_fused.csv", help="Output fused daily file")
    parser.add_argument("--plots-dir", type=Path, default=PLOTS_DIR, help="Directory to save plots")
    parser.add_argument("--winsorize", action="store_true", help="Winsorize N_RET at 1/99 percentiles")
    parser.add_argument("--q-low", type=float, default=0.3, help="Low quantile threshold")
    parser.add_argument("--q-high", type=float, default=0.7, help="High quantile threshold")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_pipeline(
        train_path=args.train,
        returns_path=args.returns,
        output_daily=args.daily_out,
        output_fused=args.fused_out,
        plots_dir=args.plots_dir,
        winsorize=args.winsorize,
        q_low=args.q_low,
        q_high=args.q_high,
    )


if __name__ == "__main__":
    main()
