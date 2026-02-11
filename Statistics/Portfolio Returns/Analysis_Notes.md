# Portfolio Analysis Notes

## How Returns Are Calculated in portfolio_backtest.py

This document explains the return calculations and annualization methods used in the portfolio backtest script.

---

### 1) **Total Return (Compounded)**

```python
total_return = (1 + returns).prod() - 1
```

**What this does:**
- Takes each daily return in the series
- Compounds them multiplicatively: (1 + r₁) × (1 + r₂) × (1 + r₃) × ... × (1 + rₙ)
- Subtracts 1 to get the total return over the entire period

**Example:**
- Day 1: +1% → 1.01
- Day 2: +0.5% → 1.005
- Day 3: -0.2% → 0.998
- Total: (1.01 × 1.005 × 0.998) - 1 = 1.01299 - 1 = **1.299% total return**

This is the **buy-and-hold return** over the entire 2024 period.

---

### 2) **Annualized Return (Geometric Mean)**

```python
n_days = len(returns)
annualized_return = (1 + total_return) ** (252 / n_days) - 1
```

**What this does:**
- Takes the total compounded return
- Scales it to a full year (252 trading days)
- Uses geometric compounding (not simple averaging)

**Formula in plain text:**
```
Annualized Return = (1 + Total Return)^(252 / N) - 1
```

Where:
- `Total Return` = compounded return over N days
- `N` = actual number of trading days in your sample
- `252` = standard trading days per year

**Example:**
- Total return over 180 days: 5% (0.05)
- Annualized: (1.05)^(252/180) - 1 = (1.05)^1.4 - 1 ≈ **7.14%**

**Why this method?**
- It accounts for compounding over time
- If your sample period is shorter than a year, it projects what the return would be if you maintained that performance for a full year
- If your sample period is longer than a year, it normalizes to annual terms

---

### 3) **Volatility (Annualized)**

```python
volatility = returns.std() * np.sqrt(252)
```

**What this does:**
- Calculates the standard deviation of **daily returns**
- Scales to annual terms by multiplying by √252

**Why √252?**
- Standard deviation scales with the square root of time (assuming i.i.d. returns)
- Daily vol × √252 ≈ annual vol

**Example:**
- Daily return std dev: 1.5%
- Annualized: 1.5% × √252 ≈ 1.5% × 15.87 ≈ **23.8% annual volatility**

---

### 4) **Sharpe Ratio**

```python
rf_daily = rf_annual / 252
excess_returns = returns - rf_daily
sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
```

**What this does:**
1. Converts annual risk-free rate to daily (simple division by 252)
2. Computes excess returns: `daily_return - rf_daily`
3. Calculates: (mean excess return) / (std dev of excess returns)
4. Annualizes by multiplying by √252

**Formula:**
```
Sharpe = (Mean Daily Excess Return / Std Dev of Excess Returns) × √252
```

**Example (with rf = 0%):**
- Mean daily return: 0.05%
- Std dev: 1.2%
- Sharpe = (0.05% / 1.2%) × √252 ≈ 0.042 × 15.87 ≈ **0.66**

---

## Summary Table

| Metric | Daily Calculation | Annualization Method |
|--------|------------------|---------------------|
| **Total Return** | Compound all daily returns | None (absolute return over period) |
| **Annualized Return** | From total return | Geometric: `(1 + total_ret)^(252/N) - 1` |
| **Volatility** | Std dev of daily returns | Square root of time: `daily_vol × √252` |
| **Sharpe Ratio** | Mean excess / std dev | Square root of time: `daily_sharpe × √252` |

---

## Important Implementation Notes

### 1. Trading Days Convention
The script uses **252 trading days per year** (standard convention for US markets).

### 2. Risk-Free Rate
Currently set to 0% in the script:
```python
RISK_FREE_RATE = 0.0
```
If you want to use actual 2024 rates (e.g., ~4-5%), update this constant at the top of `portfolio_backtest.py`.

### 3. Long-Short Return Calculation
The long-short return is calculated as the daily spread:
```python
daily_returns_wide['long_short'] = daily_returns_wide['long'] - daily_returns_wide['short']
```

This represents the return from being:
- **Long** the long portfolio (with 100% exposure)
- **Short** the short portfolio (with 100% exposure)

The result is a market-neutral strategy (dollar-neutral with 100/100 gross exposure).

### 4. Compounding Assumption
The annualized return formula assumes you **reinvest all gains daily** (geometric compounding), which is standard for portfolio performance reporting and reflects realistic portfolio dynamics.

---

## Additional Metrics Calculated

### 5) **Maximum Drawdown**

```python
cumulative = (1 + returns).cumprod()
running_max = cumulative.expanding().max()
drawdown = (cumulative - running_max) / running_max
max_drawdown = drawdown.min()
```

**What this does:**
- Computes the cumulative wealth over time
- Tracks the running maximum (peak wealth)
- Calculates the percentage decline from each peak
- Reports the largest (most negative) drawdown

**Interpretation:**
- Max drawdown of -15% means the portfolio lost 15% from its peak before recovering
- Important risk metric showing worst-case decline an investor would have experienced

### 6) **Turnover**

Calculated in the `calculate_turnover()` function:
- Measures how much the portfolio composition changes at each rebalance
- Formula: `Turnover = Σ|weight_change| / 2`
- Averaged across all rebalance periods
- Important for estimating transaction costs

**Example:**
- If 40% of portfolio is replaced at rebalance → 20% turnover per leg (40% / 2)
- Higher frequency strategies (weekly) typically have higher turnover than monthly

---

## Output Files

The script generates the following files in `results/Portfolio/`:

1. **portfolio_returns_{frequency}_{weighting}.csv**
   - Daily return series with columns: `return_date`, `long`, `short`, `long_short`
   - Can be used for plotting cumulative performance or further analysis

2. **portfolio_summary_{frequency}_{weighting}.csv**
   - Summary statistics for Long, Short, and Long-Short portfolios
   - Includes all metrics described above

3. **portfolio_comparison_all_configs.csv**
   - Cross-configuration comparison focusing on Long-Short performance
   - Useful for evaluating robustness across different frequencies and weighting schemes
