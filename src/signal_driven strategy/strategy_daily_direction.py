from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs" / "strategy_daily_direction"


def load_direction_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"date", "ticker", "sentiment", "N_RET"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Input missing columns: {missing}")

    out = df[["date", "ticker", "sentiment", "N_RET"]].copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.date
    out["ticker"] = out["ticker"].astype(str)
    out["sentiment"] = pd.to_numeric(out["sentiment"], errors="coerce")
    out["N_RET"] = pd.to_numeric(out["N_RET"], errors="coerce")
    out = out.dropna(subset=["date", "ticker", "sentiment", "N_RET"])
    out = out.sort_values(["date", "ticker"]).reset_index(drop=True)
    return out


def _signal_positions_for_day(
    day_df: pd.DataFrame,
    threshold: float,
    long_short_long_exposure: float,
    long_short_short_exposure: float,
    long_only_exposure: float,
) -> tuple[pd.DataFrame, dict]:
    long_mask = day_df["sentiment"] > threshold
    short_mask = day_df["sentiment"] < -threshold

    long_df = day_df.loc[long_mask].copy()
    short_df = day_df.loc[short_mask].copy()
    n_long = len(long_df)
    n_short = len(short_df)

    if n_long > 0 and n_short > 0:
        mode = "long_short"
        long_weight = long_short_long_exposure / n_long
        short_weight = -long_short_short_exposure / n_short
    elif n_long > 0 and n_short == 0:
        mode = "long_only"
        long_weight = long_only_exposure / n_long
        short_weight = 0.0
    else:
        mode = "flat"
        long_weight = 0.0
        short_weight = 0.0

    pos_frames: list[pd.DataFrame] = []
    if long_weight != 0.0:
        long_df["weight"] = long_weight
        long_df["side"] = "long"
        pos_frames.append(long_df)
    if short_weight != 0.0:
        short_df["weight"] = short_weight
        short_df["side"] = "short"
        pos_frames.append(short_df)

    if pos_frames:
        positions = pd.concat(pos_frames, axis=0, ignore_index=True)
        positions["contribution"] = positions["weight"] * positions["N_RET"]
    else:
        positions = pd.DataFrame(columns=["date", "ticker", "sentiment", "N_RET", "weight", "side", "contribution"])

    if positions.empty:
        long_exposure = 0.0
        short_exposure = 0.0
        net_exposure = 0.0
        gross_exposure = 0.0
    else:
        long_exposure = float(positions.loc[positions["weight"] > 0, "weight"].sum())
        short_exposure = float(positions.loc[positions["weight"] < 0, "weight"].sum())
        net_exposure = float(positions["weight"].sum())
        gross_exposure = float(positions["weight"].abs().sum())

    summary = {
        "mode": mode,
        "n_long": n_long,
        "n_short": n_short,
        "long_exposure": long_exposure,
        "short_exposure": short_exposure,
        "net_exposure": net_exposure,
        "gross_exposure": gross_exposure,
    }
    return positions, summary


def run_signal_strategy(
    df: pd.DataFrame,
    threshold: float,
    long_short_long_exposure: float,
    long_short_short_exposure: float,
    long_only_exposure: float,
    initial_capital: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    capital = float(initial_capital)
    daily_records: list[dict] = []
    all_positions: list[pd.DataFrame] = []

    for date, day_df in df.groupby("date", sort=True):
        capital_start = capital
        day_df = day_df.sort_values("ticker").reset_index(drop=True)
        positions, summary = _signal_positions_for_day(
            day_df=day_df,
            threshold=threshold,
            long_short_long_exposure=long_short_long_exposure,
            long_short_short_exposure=long_short_short_exposure,
            long_only_exposure=long_only_exposure,
        )

        if positions.empty:
            daily_return = 0.0
        else:
            daily_return = float(positions["contribution"].sum())
            positions.insert(0, "strategy", "signal_threshold")
            all_positions.append(positions)

        pnl = capital_start * daily_return
        capital = capital_start + pnl

        daily_records.append(
            {
                "date": date,
                "strategy": "signal_threshold",
                "mode": summary["mode"],
                "universe_size": int(len(day_df)),
                "n_long": int(summary["n_long"]),
                "n_short": int(summary["n_short"]),
                "long_exposure": summary["long_exposure"],
                "short_exposure": summary["short_exposure"],
                "net_exposure": summary["net_exposure"],
                "gross_exposure": summary["gross_exposure"],
                "daily_return": daily_return,
                "capital_start": capital_start,
                "pnl": pnl,
                "capital_end": capital,
            }
        )

    daily_df = pd.DataFrame(daily_records)
    pos_df = pd.concat(all_positions, axis=0, ignore_index=True) if all_positions else pd.DataFrame()
    return daily_df, pos_df


def run_equal_weight_hold_strategy(
    df: pd.DataFrame,
    initial_capital: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    capital = float(initial_capital)
    base = (
        df[["date", "ticker", "sentiment", "N_RET"]]
        .groupby(["date", "ticker"], as_index=False)
        .agg(sentiment=("sentiment", "mean"), N_RET=("N_RET", "mean"))
        .sort_values(["date", "ticker"])
        .reset_index(drop=True)
    )
    if base.empty:
        return pd.DataFrame(), pd.DataFrame()

    all_dates = sorted(base["date"].unique())
    first_date = all_dates[0]
    init_tickers = sorted(base.loc[base["date"] == first_date, "ticker"].unique().tolist())
    n_init = len(init_tickers)
    if n_init == 0:
        return pd.DataFrame(), pd.DataFrame()

    weight = 1.0 / n_init
    # Buy at first day close and hold fixed positions; missing ticker-day return is treated as 0.
    template = pd.MultiIndex.from_product([all_dates, init_tickers], names=["date", "ticker"]).to_frame(index=False)
    positions = template.merge(base, on=["date", "ticker"], how="left")
    positions["sentiment"] = pd.to_numeric(positions["sentiment"], errors="coerce").fillna(0.0)
    positions["N_RET"] = pd.to_numeric(positions["N_RET"], errors="coerce").fillna(0.0)
    positions["weight"] = weight
    positions["side"] = "long"
    positions["contribution"] = positions["weight"] * positions["N_RET"]
    positions.insert(0, "strategy", "equal_weight_hold")

    daily_ret = positions.groupby("date", as_index=False)["contribution"].sum().rename(columns={"contribution": "daily_return"})
    universe_size_map = base.groupby("date")["ticker"].nunique().to_dict()

    daily_records: list[dict] = []
    for _, row in daily_ret.sort_values("date").iterrows():
        date = row["date"]
        daily_return = float(row["daily_return"])
        capital_start = capital
        pnl = capital_start * daily_return
        capital = capital_start + pnl

        daily_records.append(
            {
                "date": date,
                "strategy": "equal_weight_hold",
                "mode": "buy_and_hold_long",
                "universe_size": int(universe_size_map.get(date, 0)),
                "n_long": int(n_init),
                "n_short": 0,
                "long_exposure": 1.0,
                "short_exposure": 0.0,
                "net_exposure": 1.0,
                "gross_exposure": 1.0,
                "daily_return": daily_return,
                "capital_start": capital_start,
                "pnl": pnl,
                "capital_end": capital,
            }
        )

    daily_df = pd.DataFrame(daily_records)
    pos_df = positions.reset_index(drop=True)
    return daily_df, pos_df


def build_performance_summary(signal_daily: pd.DataFrame, hold_daily: pd.DataFrame) -> pd.DataFrame:
    summary = signal_daily[["date", "capital_end"]].rename(columns={"capital_end": "signal_threshold_capital"})
    summary = summary.merge(
        hold_daily[["date", "capital_end"]].rename(columns={"capital_end": "equal_weight_hold_capital"}),
        on="date",
        how="outer",
    )
    summary = summary.sort_values("date").reset_index(drop=True)
    signal_init = float(signal_daily["capital_start"].iloc[0]) if not signal_daily.empty else np.nan
    hold_init = float(hold_daily["capital_start"].iloc[0]) if not hold_daily.empty else np.nan
    summary["signal_threshold_cum_return"] = summary["signal_threshold_capital"] / signal_init - 1.0
    summary["equal_weight_hold_cum_return"] = summary["equal_weight_hold_capital"] / hold_init - 1.0
    return summary


def save_outputs(
    signal_daily: pd.DataFrame,
    signal_positions: pd.DataFrame,
    hold_daily: pd.DataFrame,
    hold_positions: pd.DataFrame,
    outdir: Path,
) -> None:
    outdir.mkdir(parents=True, exist_ok=True)

    daily_cols = [
        "date",
        "strategy",
        "mode",
        "universe_size",
        "n_long",
        "n_short",
        "long_exposure",
        "short_exposure",
        "net_exposure",
        "gross_exposure",
        "daily_return",
        "capital_start",
        "pnl",
        "capital_end",
    ]
    pos_cols = ["strategy", "date", "ticker", "sentiment", "N_RET", "weight", "side", "contribution"]

    signal_daily = signal_daily.reindex(columns=daily_cols)
    hold_daily = hold_daily.reindex(columns=daily_cols)
    signal_daily.to_csv(outdir / "signal_strategy_daily_records.csv", index=False, float_format="%.8f")
    hold_daily.to_csv(outdir / "equal_weight_hold_daily_records.csv", index=False, float_format="%.8f")

    if not signal_positions.empty:
        signal_positions = signal_positions.reindex(columns=pos_cols)
        signal_positions.to_csv(outdir / "signal_strategy_positions.csv", index=False, float_format="%.8f")
    else:
        pd.DataFrame(columns=pos_cols).to_csv(outdir / "signal_strategy_positions.csv", index=False)

    if not hold_positions.empty:
        hold_positions = hold_positions.reindex(columns=pos_cols)
        hold_positions.to_csv(outdir / "equal_weight_hold_positions.csv", index=False, float_format="%.8f")
    else:
        pd.DataFrame(columns=pos_cols).to_csv(outdir / "equal_weight_hold_positions.csv", index=False)

    summary = build_performance_summary(signal_daily, hold_daily)
    summary.to_csv(outdir / "performance_summary.csv", index=False, float_format="%.8f")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run rolling daily direction strategy and equal-weight hold baseline."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DATA_DIR / "backtest_daily.csv",
        help="Backtest input file with at least date,ticker,sentiment,N_RET columns.",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory to save strategy records and positions.",
    )
    parser.add_argument("--initial-capital", type=float, default=1.0, help="Initial notional capital.")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Signal threshold. Long if sentiment > threshold; short if sentiment < -threshold.",
    )
    parser.add_argument(
        "--long-short-long-exposure",
        type=float,
        default=1.8,
        help="Total long exposure in long-short mode.",
    )
    parser.add_argument(
        "--long-short-short-exposure",
        type=float,
        default=1.0,
        help="Total short exposure (absolute value) in long-short mode.",
    )
    parser.add_argument(
        "--long-only-exposure",
        type=float,
        default=0.8,
        help="Total long exposure when only long signals exist.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.threshold <= 0:
        raise ValueError("--threshold must be positive.")
    if args.initial_capital <= 0:
        raise ValueError("--initial-capital must be positive.")

    df = load_direction_data(args.input)
    signal_daily, signal_positions = run_signal_strategy(
        df=df,
        threshold=args.threshold,
        long_short_long_exposure=args.long_short_long_exposure,
        long_short_short_exposure=args.long_short_short_exposure,
        long_only_exposure=args.long_only_exposure,
        initial_capital=args.initial_capital,
    )
    hold_daily, hold_positions = run_equal_weight_hold_strategy(
        df=df,
        initial_capital=args.initial_capital,
    )

    save_outputs(
        signal_daily=signal_daily,
        signal_positions=signal_positions,
        hold_daily=hold_daily,
        hold_positions=hold_positions,
        outdir=args.outdir,
    )

    signal_final = signal_daily["capital_end"].iloc[-1] if not signal_daily.empty else np.nan
    hold_final = hold_daily["capital_end"].iloc[-1] if not hold_daily.empty else np.nan
    signal_active_days = int((signal_daily["mode"] != "flat").sum()) if not signal_daily.empty else 0

    print(f"Input rows: {len(df)}")
    print(f"Trading days: {df['date'].nunique()}")
    print(f"Signal threshold: +/-{args.threshold}")
    print(f"Signal strategy active days: {signal_active_days}")
    print(f"Signal strategy final capital: {signal_final:.6f}")
    print(f"Equal-weight hold final capital: {hold_final:.6f}")
    print(f"Saved outputs to: {args.outdir}")


if __name__ == "__main__":
    main()
