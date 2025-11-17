"""
Quickstart Example
==================

Basic usage of the Optimal Execution library.

This example shows how to:
1. Initialize the solver with realistic parameters
2. Solve for optimal execution strategy
3. Compare against TWAP baseline
4. Visualize the results
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from optimal_execution.solvers.differential_evolution import OptimalExecutionRealistic


def main():
    """Run a basic optimal execution example"""
    
    print("=" * 60)
    print("Optimal Execution - Quickstart Example")
    print("=" * 60)
    print()
    
    # Initialize solver with SNAP stock parameters
    # These are calibrated from real market data
    print("Initializing solver with SNAP parameters...")
    solver = OptimalExecutionRealistic(
        X0=100000,              # Order size: 100,000 shares
        T=1.0,                  # Time horizon: 1 day
        N=10,                   # 10 trading periods
        eta=0.035,              # Impact coefficient (calibrated)
        lam=1e-6,               # Risk aversion
        sigma=0.02,             # Volatility (2% daily)
        gamma=0.67,             # Power law exponent
        S0=10.0,                # Initial stock price: $10
        permanent_ratio=0.4,    # 40% permanent, 60% transient
        decay_rate=7.92,        # Transient decay rate
        max_trade_pct=0.20      # Max 20% of inventory per period
    )
    
    print("Solving for optimal execution strategy...")
    result = solver.solve()
    
    # Display results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"\n✅ Optimization Status: {result['status']}")
    print(f"   Iterations: {result['iterations']}")
    print(f"   Function Evaluations: {result['function_evals']}")
    
    print(f"\n💰 Total Cost: ${result['total_cost']:.2f}")
    print(f"   - Impact Cost: ${result['impact_cost']:.2f} ({result['impact_cost']/result['total_cost']*100:.1f}%)")
    print(f"   - Spread Cost: ${result['spread_cost']:.2f} ({result['spread_cost']/result['total_cost']*100:.1f}%)")
    print(f"   - Risk Cost: ${result['risk_cost']:.2f} ({result['risk_cost']/result['total_cost']*100:.1f}%)")
    
    print(f"\n📊 Improvement vs TWAP: {result['improvement_vs_twap']:.2f}%")
    
    print("\n📈 Optimal Execution Schedule:")
    print("   Period | Shares to Trade | % of Total | Remaining")
    print("   " + "-" * 55)
    remaining = 100000
    for i, shares in enumerate(result['optimal_strategy'], 1):
        pct = (shares / 100000) * 100
        print(f"   {i:6d} | {shares:15,.0f} | {pct:10.2f}% | {remaining:9,.0f}")
        remaining -= shares
    
    print("\n" + "=" * 60)
    print("Key Insights:")
    print("=" * 60)
    print("• Front-loading: Trade more aggressively early to reduce risk")
    print("• Gradual reduction: Taper off trades as inventory decreases")
    print("• Constraint-aware: Respects liquidity limits (20% max per period)")
    print("• Cost-optimal: Balances impact, spread, and risk costs")
    print()
    
    return result


if __name__ == "__main__":
    result = main()
    print("✅ Quickstart complete! See examples/ for more advanced usage.")
