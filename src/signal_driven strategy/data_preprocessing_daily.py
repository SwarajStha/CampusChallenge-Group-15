from __future__ import annotations

import argparse
from datetime import timedelta
import warnings
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def na_row_stats(df: pd.DataFrame) -> tuple[int, pd.Series]:
    """
    Return the number of rows containing any NA and per-column NA counts.
    """
    per_col = df.isna().sum()
    row_count = int(df.isna().any(axis=1).sum())
    return row_count, per_col[per_col > 0].sort_values(ascending=False)


def ret_na_cleanup(path: Path, chunksize: int = 500_000) -> tuple[int, int, bool]:
    """
    Detect NA values in RET column; if any, drop those rows and overwrite the file.
    Returns (na_count, total_rows, cleaned_flag).
    """
    ret_col = pd.read_csv(path, usecols=["RET"])
    na_count = int(ret_col["RET"].isna().sum())
    total_rows = len(ret_col)

    if na_count == 0:
        return na_count, total_rows, False

    tmp_path = path.with_suffix(path.suffix + ".tmp")
    if tmp_path.exists():
        tmp_path.unlink()

    wrote_header = False
    for chunk in pd.read_csv(path, chunksize=chunksize):
        mask = chunk["RET"].notna()
        chunk = chunk.loc[mask]
        chunk.to_csv(tmp_path, mode="a", index=False, header=not wrote_header)
        wrote_header = True

    tmp_path.replace(path)
    return na_count, total_rows, True


def add_next_ret(path: Path) -> tuple[int, int]:
    """
    For each ticker, sort by date ascending, set N_RET as next day's RET (shift -1),
    drop rows where N_RET is NA (last row per ticker), and overwrite the file.
    Returns (rows_removed, remaining_rows).
    """
    df = pd.read_csv(path)
    required = {"ticker", "date", "RET"}
    if not required.issubset(df.columns):
        raise KeyError("train_return_data_daily missing required columns.")

    if "N_RET" in df.columns:
        df = df.drop(columns=["N_RET"])

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values(["ticker", "date"])

    def _per_ticker(group: pd.DataFrame) -> pd.DataFrame:
        group = group.sort_values("date")
        group["N_RET"] = group["RET"].shift(-1)
        ticker_name = getattr(group, "name", None)
        if ticker_name is not None:
            group["ticker"] = ticker_name
        return group

    grouped = df.groupby("ticker", group_keys=False, sort=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        processed = grouped.apply(_per_ticker)
    processed = processed.sort_values(["ticker", "date"])

    rows_removed = int(processed["N_RET"].isna().sum())
    processed = processed.loc[processed["N_RET"].notna()].reset_index(drop=True)

    processed.to_csv(path, index=False)
    return rows_removed, len(processed)


def attach_returns(
    news_df: pd.DataFrame, returns_path: Path
) -> pd.DataFrame:
    """
    Merge RET and N_RET from train_return_data_daily into news_df by ticker/date.
    """
    returns_df = pd.read_csv(returns_path, usecols=["ticker", "date", "RET", "N_RET"])
    returns_df["date"] = pd.to_datetime(returns_df["date"], errors="coerce").dt.date
    merged = news_df.merge(returns_df, on=["ticker", "date"], how="left")
    return merged


def _adjust_na_block(group: pd.DataFrame, start: int, end: int) -> None:
    """
    Adjust a consecutive NA block for RET and N_RET within a sorted ticker group in place.
    """
    prev_idx = start - 1 if start > 0 else None
    next_idx = end + 1 if end + 1 < len(group) else None
    if next_idx is None:
        return

    next_date = group.iloc[next_idx]["date"]

    # Update dates to next available date.
    block_idx = group.index[start : end + 1]
    group.loc[block_idx, "date"] = next_date

    # Prepare time windows in ET.
    o_dt = pd.to_datetime(group.loc[block_idx, "o_date"], utc=True, errors="coerce")
    o_et = o_dt.dt.tz_convert("America/New_York")

    # Keep original delta_t only for news within previous tradable day's 16:00-20:00 ET window.
    keep_original_mask = pd.Series(False, index=block_idx, dtype=bool)
    if prev_idx is not None:
        prev_date = group.iloc[prev_idx]["date"]
        prev_start = pd.Timestamp(prev_date).tz_localize("America/New_York") + pd.Timedelta(hours=16)
        prev_end = pd.Timestamp(prev_date).tz_localize("America/New_York") + pd.Timedelta(hours=20)
        keep_original_mask = (o_et >= prev_start) & (o_et <= prev_end)

    next_day_start = pd.Timestamp(next_date).tz_localize("America/New_York")
    next_4am = next_day_start + pd.Timedelta(hours=4)
    next_close = next_day_start + pd.Timedelta(hours=15, minutes=59, seconds=59)
    delta_at_4am = (next_close - next_4am).total_seconds()

    # For the missing block itself: keep only prev-day 16:00-20:00; all other rows use 4:00-derived delta_t.
    force_4am_mask = ~keep_original_mask
    group.loc[block_idx, "delta_t"] = group.loc[block_idx, "delta_t"].where(
        ~force_4am_mask, delta_at_4am
    )

    # For the block right after the missing block (same next_date):
    # if news time is before 4:00 ET on next_date, clamp to 4:00-derived delta_t.
    post_start = next_idx
    post_end = post_start
    while post_end + 1 < len(group) and group.iloc[post_end + 1]["date"] == next_date:
        post_end += 1

    post_block_idx = group.index[post_start : post_end + 1]
    if len(post_block_idx) > 0:
        post_o_dt = pd.to_datetime(group.loc[post_block_idx, "o_date"], utc=True, errors="coerce")
        post_o_et = post_o_dt.dt.tz_convert("America/New_York")
        post_before_4_mask = (post_o_et >= next_day_start) & (post_o_et < next_4am)
        group.loc[post_block_idx, "delta_t"] = group.loc[post_block_idx, "delta_t"].where(
            ~post_before_4_mask, delta_at_4am
        )

    next_ret = group.iloc[next_idx]["RET"]
    next_n_ret = group.iloc[next_idx]["N_RET"]
    group.loc[block_idx, ["RET", "N_RET"]] = [next_ret, next_n_ret]


def clean_return_gaps(news_df: pd.DataFrame) -> pd.DataFrame:
    """
    For each ticker, drop trailing rows where RET and N_RET are NA,
    then forward-fill NA blocks by aligning to the next available RET/N_RET,
    adjusting date and delta_t per specified rules.
    """
    def _clean_group(group: pd.DataFrame) -> pd.DataFrame:
        group = group.sort_values("date").reset_index(drop=True)
        mask_na = group["RET"].isna() & group["N_RET"].isna()
        # Drop trailing NA block
        tail_len = 0
        for v in mask_na.iloc[::-1]:
            if v:
                tail_len += 1
            else:
                break
        if tail_len:
            group = group.iloc[: -tail_len]
            mask_na = group["RET"].isna() & group["N_RET"].isna()

        if not mask_na.any():
            return group

        i = 0
        n = len(group)
        mask_na_vals = mask_na.to_list()
        while i < n:
            if not mask_na_vals[i]:
                i += 1
                continue
            start = i
            while i < n and mask_na_vals[i]:
                i += 1
            end = i - 1
            _adjust_na_block(group, start, end)
            mask_na_vals = (group["RET"].isna() & group["N_RET"].isna()).to_list()
            n = len(group)
        return group

    grouped = news_df.groupby("ticker", group_keys=False)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        cleaned = grouped.apply(_clean_group)
    cleaned = cleaned.sort_values(["ticker", "date"]).reset_index(drop=True)
    return cleaned


def merge_sentiment(
    df: pd.DataFrame, sentiment_path: Path | None = None
) -> tuple[pd.DataFrame, int, int, Path]:
    """
    Merge sentiment scores on ticker and date. Drops rows with NA sentiment after merge.
    Returns the merged frame, the number of matched rows (post-drop),
    missing sentiment count (pre-drop), and the file used.
    """
    candidates = [
        DATA_DIR / "sentiment_score_simu.csv",
        DATA_DIR / "sentiment_score.csv",
    ]
    if sentiment_path is not None:
        candidates.insert(0, Path(sentiment_path))

    chosen = next((p for p in candidates if p.exists()), None)
    if chosen is None:
        raise FileNotFoundError("No sentiment score file found.")

    sentiment_df = pd.read_csv(chosen, sep=None, engine="python")
    sentiment_df.columns = [c.strip().lstrip("\ufeff") for c in sentiment_df.columns]
    required = ["ticker", "date", "sentiment"]
    if not set(required).issubset(sentiment_df.columns):
        # Handle single-column semicolon-separated files.
        if sentiment_df.shape[1] == 1:
            split_cols = sentiment_df.iloc[:, 0].str.split(";", expand=True)
            if split_cols.shape[1] >= 3:
                split_cols = split_cols.iloc[:, :3]
                split_cols.columns = required
                sentiment_df = split_cols
        sentiment_df.columns = [c.strip().lstrip("\ufeff") for c in sentiment_df.columns]
        if not set(required).issubset(sentiment_df.columns):
            raise KeyError("Sentiment file missing required columns.")

    sentiment_df = sentiment_df[required]
    merged = df.merge(sentiment_df, on=["ticker", "date"], how="left")
    missing = int(merged["sentiment"].isna().sum())
    merged = merged.dropna(subset=["sentiment"])
    matched = int(len(merged))
    return merged, matched, missing, chosen


def bucket_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert the news timestamps to trading days defined as
    (t-1 16:00 ET, t 15:59:59 ET] -> t day.
    Also compute delta_t (seconds) from headline time to 16:00:00 ET of that t day.
    """
    bucketed = df.copy()
    bucketed["o_date"] = bucketed["date"].copy()
    bucketed["date"] = pd.to_datetime(bucketed["date"], utc=True, errors="coerce")

    if bucketed["date"].isna().any():
        bad_rows = bucketed[bucketed["date"].isna()]
        raise ValueError(f"Found non-parsable dates in rows: {bad_rows.index.tolist()}")

    bucketed["date_et"] = bucketed["date"].dt.tz_convert("America/New_York")
    t_day = (bucketed["date_et"] + timedelta(hours=8)).dt.date
    close_dt = pd.to_datetime(t_day).dt.tz_localize("America/New_York") + timedelta(
        hours=16
    )
    bucketed["delta_t"] = (close_dt - bucketed["date_et"]).dt.total_seconds()
    bucketed["date"] = t_day
    return bucketed.drop(columns=["date_et"])


def duplicate_ticker_date_counts(df: pd.DataFrame) -> pd.Series:
    """
    Return counts for ticker-date pairs that appear more than once.
    """
    required_cols = {"ticker", "date"}
    if not required_cols.issubset(df.columns):
        return pd.Series(dtype=int)

    counts = df.groupby(["ticker", "date"]).size()
    dup_counts = counts[counts > 1]
    return dup_counts.sort_index()


def fuse_sentiment_direction(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate multiple headlines into one ticker-date sentiment.
    Headlines closer to market close get higher weight via delta_t.
    """
    required = {"ticker", "date", "sentiment", "N_RET"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Input missing required columns for fusion: {missing}")

    fused = df.copy()
    fused["sentiment"] = pd.to_numeric(fused["sentiment"], errors="coerce")
    fused["N_RET"] = pd.to_numeric(fused["N_RET"], errors="coerce")
    if "RET" in fused.columns:
        fused["RET"] = pd.to_numeric(fused["RET"], errors="coerce")
    else:
        fused["RET"] = pd.NA

    if "delta_t" in fused.columns:
        fused["delta_t"] = pd.to_numeric(fused["delta_t"], errors="coerce")
    else:
        fused["delta_t"] = pd.NA

    clipped_delta = fused["delta_t"].clip(lower=0)
    fused["weight"] = 1.0 / (1.0 + clipped_delta / 3600.0)
    fused["weight"] = fused["weight"].fillna(1.0)
    fused["effective_weight"] = fused["weight"].where(fused["sentiment"].notna(), 0.0)
    fused["weighted_sentiment"] = fused["sentiment"].fillna(0.0) * fused["effective_weight"]

    grouped = (
        fused.groupby(["ticker", "date"], as_index=False, sort=True)
        .agg(
            weighted_sentiment_sum=("weighted_sentiment", "sum"),
            weight_sum=("effective_weight", "sum"),
            RET=("RET", "first"),
            N_RET=("N_RET", "first"),
            news_count=("sentiment", "size"),
        )
    )
    grouped["sentiment"] = grouped["weighted_sentiment_sum"] / grouped["weight_sum"]
    grouped = grouped.drop(columns=["weighted_sentiment_sum", "weight_sum"])
    grouped = grouped.dropna(subset=["sentiment", "N_RET"]).reset_index(drop=True)
    grouped = grouped.loc[grouped["sentiment"] != 0].reset_index(drop=True)
    return grouped[["date", "ticker", "sentiment", "RET", "N_RET", "news_count"]]


def preprocess_train_df(input_path: Path, output_path: Path) -> pd.DataFrame:
    df = pd.read_csv(input_path)
    # Normalize core column names from new merged train_df.
    rename_map = {}
    if "date" not in df.columns:
        if "date_day" in df.columns:
            rename_map["date_day"] = "date"
    if rename_map:
        df = df.rename(columns=rename_map)

    if "sentiment" not in df.columns:
        if "Final_Weighted" in df.columns:
            df["sentiment"] = df["Final_Weighted"]
        elif "Sentiment_Score" in df.columns:
            df["sentiment"] = df["Sentiment_Score"]

    required = {"ticker", "date", "sentiment"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"train_df missing required columns: {missing}")

    # Drop unused columns early to keep output lean.
    df = df[["ticker", "date", "sentiment"]].copy()
    na_rows, na_cols = na_row_stats(df)
    df = df.reset_index(drop=True)

    ret_path = DATA_DIR / "train_return_data_daily.csv"
    try:
        ret_na, ret_total, cleaned = ret_na_cleanup(ret_path)
        if ret_na:
            print(f"train_return_data_daily RET NA count: {ret_na} out of {ret_total} rows.")
            if cleaned:
                print("Rows with NA RET have been removed from train_return_data_daily.csv.")
        else:
            print("No NA values in train_return_data_daily RET.")
        print("Using existing N_RET from train_return_data_daily.csv (no recalculation).")
    except FileNotFoundError:
        print("train_return_data_daily.csv not found; skipped RET NA check.")
    except KeyError:
        print("RET column not found in train_return_data_daily; skipped RET NA check.")

    bucketed = bucket_dates(df)

    try:
        bucketed = attach_returns(bucketed, ret_path)
        bucketed = clean_return_gaps(bucketed)
    except FileNotFoundError:
        print("train_return_data_daily.csv not found; skipped RET/N_RET merge.")
    except KeyError as e:
        print(f"{e}; skipped RET/N_RET merge and cleaning.")

    dup_counts = duplicate_ticker_date_counts(bucketed)

    # Keep only columns required downstream.
    keep_cols = ["ticker", "date", "delta_t", "sentiment", "RET", "N_RET"]
    bucketed = bucketed.drop(
        columns=[c for c in bucketed.columns if c not in keep_cols],
        errors="ignore",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    bucketed.to_csv(output_path, index=False)

    if na_rows:
        print(f"Rows containing NA: {na_rows}")
        if not na_cols.empty:
            print("NA counts per column (top 5):")
            print(na_cols.head())
    else:
        print("No rows with NA found.")
    if not dup_counts.empty:
        print("Duplicate ticker-date counts (post-bucketing):")
        print(dup_counts.head())
    else:
        print("No duplicate ticker-date pairs found after bucketing.")
    n_ret_missing = bucketed["N_RET"].isna().sum() if "N_RET" in bucketed else None
    if n_ret_missing is not None:
        print(f"N_RET NA rows after cleaning: {n_ret_missing}")
    return bucketed


def preprocess_direction_df(
    input_path: Path,
    daily_output_path: Path,
    output_path: Path,
) -> pd.DataFrame:
    """
    Full preprocessing for direction strategy.
    1) Build day-bucketed rows with returns.
    2) Fuse ticker-date headlines to one sentiment signal.
    """
    daily = preprocess_train_df(input_path, daily_output_path)
    fused = fuse_sentiment_direction(daily)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fused.to_csv(output_path, index=False, float_format="%.6f")
    print(
        f"Saved direction-ready preprocessed data to {output_path} "
        f"({len(fused)} rows, {fused['news_count'].sum()} headlines fused)."
    )
    return fused


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preprocess train_df for direction strategy and output fused daily signals."
    )
    parser.add_argument(
        "--input",
        default=DATA_DIR / "train_df.csv",
        type=Path,
        help="Path to the raw train_df CSV with a date column.",
    )
    parser.add_argument(
        "--daily-output",
        default=DATA_DIR / "train_df_daily.csv",
        type=Path,
        help="Where to write intermediate day-bucketed rows.",
    )
    parser.add_argument(
        "--output",
        default=DATA_DIR / "train_df_daily_direction.csv",
        type=Path,
        help="Where to write fused direction-ready data.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    fused = preprocess_direction_df(
        input_path=args.input,
        daily_output_path=args.daily_output,
        output_path=args.output,
    )

    print("Saved direction-ready news to", args.output)
    print(fused.head())


if __name__ == "__main__":
    main()
