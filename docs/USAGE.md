# Usage Guide

Complete guide to using the Optimal Execution library.

---

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Basic Usage](#basic-usage)
4. [Advanced Features](#advanced-features)
5. [Calibration](#calibration)
6. [Troubleshooting](#troubleshooting)

---

## Installation

### From Source

```bash
git clone https://github.com/yourusername/optimal-execution-de.git
cd optimal-execution-de
pip install -e .
```

### Requirements

- Python 3.10+
- NumPy < 2.0
- SciPy >= 1.11.0
- See `requirements.txt` for complete list

---

## Quick Start

### Basic Example

```python
from optimal_execution.solvers import OptimalExecutionRealistic

# Create solver
solver = OptimalExecutionRealistic(
    X0=100000,      # 100k shares to liquidate
    T=1.0,          # 1 day
    N=10,           # 10 periods
    eta=0.035,      # Impact coefficient
    sigma=0.02,     # Volatility
    S0=10.0         # Initial price
)

# Solve
result = solver.solve()

# Display results
print(f"Total cost: ${result['total_cost']:.2f}")
print(f"Improvement: {result['improvement_vs_twap']:.2f}%")
```

**Expected output:**
```
Total cost: $309.54
Improvement: 5.7%
```

---

## Basic Usage

### Understanding Parameters

#### Required Parameters

- **X0** (int): Order size in shares  
  *Example:* 100,000 shares

- **T** (float): Time horizon in days  
  *Example:* 1.0 (one trading day)

- **N** (int): Number of trading periods  
  *Example:* 10 (divide day into 10 chunks)

- **eta** (float): Market impact coefficient  
  *Range:* 0.01 - 0.1  
  *Default:* 0.035 (calibrated)

- **sigma** (float): Daily volatility  
  *Range:* 0.01 - 0.05  
  *Example:* 0.02 (2% daily)

- **S0** (float): Initial stock price  
  *Example:* 10.0 ($10 per share)

#### Optional Parameters

- **gamma** (float): Power law exponent  
  *Default:* 0.67  
  *Range:* 0.5 - 0.8

- **lam** (float): Risk aversion  
  *Default:* 1e-6  
  *Range:* 1e-7 - 1e-4

- **permanent_ratio** (float): Permanent impact %  
  *Default:* 0.4 (40% permanent, 60% transient)

- **decay_rate** (float): Transient decay rate  
  *Default:* 7.92

- **max_trade_pct** (float): Max % per period  
  *Default:* 0.20 (20%)

### Interpreting Results

```python
result = solver.solve()
```

**Result dictionary:**
```python
{
    'optimal_strategy': [15432, 12845, ...],  # Shares per period
    'total_cost': 309.54,                     # Total cost ($)
    'impact_cost': 148.61,                    # Impact component
    'spread_cost': 157.50,                    # Spread component
    'risk_cost': 3.43,                        # Risk component
    'improvement_vs_twap': 5.7,               # % vs TWAP
    'status': 'success',                      # Optimization status
    'iterations': 28,                         # DE iterations
    'function_evals': 4200                    # Cost evaluations
}
```

---

## Advanced Features

### Custom Constraints

```python
# Aggressive liquidity constraint
solver = OptimalExecutionRealistic(
    X0=100000,
    T=1.0,
    N=10,
    max_trade_pct=0.15,  # Max 15% per period (tighter)
    eta=0.035,
    sigma=0.02,
    S0=10.0
)
```

### High Risk Aversion

```python
# More aggressive front-loading
solver = OptimalExecutionRealistic(
    X0=100000,
    T=1.0,
    N=10,
    lam=1e-4,  # Higher risk aversion (100x default)
    eta=0.035,
    sigma=0.02,
    S0=10.0
)
```

### Long Time Horizon

```python
# Multi-day execution
solver = OptimalExecutionRealistic(
    X0=1000000,  # 1M shares
    T=5.0,       # 5 days
    N=50,        # 50 periods (10 per day)
    eta=0.025,
    sigma=0.02,
    S0=50.0
)
```

---

## Calibration

### Automatic Calibration from Market Data

```python
from optimal_execution.calibration import LiquidityCalibrator

# Initialize calibrator
calibrator = LiquidityCalibrator()

# Fetch and calibrate for a stock
params = calibrator.calibrate_from_ticker(
    ticker="AAPL",
    period="1y"  # 1 year of historical data
)

# Use calibrated parameters
solver = OptimalExecutionRealistic(**params)
result = solver.solve()
```

### Using Pre-Calibrated Parameters

```python
import json

# Load calibrated parameters
with open("data/calibration/calibration_AAPL.json", "r") as f:
    params = json.load(f)

# Create solver with calibrated params
solver = OptimalExecutionRealistic(
    X0=100000,
    T=1.0,
    N=10,
    eta=params["eta"],
    gamma=params["gamma"],
    sigma=params["sigma"],
    S0=params["current_price"]
)
```

### Calibration Files

Pre-calibrated parameters available for:
- **AAPL** (Apple Inc.)
- **MSFT** (Microsoft)
- **NVDA** (NVIDIA)
- **SNAP** (Snap Inc.)
- **SPY** (S&P 500 ETF)

Located in: `data/calibration/`

---

## Troubleshooting

### Common Issues

#### 1. Import Error

**Problem:**
```
ModuleNotFoundError: No module named 'optimal_execution'
```

**Solution:**
```bash
# Install in editable mode
pip install -e .
```

#### 2. NumPy Version Conflict

**Problem:**
```
RuntimeError: module compiled against API version 0x10
```

**Solution:**
```bash
pip install "numpy<2.0.0" --force-reinstall
```

#### 3. Optimization Failure

**Problem:**
```
{'status': 'failed', 'message': 'Constraints violated'}
```

**Solution:**
- Increase `max_trade_pct` (e.g., 0.25 instead of 0.20)
- Reduce `N` (fewer periods = easier constraints)
- Check `X0` is reasonable relative to stock liquidity

#### 4. Unrealistic Costs

**Problem:**
Total cost seems too high or too low.

**Solution:**
- Verify parameters are calibrated (use `LiquidityCalibrator`)
- Check `eta` is in range [0.01, 0.1]
- Check `sigma` matches historical volatility
- Ensure `S0` (price) is current

---

## Examples

### 1. Small Order (Safe)

```python
solver = OptimalExecutionRealistic(
    X0=10000,       # Small order
    T=0.5,          # Half day
    N=5,            # 5 periods
    eta=0.020,      # Low impact (liquid stock)
    sigma=0.015,    # Low volatility
    S0=100.0        # High price stock
)
```

### 2. Large Order (Aggressive)

```python
solver = OptimalExecutionRealistic(
    X0=500000,      # Large order
    T=3.0,          # 3 days
    N=30,           # 30 periods
    eta=0.050,      # High impact (illiquid)
    sigma=0.03,     # Higher volatility
    S0=5.0,         # Low price stock
    lam=1e-5        # Higher risk aversion
)
```

### 3. Urgent Liquidation

```python
solver = OptimalExecutionRealistic(
    X0=100000,
    T=0.25,         # Quarter day (urgent!)
    N=4,            # Only 4 periods
    lam=1e-3,       # Very high risk aversion
    max_trade_pct=0.30,  # Allow 30% per period
    eta=0.035,
    sigma=0.02,
    S0=10.0
)
```

---

## Best Practices

### 1. Always Calibrate

Don't use hardcoded parameters. Use calibration:
```python
calibrator = LiquidityCalibrator()
params = calibrator.calibrate_from_ticker("AAPL")
```

### 2. Validate Results

Check that:
- Total cost is reasonable (0.1% - 5% of notional)
- Improvement vs TWAP is realistic (3% - 10%)
- Strategy respects constraints (sum = X0)

### 3. Test Sensitivity

Run with ±20% parameter variations:
```python
for eta_mult in [0.8, 1.0, 1.2]:
    solver = OptimalExecutionRealistic(
        X0=100000,
        eta=0.035 * eta_mult,
        # ... other params
    )
    result = solver.solve()
    print(f"eta={0.035*eta_mult:.4f}: cost=${result['total_cost']:.2f}")
```

### 4. Use Appropriate N

- **N = 5-10**: Short horizon (< 1 day)
- **N = 10-20**: Single day
- **N = 20-50**: Multi-day (2-5 days)

---

## Next Steps

- 📖 Read [Theory](THEORY.md) for mathematical background
- 🔬 Run [Monte Carlo](../examples/monte_carlo_simulation.py) for statistical validation
- 🧪 Check [API Reference](API.md) for complete function documentation

---

**Questions?** Open an issue on [GitHub](https://github.com/yourusername/optimal-execution-de/issues)
