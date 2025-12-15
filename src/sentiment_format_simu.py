import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def generate_sentiment(
    input_path: Path,
    output_path: Path,
    seed: int = 42,
    sep: str = ";",
    encoding: str = "utf-8-sig",
) -> None:
    """
    Load ticker/date columns, create random sentiment scores, and write the CSV.
    """
    df = pd.read_csv(input_path, usecols=["ticker", "date"])

    rng = np.random.default_rng(seed)
    df["sentiment"] = rng.uniform(-1.0, 1.0, size=len(df))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, sep=sep, encoding=encoding)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate simulated sentiment scores from train_df data."
    )
    parser.add_argument(
        "--input",
        default="train_df.csv",
        type=Path,
        help="Path to the train_df CSV containing ticker and date columns.",
    )
    parser.add_argument(
        "--output",
        default="sentiment_score_simu.csv",
        type=Path,
        help="Path to write the simulated sentiment CSV.",
    )
    parser.add_argument(
        "--seed",
        default=42,
        type=int,
        help="Random seed for reproducible sentiment generation.",
    )
    parser.add_argument(
        "--sep",
        default=";",
        help="Delimiter for the output CSV (default ';' to avoid single-column parsing in Excel/WPS).",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8-sig",
        help="Encoding for the output CSV (default 'utf-8-sig' for spreadsheet compatibility).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_sentiment(args.input, args.output, args.seed, args.sep, args.encoding)


if __name__ == "__main__":
    main()
