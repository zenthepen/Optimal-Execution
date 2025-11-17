# Visualization Results

Publication-quality figures from Monte Carlo simulations and analysis.

## Available Figures

### 1. Monte Carlo Cost Distributions
**File:** `monte_carlo_cost_distributions.png`

Histograms showing cost distributions across 50 Monte Carlo scenarios for 5 stocks (AAPL, NVDA, PLTR, OPEN, TOUR). Demonstrates robustness and consistency of the optimal execution strategy.

### 2. Liquidity Impact Dashboard
**File:** `liquidity_impact_dashboard.png`

Comprehensive 4-panel dashboard showing:
- Cost distributions per stock
- Liquidity spectrum (ADV comparison)
- Cost vs liquidity scatter plot
- Trading trajectory comparison

### 3. Trading Trajectories - Optimal vs TWAP
**File:** `trading_trajectories_optimal_vs_twap.png`

Comparison of execution paths showing how the optimal strategy front-loads trades compared to TWAP baseline.

### 4. Robustness Violin Plots
**File:** `robustness_violin_plots.png`

Violin plots with coefficient of variation showing cost predictability across different liquidity tiers.

### 5. Liquidity Spectrum (5 Stocks)
**File:** `liquidity_spectrum_5stocks.png`

Bar chart comparing Average Daily Volume (ADV) across the 5 test stocks.

### 6. Cost vs Liquidity Scatter
**File:** `cost_vs_liquidity_scatter.png`

Scatter plot demonstrating the relationship between stock liquidity and execution cost variance.

### 7. Adaptive Constraints Comparison
**File:** `adaptive_constraints_comparison.png`

Comparison of adaptive liquidity-based constraints vs fixed constraints.

### 8. Trade Size Adaptation by Liquidity
**File:** `trade_size_adaptation_by_liquidity.png`

Shows how maximum trade size constraints adapt based on liquidity tier (10%, 20%, 30% of ADV).

---

## Usage in Papers/Presentations

All figures are **300 DPI** publication quality and can be directly included in:
- Academic papers
- Thesis documents
- Conference presentations
- Portfolio showcases

## Figure Specifications

- Format: PNG
- Resolution: 300 DPI
- Size: ~130KB - 730KB per figure
- Total: 8 figures

---

## Regenerating Figures

To regenerate these figures from scratch:

```bash
cd examples
python monte_carlo_simulation.py
```

The script will output updated versions of all visualizations to `docs/images/results/`.
