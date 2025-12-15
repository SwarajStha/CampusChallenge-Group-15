from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from data_preprocessing_monthly import preprocess_monthly
from sentiment_merge_monthly import fuse_sentiment_monthly
from evaluate_monthly import evaluate
from evaluate_monthly_visualization import generate_plots

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PLOTS_DIR = BASE_DIR / "outputs" / "plots_monthly"


def run_pipeline(
    train_path: Path,
    returns_path: Path,
    output_monthly: Path,
    output_fused: Path,
    sentiment_path: Path | None,
    bins: int,
    plots_dir: Path,
) -> None:
    # Step 1: preprocess monthly
    monthly = preprocess_monthly(
        train_path=train_path,
        return_path=returns_path,
        output_path=output_monthly,
        sentiment_path=sentiment_path,
    )
    print(f"[monthly] saved {len(monthly)} rows to {output_monthly}")

    # Step 2: fuse sentiment monthly
    fused = fuse_sentiment_monthly(pd.read_csv(output_monthly))
    fused.to_csv(output_fused, index=False)
    print(f"[fused] saved {len(fused)} rows to {output_fused}")

    # Step 3: evaluate (drop 2021-06)
    fused_eval = fused[fused["date"] != "2021-06"]
    summary = evaluate(fused_eval, k=bins)
    print("[evaluate] RankIC raw:", summary["rankic_raw"])
    print("[evaluate] RankIC ex:", summary["rankic_ex"])
    print("[evaluate] Quant raw:", summary["quant_raw"])
    print("[evaluate] Quant ex:", summary["quant_ex"])
    print("[evaluate] Ties:", summary["ties"])
    print(
        "[evaluate] Portfolio raw (no NAV):",
        {k: v for k, v in summary["portfolio_raw"].items() if k != "nav"},
    )
    print(
        "[evaluate] Portfolio ex (no NAV):",
        {k: v for k, v in summary["portfolio_ex"].items() if k != "nav"},
    )

    # Step 4: visualization
    generate_plots(output_fused, plots_dir, k=bins)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monthly pipeline: preprocess -> fuse -> evaluate -> visualize.")
    parser.add_argument("--train", type=Path, default=DATA_DIR / "train_df.csv", help="Path to train_df.csv")
    parser.add_argument("--returns", type=Path, default=DATA_DIR / "train_return_data.csv", help="Path to monthly returns CSV")
    parser.add_argument("--sentiment", type=Path, default=None, help="Optional path to sentiment score CSV")
    parser.add_argument("--monthly-out", type=Path, default=DATA_DIR / "train_df_monthly.csv", help="Output monthly processed file")
    parser.add_argument("--fused-out", type=Path, default=DATA_DIR / "train_df_monthly_fused.csv", help="Output fused monthly file")
    parser.add_argument("--bins", type=int, default=4, help="Number of quantile bins")
    parser.add_argument("--plots-dir", type=Path, default=PLOTS_DIR, help="Directory to save plots")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_pipeline(
        train_path=args.train,
        returns_path=args.returns,
        output_monthly=args.monthly_out,
        output_fused=args.fused_out,
        sentiment_path=args.sentiment,
        bins=args.bins,
        plots_dir=args.plots_dir,
    )


if __name__ == "__main__":
    main()
