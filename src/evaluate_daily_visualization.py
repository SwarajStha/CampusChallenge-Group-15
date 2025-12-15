from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter
from scipy import stats

from evaluate_daily import load_data, quantile_test, three_state_strategy

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PLOTS_DIR = BASE_DIR / "outputs" / "plots_daily"


def scatter_with_fit(df: pd.DataFrame, outdir: Path) -> None:
    s, r = df["sentiment"], df["N_RET"]
    slope, intercept, _, _, _ = stats.linregress(s, r)
    xfit = np.linspace(s.min(), s.max(), 100)
    yfit = intercept + slope * xfit
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(s, r, alpha=0.5, s=8, color="steelblue")
    ax.plot(xfit, yfit, color="red", label=f"fit slope={slope:.4f}")
    ax.set_xlabel("sentiment s_t")
    ax.set_ylabel("N_RET_{t+1}")
    ax.set_title("Sentiment vs next-day return")
    ax.legend()
    fig.tight_layout()
    fig.savefig(outdir / "scatter_fit.png", dpi=200)
    plt.close(fig)


def binned_means(df: pd.DataFrame, k: int, outdir: Path) -> None:
    df = df.copy()
    df["bin"] = pd.qcut(df["sentiment"], q=k, labels=False, duplicates="drop")
    grouped = df.groupby("bin")
    x = grouped["sentiment"].mean()
    y = grouped["N_RET"].mean()
    se = grouped["N_RET"].apply(lambda v: v.std(ddof=1) / np.sqrt(len(v)))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(range(len(x)), y, yerr=se, color="skyblue", alpha=0.8, capsize=4)
    ax.set_xticks(range(len(x)))
    ax.set_xticklabels([f"bin {i+1}" for i in range(len(x))])
    ax.set_ylabel("mean N_RET")
    ax.set_title("Binned means of sentiment vs next-day return")
    fig.tight_layout()
    fig.savefig(outdir / "binned_means.png", dpi=200)
    plt.close(fig)


def rolling_ic(df: pd.DataFrame, windows: List[int], outdir: Path) -> None:
    s = df["sentiment"].to_numpy()
    r = df["N_RET"].to_numpy()
    dates = df["date"]
    fig, ax = plt.subplots(figsize=(10, 4))
    for w in windows:
        ic_vals = []
        ic_dates = []
        for i in range(w, len(df)):
            ic = pd.Series(s[i - w : i]).rank().corr(pd.Series(r[i - w : i]).rank())
            ic_vals.append(ic)
            ic_dates.append(dates.iloc[i])
        ax.plot(ic_dates, ic_vals, label=f"IC {w}")
    ax.axhline(0, color="k", linestyle="--", linewidth=1)
    ax.set_title("Rolling IC")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(outdir / "rolling_ic.png", dpi=200)
    plt.close(fig)


def residual_diagnostics(df: pd.DataFrame, outdir: Path) -> None:
    s = df["sentiment"]
    r = df["N_RET"]
    slope, intercept, _, _, _ = stats.linregress(s, r)
    resid = r - (intercept + slope * s)
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    axes[0].hist(resid, bins=30, color="steelblue", alpha=0.8)
    axes[0].set_title("Residuals histogram")
    stats.probplot(resid, dist="norm", plot=axes[1])
    axes[1].set_title("Residuals QQ")
    axes[2].scatter(s, resid, alpha=0.5, s=8)
    axes[2].axhline(0, color="k", linestyle="--", linewidth=1)
    axes[2].set_xlabel("sentiment")
    axes[2].set_ylabel("residual")
    axes[2].set_title("Residuals vs sentiment")
    fig.tight_layout()
    fig.savefig(outdir / "residuals.png", dpi=200)
    plt.close(fig)


def quantile_plots(df: pd.DataFrame, outdir: Path) -> None:
    k = 10
    df = df.copy()
    df["bin"] = pd.qcut(df["sentiment"], q=k, labels=False, duplicates="drop")
    grouped = df.groupby("bin")
    means = grouped["N_RET"].mean()
    se = grouped["N_RET"].apply(lambda v: v.std(ddof=1) / np.sqrt(len(v)))
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(range(len(means)), means, yerr=se, color="skyblue", alpha=0.8, capsize=4)
    ax.set_xticks(range(len(means)))
    ax.set_xticklabels([f"{i+1}" for i in range(len(means))])
    ax.set_title("Quantile mean returns (10 bins)")
    fig.tight_layout()
    fig.savefig(outdir / "quantile_bar.png", dpi=200)
    plt.close(fig)

    # Boxplot for High/Mid/Low
    q_low, q_high = df["sentiment"].quantile([0.3, 0.7])
    low = df[df["sentiment"] <= q_low]["N_RET"]
    mid = df[(df["sentiment"] > q_low) & (df["sentiment"] < q_high)]["N_RET"]
    high = df[df["sentiment"] >= q_high]["N_RET"]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.boxplot([low, mid, high], labels=["Low", "Mid", "High"], showmeans=True)
    ax.set_title("High/Mid/Low return distribution")
    fig.tight_layout()
    fig.savefig(outdir / "high_low_box.png", dpi=200)
    plt.close(fig)


def roc_and_hit(df: pd.DataFrame, outdir: Path) -> None:
    try:
        from sklearn.metrics import roc_curve, auc
    except ImportError:  # pragma: no cover
        return
    y = (df["N_RET"] > 0).astype(int)
    scores = df["sentiment"]
    fpr, tpr, _ = roc_curve(y, scores)
    auc_val = auc(fpr, tpr)
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot(fpr, tpr, label=f"AUC={auc_val:.3f}")
    ax.plot([0, 1], [0, 1], linestyle="--", color="k")
    ax.set_xlabel("FPR")
    ax.set_ylabel("TPR")
    ax.set_title("ROC (directional)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(outdir / "roc.png", dpi=200)
    plt.close(fig)

    q_low, q_high = scores.quantile([0.3, 0.7])
    low = y[scores <= q_low]
    high = y[scores >= q_high]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(["Low", "High"], [low.mean(), high.mean()], color=["tomato", "seagreen"])
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_title("Hit rate: High vs Low")
    fig.tight_layout()
    fig.savefig(outdir / "hit_rate.png", dpi=200)
    plt.close(fig)


def strategy_plots(df: pd.DataFrame, outdir: Path, q_low: float = 0.3, q_high: float = 0.7) -> None:
    s = df["sentiment"]
    r = df["N_RET"]
    tau_low = s.quantile(q_low)
    tau_high = s.quantile(q_high)
    p = np.where(s >= tau_high, 1, np.where(s <= tau_low, -1, 0))
    pnl = p * r
    dates = df["date"]

    # Equity curves
    eq_total = (1 + pnl).cumprod()
    eq_long = (1 + pnl.where(p == 1, 0)).cumprod()
    eq_short = (1 + pnl.where(p == -1, 0)).cumprod()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(dates, eq_total, label="Total")
    ax.plot(dates, eq_long, label="Long-only")
    ax.plot(dates, eq_short, label="Short-only")
    ax.set_title("Equity curves (3-state)")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(outdir / "equity.png", dpi=200)
    plt.close(fig)

    # Drawdown
    dd = 1 - eq_total / eq_total.cummax()
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(dates, dd)
    ax.set_title("Drawdown")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(outdir / "drawdown.png", dpi=200)
    plt.close(fig)

    # P&L distribution
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(pnl, bins=40, color="steelblue", alpha=0.8)
    ax.set_title("P&L distribution")
    fig.tight_layout()
    fig.savefig(outdir / "pnl_dist.png", dpi=200)
    plt.close(fig)

    # Position coverage over time
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(dates, p, alpha=0.6)
    ax.set_title("Positions over time (1/-1/0)")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(outdir / "positions.png", dpi=200)
    plt.close(fig)


def train_test_equity(df: pd.DataFrame, split: float, outdir: Path, q_low: float = 0.3, q_high: float = 0.7) -> None:
    n = len(df)
    n_train = int(n * split)
    train = df.iloc[:n_train]
    test = df.iloc[n_train:]
    tau_low = train["sentiment"].quantile(q_low)
    tau_high = train["sentiment"].quantile(q_high)
    def equity(sub: pd.DataFrame) -> pd.Series:
        p = np.where(sub["sentiment"] >= tau_high, 1, np.where(sub["sentiment"] <= tau_low, -1, 0))
        pnl = p * sub["N_RET"]
        return (1 + pnl).cumprod()
    eq_train = equity(train)
    eq_test = equity(test)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(train["date"], eq_train, label="Train")
    ax.plot(test["date"], eq_test, label="Test")
    ax.axvline(test["date"].iloc[0], color="k", linestyle="--", label="split")
    ax.set_title("Train vs Test equity")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(outdir / "train_test_equity.png", dpi=200)
    plt.close(fig)


def winrate_diagnostics(df: pd.DataFrame, q_low: float, q_high: float, outdir: Path) -> None:
    s = df["sentiment"]
    r = df["N_RET"]
    tau_low = s.quantile(q_low)
    tau_high = s.quantile(q_high)
    p = np.where(s >= tau_high, 1, np.where(s <= tau_low, -1, 0))
    pnl = p * r
    rates = {
        "P(pi>0)": (pnl > 0).mean(),
        "P(pi>0 | p!=0)": (pnl[p != 0] > 0).mean(),
        "P(pi==0)": (pnl == 0).mean(),
    }
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(rates.keys(), rates.values(), color=["seagreen", "royalblue", "gray"])
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_title("WinRate diagnostics")
    fig.tight_layout()
    fig.savefig(outdir / "winrate_diag.png", dpi=200)
    plt.close(fig)


def generate_daily_plots(
    input_path: Path,
    outdir: Path,
    winsorize: bool = False,
    q_low: float = 0.3,
    q_high: float = 0.7,
    bins: int = 10,
) -> None:
    df = load_data(input_path, winsorize=winsorize)
    outdir.mkdir(parents=True, exist_ok=True)

    scatter_with_fit(df, outdir)
    binned_means(df, bins, outdir)
    rolling_ic(df, windows=[60, 120, 252], outdir=outdir)
    residual_diagnostics(df, outdir)
    quantile_plots(df, outdir)
    roc_and_hit(df, outdir)
    strategy_plots(df, outdir, q_low=q_low, q_high=q_high)
    train_test_equity(df, split=0.6, outdir=outdir, q_low=q_low, q_high=q_high)
    winrate_diagnostics(df, q_low=q_low, q_high=q_high, outdir=outdir)
    print(f"Saved daily plots to {outdir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualize daily sentiment evaluation.")
    parser.add_argument("--input", type=Path, default=DATA_DIR / "train_df_daily_fused.csv", help="Path to daily fused data.")
    parser.add_argument("--outdir", type=Path, default=PLOTS_DIR, help="Output directory for plots.")
    parser.add_argument("--winsorize", action="store_true", help="Winsorize returns at 1/99.")
    parser.add_argument("--q-low", type=float, default=0.3, help="Low quantile threshold.")
    parser.add_argument("--q-high", type=float, default=0.7, help="High quantile threshold.")
    parser.add_argument("--bins", type=int, default=10, help="Bins for binned means / quantile bars.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_daily_plots(
        input_path=args.input,
        outdir=args.outdir,
        winsorize=args.winsorize,
        q_low=args.q_low,
        q_high=args.q_high,
        bins=args.bins,
    )


if __name__ == "__main__":
    main()
