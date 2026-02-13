from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs" / "strategy_daily_direction"


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return pd.read_csv(path)


def load_strategy_outputs(results_dir: Path) -> dict[str, pd.DataFrame]:
    files = {
        "signal_daily": "signal_strategy_daily_records.csv",
        "signal_positions": "signal_strategy_positions.csv",
        "hold_daily": "equal_weight_hold_daily_records.csv",
        "hold_positions": "equal_weight_hold_positions.csv",
        "summary": "performance_summary.csv",
    }
    data = {k: _load_csv(results_dir / v) for k, v in files.items()}

    for key in ("signal_daily", "signal_positions", "hold_daily", "hold_positions", "summary"):
        if "date" in data[key].columns:
            data[key]["date"] = pd.to_datetime(data[key]["date"], errors="coerce").dt.date

    numeric_cols = {
        "signal_daily": ["daily_return", "capital_start", "pnl", "capital_end"],
        "hold_daily": ["daily_return", "capital_start", "pnl", "capital_end"],
        "signal_positions": ["weight", "N_RET", "contribution"],
        "hold_positions": ["weight", "N_RET", "contribution"],
        "summary": [
            "signal_threshold_capital",
            "equal_weight_hold_capital",
            "signal_threshold_cum_return",
            "equal_weight_hold_cum_return",
        ],
    }
    for key, cols in numeric_cols.items():
        for col in cols:
            if col in data[key].columns:
                data[key][col] = pd.to_numeric(data[key][col], errors="coerce")

    return data


def _max_drawdown(capital_series: pd.Series) -> float:
    if capital_series.empty:
        return np.nan
    running_max = capital_series.cummax()
    drawdown = capital_series / running_max - 1.0
    return float(drawdown.min())


def _annualized_return(total_return: float, total_days: int, trading_days: int = 252) -> float:
    if total_days <= 0:
        return np.nan
    return float((1.0 + total_return) ** (trading_days / total_days) - 1.0)


def compute_backtest_metrics(
    daily_df: pd.DataFrame,
    strategy_name: str,
    trading_days: int = 252,
) -> dict[str, float | int | str]:
    required = {"date", "daily_return", "capital_start", "capital_end"}
    if missing := required - set(daily_df.columns):
        raise KeyError(f"{strategy_name} daily records missing columns: {missing}")

    d = daily_df.copy()
    d = d.dropna(subset=["date", "daily_return", "capital_start", "capital_end"]).sort_values("date").reset_index(drop=True)
    if d.empty:
        return {"strategy": strategy_name, "total_days": 0}

    initial_capital = float(d["capital_start"].iloc[0])
    final_capital = float(d["capital_end"].iloc[-1])
    total_return = final_capital / initial_capital - 1.0
    mean_daily = float(d["daily_return"].mean())
    std_daily = float(d["daily_return"].std(ddof=1))
    annual_vol = std_daily * np.sqrt(trading_days) if np.isfinite(std_daily) else np.nan
    sharpe = np.nan
    if std_daily > 0:
        sharpe = mean_daily / std_daily * np.sqrt(trading_days)

    mdd = _max_drawdown(d["capital_end"])
    annual_ret = _annualized_return(total_return=total_return, total_days=len(d), trading_days=trading_days)
    calmar = np.nan
    if mdd < 0:
        calmar = annual_ret / abs(mdd)

    active_days = int((d["mode"] != "flat").sum()) if "mode" in d.columns else int((d["daily_return"] != 0).sum())
    win_rate = float((d["daily_return"] > 0).mean())

    return {
        "strategy": strategy_name,
        "total_days": int(len(d)),
        "active_days": active_days,
        "initial_capital": initial_capital,
        "final_capital": final_capital,
        "total_return": float(total_return),
        "annualized_return": float(annual_ret),
        "mean_daily_return": mean_daily,
        "std_daily_return": std_daily,
        "annualized_volatility": float(annual_vol),
        "sharpe": float(sharpe) if np.isfinite(sharpe) else np.nan,
        "max_drawdown": float(mdd),
        "calmar": float(calmar) if np.isfinite(calmar) else np.nan,
        "win_rate": win_rate,
        "best_day_return": float(d["daily_return"].max()),
        "worst_day_return": float(d["daily_return"].min()),
    }


def build_signal_component_curves(
    signal_daily: pd.DataFrame,
    signal_positions: pd.DataFrame,
) -> pd.DataFrame:
    base = signal_daily[["date", "daily_return", "capital_start", "capital_end"]].copy()
    base = base.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    if base.empty:
        return pd.DataFrame(columns=["date", "signal_total", "signal_long_only", "signal_short_only"])

    all_dates = pd.Index(base["date"], name="date")
    long_daily = (
        signal_positions[signal_positions["side"] == "long"]
        .groupby("date")["contribution"]
        .sum()
        .reindex(all_dates, fill_value=0.0)
    )
    short_daily = (
        signal_positions[signal_positions["side"] == "short"]
        .groupby("date")["contribution"]
        .sum()
        .reindex(all_dates, fill_value=0.0)
    )

    out = pd.DataFrame({"date": all_dates.to_list()})
    out["signal_total_daily"] = pd.to_numeric(base["daily_return"], errors="coerce").fillna(0.0).to_numpy()
    out["signal_long_daily"] = long_daily.to_numpy()
    out["signal_short_daily"] = short_daily.to_numpy()
    out["signal_total"] = (1.0 + out["signal_total_daily"]).cumprod() - 1.0
    out["signal_long_only"] = (1.0 + out["signal_long_daily"]).cumprod() - 1.0
    out["signal_short_only"] = (1.0 + out["signal_short_daily"]).cumprod() - 1.0
    return out


def build_annualized_comparison_table(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a two-strategy comparison table with common quant backtest metrics.
    """
    strategy_index = metrics_df.set_index("strategy")
    required_strategies = ["signal_strategy", "equal_weight_hold"]
    missing = [s for s in required_strategies if s not in strategy_index.index]
    if missing:
        raise KeyError(f"Missing required strategies in metrics: {missing}")

    signal = strategy_index.loc["signal_strategy"]
    hold = strategy_index.loc["equal_weight_hold"]

    metric_map = [
        ("Cumulative Return", "total_return"),
        ("Annualized Return", "annualized_return"),
        ("Annualized Volatility", "annualized_volatility"),
        ("Sharpe Ratio", "sharpe"),
        ("Calmar Ratio", "calmar"),
        ("Max Drawdown", "max_drawdown"),
        ("Win Rate", "win_rate"),
    ]

    rows: list[dict[str, float | str]] = []
    for label, col in metric_map:
        signal_val = pd.to_numeric(signal.get(col), errors="coerce")
        hold_val = pd.to_numeric(hold.get(col), errors="coerce")
        rows.append(
            {
                "Metric": label,
                "Signal Strategy": float(signal_val) if pd.notna(signal_val) else np.nan,
                "Equal-Weight Hold": float(hold_val) if pd.notna(hold_val) else np.nan,
                "Signal - Hold": (
                    float(signal_val - hold_val)
                    if pd.notna(signal_val) and pd.notna(hold_val)
                    else np.nan
                ),
            }
        )

    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate financial backtest metrics from strategy_daily_direction outputs."
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory containing strategy output CSV files.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=OUTPUT_DIR / "evaluation_metrics.csv",
        help="Path to save computed metrics CSV.",
    )
    parser.add_argument(
        "--components-out",
        type=Path,
        default=OUTPUT_DIR / "signal_component_curves.csv",
        help="Path to save signal strategy total/long/short curve CSV.",
    )
    parser.add_argument(
        "--annualized-table-out",
        type=Path,
        default=OUTPUT_DIR / "annualized_metrics_comparison.csv",
        help="Path to save annualized comparison table (two strategies).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = load_strategy_outputs(args.results_dir)

    signal_metrics = compute_backtest_metrics(data["signal_daily"], strategy_name="signal_strategy")
    hold_metrics = compute_backtest_metrics(data["hold_daily"], strategy_name="equal_weight_hold")

    component_curves = build_signal_component_curves(
        signal_daily=data["signal_daily"],
        signal_positions=data["signal_positions"],
    )

    component_daily = component_curves[["date", "signal_long_daily", "signal_short_daily"]].copy()
    if "capital_start" in data["signal_daily"].columns and not data["signal_daily"].empty:
        component_daily["capital_start"] = float(data["signal_daily"]["capital_start"].iloc[0])
        component_daily["capital_end"] = (1.0 + component_daily["signal_long_daily"]).cumprod() * component_daily["capital_start"]
        long_metrics = compute_backtest_metrics(
            component_daily.rename(columns={"signal_long_daily": "daily_return"}),
            strategy_name="signal_long_only_component",
        )
        component_daily["capital_end"] = (1.0 + component_daily["signal_short_daily"]).cumprod() * component_daily["capital_start"]
        short_metrics = compute_backtest_metrics(
            component_daily.rename(columns={"signal_short_daily": "daily_return"}),
            strategy_name="signal_short_only_component",
        )
    else:
        long_metrics = {"strategy": "signal_long_only_component", "total_days": 0}
        short_metrics = {"strategy": "signal_short_only_component", "total_days": 0}

    metrics_df = pd.DataFrame([signal_metrics, hold_metrics, long_metrics, short_metrics])
    annualized_table_df = build_annualized_comparison_table(metrics_df)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(args.out, index=False, float_format="%.8f")
    args.components_out.parent.mkdir(parents=True, exist_ok=True)
    component_curves.to_csv(args.components_out, index=False, float_format="%.8f")
    args.annualized_table_out.parent.mkdir(parents=True, exist_ok=True)
    annualized_table_df.to_csv(args.annualized_table_out, index=False, float_format="%.8f")

    print("Saved metrics to:", args.out)
    print("Saved signal component curves to:", args.components_out)
    print("Saved annualized comparison table to:", args.annualized_table_out)
    print(annualized_table_df.to_string(index=False))
    print(metrics_df.to_string(index=False))


if __name__ == "__main__":
    main()
