from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PLOTS_DIR = BASE_DIR / "outputs" / "plots_monthly"


def assign_bins(f: pd.Series, k: int) -> pd.Series:
    n = len(f)
    ranks = f.rank(method="first")
    bins = np.floor((ranks - 1) * k / n).astype(int) + 1
    return bins.clip(1, k)


def compute_series(df: pd.DataFrame, k: int = 4) -> Dict[str, object]:
    """Compute per-date series needed for visualization."""
    rankic = []
    quant_raw = {i: [] for i in range(1, k + 1)}
    ls_raw = []
    tie_y = []
    tie_f = []
    p0 = []
    port_raw = []

    for date, g in df.groupby("date", sort=True):
        f = g["sentiment"]
        y = g["N_RET"]
        if len(f) < 2:
            continue
        # RankIC (raw/ex identical under demean)
        rankic.append((date, f.rank().corr(y.rank())))

        tie_y.append((date, 1 - y.nunique() / len(y)))
        tie_f.append((date, 1 - f.nunique() / len(f)))
        p0.append((date, (y == 0).mean()))

        bins = assign_bins(f, k)
        g = g.assign(bin=bins, y=y, y_ex=y - y.mean())
        grouped = g.groupby("bin")
        for bin_id in range(1, k + 1):
            if bin_id in grouped.groups:
                r_raw = grouped.get_group(bin_id)["y"].mean()
            else:
                r_raw = np.nan
            quant_raw[bin_id].append((date, r_raw))
        if 1 in grouped.groups and k in grouped.groups:
            ls_raw.append((date, grouped.get_group(k)["y"].mean() - grouped.get_group(1)["y"].mean()))
            top = grouped.get_group(k)
            bot = grouped.get_group(1)
            port_raw.append((date, (top["y"] / len(top)).sum() - (bot["y"] / len(bot)).sum()))

    return {
        "rankic": rankic,
        "quant_raw": quant_raw,
        "ls_raw": ls_raw,
        "tie_y": tie_y,
        "tie_f": tie_f,
        "p0": p0,
        "port_raw": port_raw,
    }


def plot_rankic(rankic: List[Tuple[pd.Timestamp, float]], outdir: Path) -> None:
    if not rankic:
        return
    dates, vals = zip(*rankic)
    s = pd.Series(vals, index=pd.to_datetime(dates)).sort_index()

    # Line with rolling means and cumulative
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    ax = axes[0, 0]
    ax.plot(s.index, s.values, label="RankIC")
    ax.axhline(0, color="k", linestyle="--", linewidth=1)
    ax.set_title("RankIC over time")
    ax.legend()

    ax = axes[0, 1]
    for w in (6, 12):
        ax.plot(s.index, s.rolling(w).mean(), label=f"roll mean {w}")
    ax.axhline(0, color="k", linestyle="--", linewidth=1)
    ax.set_title("Rolling means")
    ax.legend()

    ax = axes[1, 0]
    ax.hist(s.values, bins=30, color="steelblue", alpha=0.7)
    ax.axvline(s.mean(), color="red", linestyle="--", label=f"mean={s.mean():.3f}")
    ax.set_title("RankIC distribution")
    ax.legend()

    ax = axes[1, 1]
    ax.plot(s.index, s.cumsum(), label="cumsum RankIC")
    ax.axhline(0, color="k", linestyle="--", linewidth=1)
    ax.set_title("Cumulative RankIC")
    ax.legend()

    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(outdir / "rankic.png", dpi=200)
    plt.close(fig)


def plot_quantiles(quant_raw: Dict[int, List[Tuple[pd.Timestamp, float]]], k: int, outdir: Path) -> None:
    # Average bar with error bars
    means = []
    stds = []
    for bin_id in range(1, k + 1):
        series = pd.Series([v for _, v in quant_raw[bin_id]])
        means.append(series.mean())
        stds.append(series.std())

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(range(1, k + 1), means, yerr=stds, color="skyblue", alpha=0.8, capsize=4)
    ax.set_xlabel("Quantile bin")
    ax.set_ylabel("Avg return")
    ax.set_title("Average quantile returns (raw)")
    fig.tight_layout()
    fig.savefig(outdir / "quantile_bar.png", dpi=200)
    plt.close(fig)

    # Heatmap across time
    all_dates = sorted({d for vals in quant_raw.values() for d, _ in vals})
    data = np.full((len(all_dates), k), np.nan)
    date_idx = {d: i for i, d in enumerate(all_dates)}
    for bin_id in range(1, k + 1):
        for d, v in quant_raw[bin_id]:
            data[date_idx[d], bin_id - 1] = v
    fig, ax = plt.subplots(figsize=(10, 6))
    c = ax.imshow(data, aspect="auto", origin="lower", cmap="RdBu", vmin=-np.nanmax(np.abs(data)), vmax=np.nanmax(np.abs(data)))
    ax.set_yticks(range(0, len(all_dates), max(1, len(all_dates) // 10)))
    ax.set_yticklabels([pd.to_datetime(all_dates[i]).strftime("%Y-%m") for i in ax.get_yticks().astype(int)])
    ax.set_xticks(range(k))
    ax.set_xticklabels([str(i) for i in range(1, k + 1)])
    ax.set_xlabel("Quantile bin")
    ax.set_ylabel("Date")
    ax.set_title("Quantile returns heatmap (raw)")
    fig.colorbar(c, ax=ax)
    fig.tight_layout()
    fig.savefig(outdir / "quantile_heatmap.png", dpi=200)
    plt.close(fig)


def plot_ls(ls_raw: List[Tuple[pd.Timestamp, float]], outdir: Path) -> None:
    if not ls_raw:
        return
    dates, vals = zip(*ls_raw)
    s = pd.Series(vals, index=pd.to_datetime(dates)).sort_index()
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(s.index, s.values, label="LS raw")
    ax.axhline(0, color="k", linestyle="--", linewidth=1)
    for w in (6, 12):
        ax.plot(s.index, s.rolling(w).mean(), label=f"roll mean {w}")
    ax.set_title("Long-short return series (raw)")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(outdir / "ls_series.png", dpi=200)
    plt.close(fig)


def plot_ties(tie_y: List[Tuple[pd.Timestamp, float]], tie_f: List[Tuple[pd.Timestamp, float]], p0: List[Tuple[pd.Timestamp, float]], rankic: List[Tuple[pd.Timestamp, float]], outdir: Path) -> None:
    if not tie_y:
        return
    def to_series(lst):
        d, v = zip(*lst)
        return pd.Series(v, index=pd.to_datetime(d)).sort_index()
    ty = to_series(tie_y)
    tf = to_series(tie_f)
    pz = to_series(p0)
    ric = to_series(rankic)
    fig, axes = plt.subplots(3, 2, figsize=(12, 10))
    for ax, series, title in zip(axes[:,0], [ty, tf, pz], ["tie_y", "tie_f", "p0"]):
        ax.plot(series.index, series.values)
        ax.set_title(title)
    for ax, series, title in zip(axes[:,1], [ty, tf, pz], ["tie_y hist", "tie_f hist", "p0 hist"]):
        ax.hist(series.values, bins=30, color="steelblue", alpha=0.7)
        ax.set_title(title)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(outdir / "ties.png", dpi=200)
    plt.close(fig)

    # Scatter |RankIC| vs tie/p0
    abs_ric = ric.abs().reindex(ty.index, method="nearest")
    fig, axes = plt.subplots(1, 3, figsize=(12,4))
    for ax, series, title in zip(axes, [ty, tf, pz], ["tie_y", "tie_f", "p0"]):
        ax.scatter(series.values, abs_ric.values, alpha=0.6)
        ax.set_xlabel(title)
        ax.set_ylabel("|RankIC|")
    fig.tight_layout()
    fig.savefig(outdir / "ties_scatter.png", dpi=200)
    plt.close(fig)


def plot_portfolio(port_raw: List[Tuple[pd.Timestamp, float]], outdir: Path) -> None:
    if not port_raw:
        return
    dates, vals = zip(*port_raw)
    s = pd.Series(vals, index=pd.to_datetime(dates)).sort_index()
    nav = (1 + s).cumprod()
    rolling_sr = s.rolling(12).apply(lambda x: x.mean() / x.std() * np.sqrt(12) if x.std() not in (0, np.nan) else np.nan, raw=False)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes[0,0].plot(nav.index, nav.values)
    axes[0,0].set_title("NAV (raw/ex identical)")
    dd = 1 - nav / nav.cummax()
    axes[0,1].plot(dd.index, dd.values)
    axes[0,1].set_title("Drawdown")
    axes[1,0].hist(s.values, bins=30, color="steelblue", alpha=0.7)
    axes[1,0].set_title("Monthly return distribution")
    axes[1,1].plot(rolling_sr.index, rolling_sr.values)
    axes[1,1].set_title("Rolling Sharpe (12)")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(outdir / "portfolio.png", dpi=200)
    plt.close(fig)


def generate_plots(input_path: Path, output_dir: Path, k: int = 4) -> None:
    df = pd.read_csv(input_path)
    df = df[df["date"] != "2021-06"]
    df = df.dropna(subset=["sentiment", "N_RET"])
    series = compute_series(df, k=k)
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_rankic(series["rankic"], output_dir)
    plot_quantiles(series["quant_raw"], k, output_dir)
    plot_ls(series["ls_raw"], output_dir)
    plot_ties(series["tie_y"], series["tie_f"], series["p0"], series["rankic"], output_dir)
    plot_portfolio(series["port_raw"], output_dir)
    print(f"Saved plots to {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualize monthly evaluation metrics.")
    parser.add_argument("--input", type=Path, default=DATA_DIR / "train_df_monthly_fused.csv", help="Path to fused monthly CSV.")
    parser.add_argument("--outdir", type=Path, default=PLOTS_DIR, help="Output directory for plots.")
    parser.add_argument("--bins", type=int, default=4, help="Number of quantile bins.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_plots(args.input, args.outdir, k=args.bins)


if __name__ == "__main__":
    main()
