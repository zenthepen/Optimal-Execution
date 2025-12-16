# Limitations and Assumptions

## Model Assumptions

**Deterministic Execution:**
We assume orders execute at expected prices without additional random slippage. In practice, order execution involves:
- Bid-ask bounce
- Queue position uncertainty
- Hidden liquidity discovery

**Impact:** Results represent expected costs; realized costs may vary by ±2-5%.

**Price Independence:**
Market impact is modeled as a function of trade size only, ignoring:
- Order book state
- Market maker inventory
- Contemporaneous order flow

**Impact:** Power-law model may overestimate impact for very large orders (>10% ADV).

**No Transaction Costs:**
We exclude:
- Broker commissions ($0.001-0.005 per share)
- Exchange fees ($0.0003-0.0005 per share)
- SEC regulatory fees ($0.0000278 per dollar)

**Impact:** Total costs underestimated by ~$50-200 for 100k share order. However, transaction costs are constant across strategies, so relative comparison (optimal vs TWAP) remains valid.

**Single Asset:**
Multi-asset portfolios with correlations and cross-impact are not considered.

**Impact:** Methodology extends naturally to portfolio case with additional complexity.

### 8.2 Computational Limitations

**Grid Resolution (DP):**
With $M = 150$ inventory points and $K = 80$ control points, the discretization introduces quantization errors of order $\mathcal{O}(X_0 / M) \approx 667$ shares.

**Impact:** Solutions may be suboptimal by 1-3% due to discretization artifacts.

**Local Convergence (SQP):**
Gradient-based methods guarantee convergence only to local optima. Global convergence requires:
- Convex objective (not satisfied for power-law impact)
- Initial guess in basin of attraction (unknown a priori)

**Impact:** SQP results are initial-guess dependent.

**Stochastic Variance (DE):**
Evolutionary algorithms have inherent randomness. Solution quality varies across runs (standard deviation ~0.5% of optimal cost).

**Impact:** Multiple runs recommended (we use 3 runs, report best).

### Data Limitations

**Historical Calibration:**
Parameters estimated from past data may not reflect future market conditions:
- Volatility regime changes
- Liquidity evolution (ADV trends)
- Market structure shifts (e.g., decimalization, dark pools)

**Impact:** Recalibration recommended quarterly or after major market events.

**ADV Estimation Window:**
30-day rolling average may not capture:
- Seasonal patterns (earnings seasons)
- Corporate actions (splits, buybacks)
- Macroeconomic shocks (COVID-19, rate decisions)

**Impact:** Constraint violations possible in abnormal market conditions.

**Survivorship Bias:**
Analysis focuses on continuously traded stocks. Delisted or bankrupt firms excluded.

**Impact:** Results may not generalize to distressed securities.

