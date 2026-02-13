from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from evaluate_daily_direction import (
        load_strategy_outputs,
        build_signal_component_curves,
        compute_backtest_metrics,
        build_annualized_comparison_table,
    )
except ImportError:
    from .evaluate_daily_direction import (
        load_strategy_outputs,
        build_signal_component_curves,
        compute_backtest_metrics,
        build_annualized_comparison_table,
    )

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "outputs" / "strategy_daily_direction"
PLOTS_DIR = RESULTS_DIR / "plots"


def build_curve_frame(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    summary = data["summary"][["date", "signal_threshold_cum_return", "equal_weight_hold_cum_return"]].copy()
    summary = summary.rename(
        columns={
            "signal_threshold_cum_return": "signal_total",
            "equal_weight_hold_cum_return": "equal_weight_hold_total",
        }
    )

    signal_components = build_signal_component_curves(
        signal_daily=data["signal_daily"],
        signal_positions=data["signal_positions"],
    )
    signal_components = signal_components[["date", "signal_long_only", "signal_short_only"]]

    merged = summary.merge(signal_components, on="date", how="left")
    merged = merged.sort_values("date").reset_index(drop=True)
    merged[["signal_long_only", "signal_short_only"]] = (
        merged[["signal_long_only", "signal_short_only"]].ffill().fillna(0.0)
    )
    return merged


def plot_cumulative_curves(curves: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(curves["date"], curves["signal_total"], label="Signal Strategy (Total)", linewidth=2.2)
    ax.plot(curves["date"], curves["equal_weight_hold_total"], label="Equal-Weight Hold (Total)", linewidth=2.2)
    ax.plot(curves["date"], curves["signal_long_only"], label="Signal Long-only Component", linestyle="--", linewidth=1.8)
    ax.plot(curves["date"], curves["signal_short_only"], label="Signal Short-only Component", linestyle=":", linewidth=2.0)
    ax.set_title("Cumulative Return Curves")
    ax.set_xlabel("Date")
    ax.set_ylabel("Cumulative Return")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def plot_daily_returns(signal_daily: pd.DataFrame, hold_daily: pd.DataFrame, out_path: Path) -> None:
    merged = signal_daily[["date", "daily_return"]].rename(columns={"daily_return": "signal_daily_return"})
    merged = merged.merge(
        hold_daily[["date", "daily_return"]].rename(columns={"daily_return": "hold_daily_return"}),
        on="date",
        how="outer",
    ).sort_values("date")
    merged = merged.fillna(0.0)

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(merged["date"], merged["signal_daily_return"], label="Signal daily return", linewidth=1.5)
    ax.plot(merged["date"], merged["hold_daily_return"], label="Hold daily return", linewidth=1.5)
    ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.7)
    ax.set_title("Daily Return Comparison")
    ax.set_xlabel("Date")
    ax.set_ylabel("Daily Return")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def plot_signal_structure(signal_daily: pd.DataFrame, out_path: Path) -> None:
    d = signal_daily[["date", "long_exposure", "short_exposure", "n_long", "n_short"]].copy().sort_values("date")

    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)

    axes[0].plot(d["date"], d["long_exposure"], label="Long exposure", linewidth=1.8)
    axes[0].plot(d["date"], d["short_exposure"], label="Short exposure", linewidth=1.8)
    axes[0].plot(d["date"], d["long_exposure"] + d["short_exposure"], label="Net exposure", linewidth=1.8, linestyle="--")
    axes[0].set_ylabel("Exposure")
    axes[0].set_title("Signal Strategy Exposure Structure")
    axes[0].grid(alpha=0.25)
    axes[0].legend()

    axes[1].plot(d["date"], d["n_long"], label="Long tickers", linewidth=1.8)
    axes[1].plot(d["date"], d["n_short"], label="Short tickers", linewidth=1.8)
    axes[1].set_xlabel("Date")
    axes[1].set_ylabel("Count")
    axes[1].grid(alpha=0.25)
    axes[1].legend()

    fig.autofmt_xdate()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def load_or_build_annualized_table(
    data: dict[str, pd.DataFrame],
    results_dir: Path,
) -> pd.DataFrame:
    annualized_csv = results_dir / "annualized_metrics_comparison.csv"
    if annualized_csv.exists():
        table = pd.read_csv(annualized_csv)
        required = {"Metric", "Signal Strategy", "Equal-Weight Hold", "Signal - Hold"}
        if required.issubset(table.columns):
            for col in ("Signal Strategy", "Equal-Weight Hold", "Signal - Hold"):
                table[col] = pd.to_numeric(table[col], errors="coerce")
            return table

    metrics_csv = results_dir / "evaluation_metrics.csv"
    if metrics_csv.exists():
        metrics_df = pd.read_csv(metrics_csv)
    else:
        signal_metrics = compute_backtest_metrics(data["signal_daily"], strategy_name="signal_strategy")
        hold_metrics = compute_backtest_metrics(data["hold_daily"], strategy_name="equal_weight_hold")
        metrics_df = pd.DataFrame([signal_metrics, hold_metrics])
    return build_annualized_comparison_table(metrics_df)


def _format_metric_value(metric: str, value: float, is_diff: bool = False) -> str:
    if pd.isna(value):
        return "N/A"
    percent_metrics = {
        "Cumulative Return",
        "Annualized Return",
        "Annualized Volatility",
        "Max Drawdown",
        "Win Rate",
    }
    if metric in percent_metrics:
        if is_diff:
            return f"{value * 100:+.2f} pp"
        return f"{value * 100:.2f}%"
    if is_diff:
        return f"{value:+.3f}"
    return f"{value:.3f}"


def plot_annualized_comparison_table(table_df: pd.DataFrame, out_path: Path) -> None:
    display_df = table_df.copy()
    display_df["Signal Strategy"] = [
        _format_metric_value(m, v) for m, v in zip(display_df["Metric"], display_df["Signal Strategy"])
    ]
    display_df["Equal-Weight Hold"] = [
        _format_metric_value(m, v) for m, v in zip(display_df["Metric"], display_df["Equal-Weight Hold"])
    ]
    display_df["Signal - Hold"] = [
        _format_metric_value(m, v, is_diff=True) for m, v in zip(display_df["Metric"], display_df["Signal - Hold"])
    ]

    fig_h = max(2.8, 0.62 * len(display_df) + 1.8)
    fig, ax = plt.subplots(figsize=(11, fig_h))
    ax.axis("off")
    table = ax.table(
        cellText=display_df.values,
        colLabels=display_df.columns,
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 1.4)

    for (r, c), cell in table.get_celld().items():
        if r == 0:
            cell.set_facecolor("#E9EEF5")
            cell.set_text_props(weight="bold")
        elif c == 0:
            cell.set_facecolor("#F8FAFD")
            cell.set_text_props(weight="bold")
        elif c == 3:
            metric_idx = r - 1
            if metric_idx >= 0 and metric_idx < len(table_df):
                diff_val = table_df.iloc[metric_idx]["Signal - Hold"]
                if pd.notna(diff_val):
                    if diff_val > 0:
                        cell.set_facecolor("#E8F5E9")
                    elif diff_val < 0:
                        cell.set_facecolor("#FDECEA")

    ax.set_title(
        "Backtest Metrics Comparison (Signal Strategy vs Equal-Weight Hold)",
        fontsize=12,
        pad=18,
    )
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Visualize strategy_daily_direction outputs (without S&P 500 benchmark)."
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=RESULTS_DIR,
        help="Directory containing strategy output CSV files.",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=PLOTS_DIR,
        help="Directory to save plots.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = load_strategy_outputs(args.results_dir)
    args.outdir.mkdir(parents=True, exist_ok=True)
    curves = build_curve_frame(data)
    curves_csv = args.outdir / "strategy_cumulative_curves.csv"
    curves.to_csv(curves_csv, index=False, float_format="%.8f")

    curve_plot = args.outdir / "cumulative_returns_4curves.png"
    daily_ret_plot = args.outdir / "daily_returns_signal_vs_hold.png"
    structure_plot = args.outdir / "signal_exposure_and_counts.png"
    annualized_table_csv = args.outdir / "annualized_metrics_comparison.csv"
    annualized_table_plot = args.outdir / "annualized_metrics_comparison_table.png"

    plot_cumulative_curves(curves, curve_plot)
    plot_daily_returns(data["signal_daily"], data["hold_daily"], daily_ret_plot)
    plot_signal_structure(data["signal_daily"], structure_plot)
    annualized_table_df = load_or_build_annualized_table(data, args.results_dir)
    annualized_table_df.to_csv(annualized_table_csv, index=False, float_format="%.8f")
    plot_annualized_comparison_table(annualized_table_df, annualized_table_plot)

    print(f"Saved curves csv: {curves_csv}")
    print(f"Saved annualized table csv: {annualized_table_csv}")
    print(f"Saved plot: {curve_plot}")
    print(f"Saved plot: {daily_ret_plot}")
    print(f"Saved plot: {structure_plot}")
    print(f"Saved plot: {annualized_table_plot}")


if __name__ == "__main__":
    main()
