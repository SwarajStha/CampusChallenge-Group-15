# Walkthrough / Q&A Notes

This file captures explanations (with readable formulas) for questions that come up during the project.

---

## Q1 — In Phase B (Portfolio backtests), what does it mean to “compute daily return series for Long / Short / Long-Short”?

It means you should produce **three time series (one value per trading day in 2024)** that represent how each “leg” of the strategy performed while you hold the chosen weights between rebalances.

### 1) What the three daily return series are

Assume on each rebalance date you pick a set of stocks for **Long** and **Short** and assign weights that stay fixed until the next rebalance.

#### Long portfolio daily returns

For each trading day \(d\) in the holding window:

$$
 r^{\text{Long}}_{d} = \sum_{i \in \text{Long}} w^{\text{Long}}_{i} \cdot r_{i,d}
$$

Where:
- \(r_{i,d}\) = daily return of stock \(i\) on day \(d\)
- \(w^{\text{Long}}_{i}\) = portfolio weight of stock \(i\) in the long leg (e.g., equal-weight)

Plain-text version:

```
r_Long[d] = sum over i in Long: w_Long[i] * r[i,d]
```

#### Short portfolio daily returns

$$
 r^{\text{Short}}_{d} = \sum_{i \in \text{Short}} w^{\text{Short}}_{i} \cdot r_{i,d}
$$

This is the **return of the short-side basket** (as if you held a portfolio of those stocks).

Note on conventions:
- Some people report “short leg contribution” as \(-r^{\text{Short}}_{d}\).
- Either convention is fine as long as you’re consistent and clearly label it.

Plain-text version:

```
r_Short[d] = sum over i in Short: w_Short[i] * r[i,d]
```

#### Long–Short daily returns

The **market-neutral spread** each day:

$$
 r^{\text{LS}}_{d} = r^{\text{Long}}_{d} - r^{\text{Short}}_{d}
$$

Interpretation: you’re long the long basket and short the short basket with equal gross exposure (commonly 100/100).

Plain-text version:

```
r_LS[d] = r_Long[d] - r_Short[d]
```

### 2) Why you want daily series even for weekly/monthly rebalancing

Even if you rebalance **weekly** or **monthly**, you still typically:
- set weights at rebalance,
- **hold them constant**, and
- compute the strategy’s **day-by-day** realized performance during that holding period.

This gives you:
- full-year cumulative return (by compounding daily \(r_d\))
- annualized volatility/Sharpe computed from daily returns
- drawdowns and plots

If instead you only compute one return per week/month, you can still do it—but then your Sharpe/volatility will be based on weekly/monthly data (fewer observations).

### 3) Tiny example (to make the sign clear)

If on a given day:
- Long basket returns \(+0.40\%\)
- Short basket returns \(+0.10\%\)

Then:

$$
 r^{\text{LS}} = 0.40\% - 0.10\% = +0.30\%
$$

If the short basket rises a lot (bad for a short position), \(r^{\text{LS}}\) becomes negative automatically via the subtraction.
