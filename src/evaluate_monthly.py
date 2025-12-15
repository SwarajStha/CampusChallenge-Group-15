from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def spearman_rank_corr(x: pd.Series, y: pd.Series) -> float:
    rx = x.rank(method="average")
    ry = y.rank(method="average")
    return rx.corr(ry)


def assign_bins(f: pd.Series, k: int) -> pd.Series:
    """Approximate equal-count bins using rank order."""
    n = len(f)
    ranks = f.rank(method="first")
    bins = np.floor((ranks - 1) * k / n).astype(int) + 1
    bins = bins.clip(1, k)
    return bins


def summarize_series(series: List[float]) -> Tuple[float, float, float]:
    arr = np.asarray(series, dtype=float)
    mean = float(np.nanmean(arr))
    std = float(np.nanstd(arr, ddof=1)) if len(arr) > 1 else np.nan
    t_stat = mean / (std / np.sqrt(len(arr))) if (len(arr) > 1 and std not in (0, np.nan)) else np.nan
    return mean, std, t_stat


def evaluate(df: pd.DataFrame, k: int = 4, ann_factor: float = np.sqrt(12)) -> Dict[str, object]:
    results: Dict[str, object] = {}

    # Drop rows with missing sentiment or N_RET
    df = df.dropna(subset=["sentiment", "N_RET"]).copy()
    df["date"] = pd.to_datetime(df["date"])

    rankic_raw: List[float] = []
    rankic_ex: List[float] = []
    tie_y: List[float] = []
    tie_f: List[float] = []
    p0_list: List[float] = []

    quant_raw = {i: [] for i in range(1, k + 1)}
    quant_ex = {i: [] for i in range(1, k + 1)}
    ls_raw: List[float] = []
    ls_ex: List[float] = []
    port_raw: List[float] = []
    port_ex: List[float] = []

    for _, g in df.groupby("date", sort=True):
        f = g["sentiment"]
        y = g["N_RET"]
        if len(f) < 2:
            continue

        y_ex = y - y.mean()

        # RankIC
        rankic_raw.append(spearman_rank_corr(f, y))
        rankic_ex.append(spearman_rank_corr(f, y_ex))

        # Ties
        n = len(g)
        tie_y.append(1 - y.nunique() / n)
        tie_f.append(1 - f.nunique() / n)
        p0_list.append((y == 0).mean())

        # Quantile bins
        bins = assign_bins(f, k)
        g = g.assign(bin=bins, y=y, y_ex=y_ex)
        grouped = g.groupby("bin")

        # Ensure we have all bins
        r_raw = {}
        r_ex = {}
        for bin_id in range(1, k + 1):
            grp = grouped.get_group(bin_id) if bin_id in grouped.groups else None
            if grp is None or grp.empty:
                r_raw[bin_id] = np.nan
                r_ex[bin_id] = np.nan
            else:
                r_raw[bin_id] = grp["y"].mean()
                r_ex[bin_id] = grp["y_ex"].mean()
        for bin_id in range(1, k + 1):
            quant_raw[bin_id].append(r_raw[bin_id])
            quant_ex[bin_id].append(r_ex[bin_id])

        if not np.isnan(r_raw[k]) and not np.isnan(r_raw[1]):
            ls_raw.append(r_raw[k] - r_raw[1])
        if not np.isnan(r_ex[k]) and not np.isnan(r_ex[1]):
            ls_ex.append(r_ex[k] - r_ex[1])

        # Portfolio returns (long top, short bottom)
        top = g[g["bin"] == k]
        bot = g[g["bin"] == 1]
        if not top.empty and not bot.empty:
            w_top = 1 / len(top)
            w_bot = -1 / len(bot)
            port_raw.append((top["y"] * w_top).sum() + (bot["y"] * w_bot).sum())
            port_ex.append((top["y_ex"] * w_top).sum() + (bot["y_ex"] * w_bot).sum())

    T = len(rankic_raw)
    def agg_rankic(series: List[float]) -> Dict[str, float]:
        mean, std, t = summarize_series(series)
        hr = float(np.mean(np.asarray(series) > 0)) if series else np.nan
        ir = mean / std if std not in (0, np.nan) else np.nan
        return {"mean": mean, "std": std, "ir": ir, "hr": hr, "t": t}

    results["rankic_raw"] = agg_rankic(rankic_raw)
    results["rankic_ex"] = agg_rankic(rankic_ex)

    def agg_quant(qdict: Dict[int, List[float]]) -> Tuple[List[float], float]:
        avg = [np.nanmean(qdict[i]) for i in range(1, k + 1)]
        mono = spearman_rank_corr(pd.Series(range(1, k + 1)), pd.Series(avg))
        return avg, mono

    avg_raw, mono_raw = agg_quant(quant_raw)
    avg_ex, mono_ex = agg_quant(quant_ex)

    def agg_ls(series: List[float]) -> Dict[str, float]:
        mean, std, t = summarize_series(series)
        ir = mean / std if std not in (0, np.nan) else np.nan
        sr_ann = ir * ann_factor if ir is not np.nan else np.nan
        return {"mean": mean, "std": std, "ir": ir, "sr_ann": sr_ann, "t": t}

    results["quant_raw"] = {"avg": avg_raw, "mono": mono_raw, "ls": agg_ls(ls_raw)}
    results["quant_ex"] = {"avg": avg_ex, "mono": mono_ex, "ls": agg_ls(ls_ex)}

    def agg_ties(arr: List[float]) -> Dict[str, float]:
        vals = np.asarray(arr, dtype=float)
        return {
            "mean": float(np.nanmean(vals)),
            "p25": float(np.nanpercentile(vals, 25)),
            "p50": float(np.nanpercentile(vals, 50)),
            "p75": float(np.nanpercentile(vals, 75)),
        }

    results["ties"] = {
        "tie_y": agg_ties(tie_y),
        "tie_f": agg_ties(tie_f),
        "p0": agg_ties(p0_list),
    }

    def agg_port(ret_series: List[float]) -> Dict[str, object]:
        arr = np.asarray(ret_series, dtype=float)
        mean = float(np.nanmean(arr))
        std = float(np.nanstd(arr, ddof=1)) if len(arr) > 1 else np.nan
        ir = mean / std if std not in (0, np.nan) else np.nan
        sr_ann = ir * ann_factor if ir is not np.nan else np.nan
        t = mean / (std / np.sqrt(len(arr))) if (len(arr) > 1 and std not in (0, np.nan)) else np.nan
        nav = np.cumprod(1 + arr).tolist()
        mu_ann = mean * 12
        sigma_ann = std * np.sqrt(12) if std not in (0, np.nan) else np.nan
        return {
            "mean": mean,
            "std": std,
            "ir": ir,
            "sr_ann": sr_ann,
            "t": t,
            "nav": nav,
            "mu_ann": mu_ann,
            "sigma_ann": sigma_ann,
        }

    results["portfolio_raw"] = agg_port(port_raw)
    results["portfolio_ex"] = agg_port(port_ex)

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate monthly fused sentiment with RankIC and portfolio metrics.")
    parser.add_argument("--input", type=Path, default=DATA_DIR / "train_df_monthly_fused.csv", help="Path to fused monthly data.")
    parser.add_argument("--output", type=Path, default=None, help="Optional path to write summary JSON.")
    parser.add_argument("--bins", type=int, default=4, help="Number of quantile bins (default: 4).")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.input)
    df = df[df["date"] != "2021-06"]
    summary = evaluate(df, k=args.bins)

    if args.output:
        import json

        with open(args.output, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"Summary written to {args.output}")

    print("RankIC raw:", summary["rankic_raw"])
    print("RankIC ex:", summary["rankic_ex"])
    print("Quant raw:", summary["quant_raw"])
    print("Quant ex:", summary["quant_ex"])
    print("Ties:", summary["ties"])
    print("Portfolio raw:", {k: v for k, v in summary["portfolio_raw"].items() if k != "nav"})
    print("Portfolio ex:", {k: v for k, v in summary["portfolio_ex"].items() if k != "nav"})


if __name__ == "__main__":
    main()
