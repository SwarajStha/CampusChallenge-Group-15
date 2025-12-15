from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

try:
    from sklearn.metrics import roc_auc_score
except ImportError:  # pragma: no cover
    roc_auc_score = None


def load_data(path: Path, winsorize: bool = False, win_q: Tuple[float, float] = (0.01, 0.99)) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df[["date", "sentiment", "N_RET"]].dropna()
    df = df.sort_values("date").reset_index(drop=True)
    if winsorize:
        low, high = df["N_RET"].quantile(win_q[0]), df["N_RET"].quantile(win_q[1])
        df["N_RET"] = df["N_RET"].clip(low, high)
    return df


def predictive_metrics(df: pd.DataFrame, nw_lags: int = 5) -> Dict[str, float]:
    s = df["sentiment"]
    r = df["N_RET"]
    pearson = s.corr(r)
    spearman = s.rank().corr(r.rank())
    X = sm.add_constant(s)
    model = sm.OLS(r, X).fit(cov_type="HAC", cov_kwds={"maxlags": nw_lags})
    beta = model.params["sentiment"]
    t_beta = model.tvalues["sentiment"]
    return {"pearson": pearson, "spearman": spearman, "beta": beta, "t_beta_nw": t_beta}


def quantile_test(df: pd.DataFrame, q_low: float = 0.3, q_high: float = 0.7) -> Dict[str, float]:
    s = df["sentiment"]
    r = df["N_RET"]
    tau_low = s.quantile(q_low)
    tau_high = s.quantile(q_high)
    low = r[s <= tau_low]
    high = r[s >= tau_high]
    delta = high.mean() - low.mean()
    t_stat, p_val = stats.ttest_ind(high, low, equal_var=False, nan_policy="omit")
    # CI via normal approximation
    se = np.sqrt(high.var(ddof=1) / len(high) + low.var(ddof=1) / len(low))
    tcrit = stats.t.ppf(0.975, df=len(high) + len(low) - 2) if len(high) + len(low) > 2 else np.nan
    ci_lower = delta - tcrit * se if not np.isnan(tcrit) else np.nan
    ci_upper = delta + tcrit * se if not np.isnan(tcrit) else np.nan
    auc = None
    hit_high = None
    hit_low = None
    if roc_auc_score is not None:
        y_bin = (r > 0).astype(int)
        mask = s.notna() & y_bin.notna()
        try:
            auc = roc_auc_score(y_bin[mask], s[mask])
        except Exception:
            auc = None
        hit_high = (high > 0).mean()
        hit_low = (low > 0).mean()
    return {
        "tau_low": tau_low,
        "tau_high": tau_high,
        "delta": delta,
        "t_stat": t_stat,
        "p_val": p_val,
        "ci": (ci_lower, ci_upper),
        "auc": auc,
        "hit_high": hit_high,
        "hit_low": hit_low,
    }


def three_state_strategy(df: pd.DataFrame, q_low: float = 0.3, q_high: float = 0.7) -> Dict[str, float]:
    s = df["sentiment"]
    r = df["N_RET"]
    tau_low = s.quantile(q_low)
    tau_high = s.quantile(q_high)

    p = np.where(s >= tau_high, 1, np.where(s <= tau_low, -1, 0))
    pnl = p * r

    mean = pnl.mean()
    std = pnl.std(ddof=1)
    sharpe = mean / std * np.sqrt(252) if std not in (0, np.nan) else np.nan
    winrate = (pnl > 0).mean()
    cov = (p != 0).mean()
    cov_long = (p == 1).mean()
    cov_short = (p == -1).mean()
    pnl_long = pnl[p == 1].mean() if cov_long > 0 else np.nan
    pnl_short = pnl[p == -1].mean() if cov_short > 0 else np.nan

    return {
        "tau_low": tau_low,
        "tau_high": tau_high,
        "mean": mean,
        "std": std,
        "sharpe_ann": sharpe,
        "winrate": winrate,
        "coverage": cov,
        "coverage_long": cov_long,
        "coverage_short": cov_short,
        "pnl_long": pnl_long,
        "pnl_short": pnl_short,
    }


def train_test_split_strategy(df: pd.DataFrame, split: float = 0.6, q_low: float = 0.3, q_high: float = 0.7) -> Dict[str, Dict[str, float]]:
    n = len(df)
    n_train = int(n * split)
    train = df.iloc[:n_train]
    test = df.iloc[n_train:]
    tau_low = train["sentiment"].quantile(q_low)
    tau_high = train["sentiment"].quantile(q_high)
    def run(df_in: pd.DataFrame) -> Dict[str, float]:
        p = np.where(df_in["sentiment"] >= tau_high, 1, np.where(df_in["sentiment"] <= tau_low, -1, 0))
        pnl = p * df_in["N_RET"]
        mean = pnl.mean()
        std = pnl.std(ddof=1)
        sharpe = mean / std * np.sqrt(252) if std not in (0, np.nan) else np.nan
        return {"mean": mean, "std": std, "sharpe_ann": sharpe, "coverage": (p != 0).mean()}
    return {"train": run(train), "test": run(test), "tau_low": tau_low, "tau_high": tau_high}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate daily sentiment vs next-day returns.")
    parser.add_argument("--input", type=Path, default=DATA_DIR / "train_df_daily_fused.csv", help="Path to fused daily file.")
    parser.add_argument("--winsorize", action="store_true", help="Winsorize returns at 1/99 percentiles.")
    parser.add_argument("--q-low", type=float, default=0.3, help="Low quantile threshold (default 0.3).")
    parser.add_argument("--q-high", type=float, default=0.7, help="High quantile threshold (default 0.7).")
    parser.add_argument("--nw-lags", type=int, default=5, help="Newey-West lags for regression.")
    parser.add_argument("--split", type=float, default=0.6, help="Train/test split ratio for OOS check.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_data(args.input, winsorize=args.winsorize)
    print(f"Loaded {len(df)} rows after cleaning.")

    metrics = predictive_metrics(df, nw_lags=args.nw_lags)
    qtest = quantile_test(df, q_low=args.q_low, q_high=args.q_high)
    strat = three_state_strategy(df, q_low=args.q_low, q_high=args.q_high)
    oos = train_test_split_strategy(df, split=args.split, q_low=args.q_low, q_high=args.q_high)

    print("Predictive metrics:", metrics)
    print("Quantile test:", qtest)
    print("Three-state strategy:", strat)
    print("Train/Test strategy:", oos)


if __name__ == "__main__":
    main()
