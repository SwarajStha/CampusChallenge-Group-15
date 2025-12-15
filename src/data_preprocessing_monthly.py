from __future__ import annotations

import argparse
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_sentiment(path_hint: Path | None = None) -> pd.DataFrame:
    """Load sentiment file, supporting semicolon-delimited and BOM headers."""
    candidates = [
        DATA_DIR / "sentiment_score.csv",
        DATA_DIR / "sentiment_score_simu.csv",
    ]
    if path_hint:
        candidates.insert(0, Path(path_hint))
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        raise FileNotFoundError("No sentiment score file found.")

    df = pd.read_csv(path, sep=None, engine="python")
    df.columns = [c.strip().lstrip("\ufeff") for c in df.columns]
    required = {"ticker", "date", "sentiment"}
    if not required.issubset(df.columns):
        # try single-column semicolon case
        if df.shape[1] == 1:
            split = df.iloc[:, 0].str.split(";", expand=True)
            if split.shape[1] >= 3:
                split = split.iloc[:, :3]
                split.columns = ["ticker", "date", "sentiment"]
                df = split
    if not required.issubset(df.columns):
        raise KeyError("Sentiment file missing ticker/date/sentiment columns.")
    return df[["ticker", "date", "sentiment"]]


def merge_sentiment(news_df: pd.DataFrame, sent_df: pd.DataFrame) -> pd.DataFrame:
    return news_df.merge(sent_df, on=["ticker", "date"], how="left")


def drop_rss_rows(news_df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop rows whose link contains '?.tsrc=rss' substring."""
    if "link" not in news_df.columns:
        return news_df, 0
    mask = news_df["link"].astype(str).str.contains("?.tsrc=rss", regex=False, na=False)
    if not mask.any():
        return news_df, 0
    cleaned = news_df.loc[~mask].copy()
    return cleaned, int(mask.sum())


def bucket_dates(news_df: pd.DataFrame) -> pd.DataFrame:
    """Shift ET window so (t-1 16:00, t 15:59:59] -> t."""
    df = news_df.copy()
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    if df["date"].isna().any():
        bad = df[df["date"].isna()]
        raise ValueError(f"Non-parsable dates at rows {bad.index.tolist()}")
    df["date_et"] = df["date"].dt.tz_convert("America/New_York")
    df["date"] = (df["date_et"] + timedelta(hours=8)).dt.date
    df = df.drop(columns=["date_et"])
    return df


def trim_returns(ret_df: pd.DataFrame, min_date: pd.Timestamp, max_date: pd.Timestamp) -> pd.DataFrame:
    mask = (ret_df["date"] >= min_date) & (ret_df["date"] <= max_date)
    return ret_df.loc[mask].copy()


def clean_and_shift_returns(ret_df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    df = ret_df.copy()
    df = df[df["RET"].notna()].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values(["TICKER", "date"])

    def _per_ticker(g: pd.DataFrame) -> pd.DataFrame:
        g = g.sort_values("date")
        g["N_RET"] = g["RET"].shift(-1)
        g = g.loc[g["N_RET"].notna()]
        return g

    processed = df.groupby("TICKER", group_keys=False).apply(_per_ticker)
    processed = processed.sort_values(["TICKER", "date"]).reset_index(drop=True)
    return processed, len(df) - len(processed)


def align_news_to_returns(news_df: pd.DataFrame, ret_df: pd.DataFrame) -> pd.DataFrame:
    """
    Align news dates to return dates per ticker with the specified rules.
    """
    ret_df = ret_df.copy()
    ret_df["date"] = pd.to_datetime(ret_df["date"], errors="coerce").dt.date
    news_df = news_df.copy()
    news_df["date"] = pd.to_datetime(news_df["date"]).dt.date

    def _align_group(g_news: pd.DataFrame, g_ret: pd.DataFrame) -> pd.DataFrame:
        if g_ret.empty:
            return pd.DataFrame(columns=list(g_news.columns) + ["RET", "N_RET", "o_date", "delta_t"])

        ret_dates = g_ret["date"].to_numpy()
        ret_vals = g_ret[["RET", "N_RET"]].to_numpy()

        g_news = g_news.sort_values("date").reset_index(drop=True)
        records = []
        for _, row in g_news.iterrows():
            orig_date = row["date"]

            if orig_date > ret_dates[-1]:
                # Drop dates later than returns coverage.
                continue
            if orig_date < ret_dates[0]:
                target_idx = 0
            else:
                pos = np.searchsorted(ret_dates, orig_date, side="right")
                if pos == 0:
                    target_idx = 0
                else:
                    target_idx = pos if pos < len(ret_dates) else len(ret_dates) - 1
                # Ensure we map to the right endpoint of interval (previous, current]
                if ret_dates[target_idx] > orig_date:
                    # we already chose right endpoint
                    pass
            target_date = ret_dates[target_idx]
            ret_row = ret_vals[target_idx]
            new_row = row.copy()
            new_row["o_date"] = orig_date
            new_row["date"] = target_date
            delta_days = (pd.to_datetime(target_date) - pd.to_datetime(orig_date)).days
            new_row["delta_t"] = delta_days
            new_row["RET"] = ret_row[0]
            new_row["N_RET"] = ret_row[1]
            records.append(new_row)

        if not records:
            return pd.DataFrame(columns=list(g_news.columns) + ["RET", "N_RET", "o_date", "delta_t"])
        out = pd.DataFrame(records)
        return out

    aligned_groups = []
    for ticker, g_news in news_df.groupby("ticker"):
        g_ret = ret_df[ret_df["TICKER"] == ticker]
        aligned = _align_group(g_news, g_ret)
        if not aligned.empty:
            aligned["ticker"] = ticker
        aligned_groups.append(aligned)

    aligned_df = pd.concat(aligned_groups, ignore_index=True) if aligned_groups else pd.DataFrame()
    aligned_df = aligned_df.sort_values(["ticker", "date"]).reset_index(drop=True)
    return aligned_df


def preprocess_monthly(
    train_path: Path,
    return_path: Path,
    output_path: Path,
    sentiment_path: Path | None = None,
) -> pd.DataFrame:
    news = pd.read_csv(train_path)
    sent_df = load_sentiment(sentiment_path)
    news = merge_sentiment(news, sent_df)
    news, dropped = drop_rss_rows(news)
    if dropped:
        print(f"Dropped {dropped} rows with '?.tsrc=rss' in link.")

    news = bucket_dates(news)
    min_date = news["date"].min()
    max_date = news["date"].max()
    print(f"News date range after bucketing: {min_date} -> {max_date}")

    rets = pd.read_csv(return_path)
    rets["date"] = pd.to_datetime(rets["date"], errors="coerce").dt.date
    rets = trim_returns(rets, min_date, max_date)
    rets_clean, removed = clean_and_shift_returns(rets)
    if removed:
        print(f"Removed {removed} rows from returns during N_RET creation.")

    aligned = align_news_to_returns(news, rets_clean)
    n_na = aligned["N_RET"].isna().sum() if not aligned.empty else None
    print(f"Aligned news rows: {len(aligned)}; N_RET NA rows: {n_na}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    aligned.to_csv(output_path, index=False)
    return aligned


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monthly preprocessing with sentiment and return alignment.")
    parser.add_argument("--train", type=Path, default=DATA_DIR / "train_df.csv", help="Path to train_df.csv")
    parser.add_argument("--returns", type=Path, default=DATA_DIR / "train_return_data.csv", help="Path to monthly returns CSV")
    parser.add_argument("--output", type=Path, default=DATA_DIR / "train_df_monthly.csv", help="Output CSV path")
    parser.add_argument("--sentiment", type=Path, default=None, help="Optional path to sentiment score CSV")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = preprocess_monthly(args.train, args.returns, args.output, args.sentiment)
    print(f"Saved monthly processed data to {args.output} with {len(result)} rows.")


if __name__ == "__main__":
    main()
