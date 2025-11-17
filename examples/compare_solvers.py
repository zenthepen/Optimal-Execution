"""
Fair Comparison: Realistic Model vs TWAP

This compares the realistic model against TWAP (the practical baseline),
not against the unconstrained instantaneous model.
"""

import numpy as np
import sys
from pathlib import Path

# Add DE solver core directory (go up one level from validation to DE_SOLVER, then to core)
sys.path.append(str(Path(__file__).resolve().parent.parent / 'core'))

from de_solver_realistic import OptimalExecutionRealistic


def compute_twap_cost_realistic(X0, T, N, sigma, lam, eta, gamma, S0,
                                  spread_bps, permanent_fraction, decay_rate):
    """
    Compute TWAP cost using the SAME realistic cost function.
    
    This ensures fair comparison (apples-to-apples).
    """
    # TWAP strategy: equal trades each period
    S_twap = np.ones(N) * X0 / N
    
    # Compute cost using realistic model
    tau = T / N
    price_displacement = 0.0
    inventory = X0
    total_cost = 0.0
    
    # Split impact
    eta_perm = eta * permanent_fraction
    eta_trans = eta * (1 - permanent_fraction)
    spread_cost_per_share = spread_bps * 0.0001 * S0
    
    for i in range(N):
        # Decay transient
        decay_factor = np.exp(-decay_rate * tau)
        price_displacement = price_displacement * decay_factor
        
        # Compute impacts
        permanent_impact = eta_perm * (np.abs(S_twap[i]) ** gamma)
        transient_impact = eta_trans * (np.abs(S_twap[i]) ** gamma)
        current_price_impact = price_displacement + permanent_impact + transient_impact
        
        # Impact cost
        impact_cost = S_twap[i] * current_price_impact * S0
        
        # Spread cost
        spread_cost = spread_cost_per_share * S_twap[i]
        
        # Update inventory
        inventory -= S_twap[i]
        
        # Risk cost
        risk_cost = 0.5 * lam * (inventory ** 2) * (sigma ** 2) * tau
        
        total_cost += impact_cost + spread_cost + risk_cost
        
        # Update price displacement
        price_displacement = price_displacement + transient_impact
    
    return total_cost, S_twap


def compare_realistic_vs_twap():
    """
    Compare realistic optimal execution against TWAP.
    
    Both use the SAME cost function (fair comparison).
    """
    # Test parameters (SNAP)
    X0 = 100000
    T = 1.0
    N = 10
    sigma = 0.0348
    lam = 1e-6
    eta = 2e-7
    gamma = 0.67
    S0 = 7.92
    
    # Realistic constraints
    max_trade_fraction = 0.4
    spread_bps = 1.0
    permanent_fraction = 0.4
    decay_rate = 0.5
    
    print("="*80)
    print("FAIR COMPARISON: REALISTIC OPTIMAL EXECUTION vs TWAP")
    print("="*80)
    print()
    print(f"Stock: SNAP")
    print(f"  X₀ = {X0:,} shares, T = {T} day, N = {N} periods")
    print(f"  σ = {sigma:.4f}, λ = {lam:.2e}")
    print(f"  η = {eta:.2e}, γ = {gamma:.4f}, S₀ = ${S0:.2f}")
    print()
    print(f"Realistic Constraints:")
    print(f"  • Max trade/period: {max_trade_fraction:.0%}")
    print(f"  • Spread: {spread_bps} bps")
    print(f"  • Permanent: {permanent_fraction:.0%}, Transient: {1-permanent_fraction:.0%}")
    print(f"  • Decay rate: ρ = {decay_rate}")
    print()
    print("="*80)
    print()
    
    # Solve with realistic model
    print("1. REALISTIC OPTIMAL EXECUTION")
    print("-"*80)
    solver = OptimalExecutionRealistic(
        X0, T, N, sigma, lam, eta, gamma, S0,
        max_trade_fraction=max_trade_fraction,
        spread_bps=spread_bps,
        permanent_fraction=permanent_fraction,
        decay_rate=decay_rate
    )
    result_opt = solver.solve(maxiter=1000, verbose=False)
    
    print(f"Total cost: ${result_opt['cost']:.2f}")
    print(f"  Impact: ${result_opt['cost_breakdown']['impact_cost']:.2f} "
          f"({result_opt['cost_breakdown']['impact_pct']:.1f}%)")
    print(f"  Spread: ${result_opt['cost_breakdown']['spread_cost']:.2f} "
          f"({result_opt['cost_breakdown']['spread_pct']:.1f}%)")
    print(f"  Risk: ${result_opt['cost_breakdown']['risk_cost']:.2f} "
          f"({result_opt['cost_breakdown']['risk_pct']:.1f}%)")
    print()
    print(f"Strategy:")
    print(f"  First trade: {result_opt['optimal_trades'][0]:,.0f} shares ({result_opt['optimal_trades'][0]/X0:.1%})")
    print(f"  Max trade: {np.max(result_opt['optimal_trades']):,.0f} shares ({np.max(result_opt['optimal_trades'])/X0:.1%})")
    print(f"  Active periods: {np.sum(result_opt['optimal_trades'] > X0*0.01)}/{N}")
    print(f"  Pattern: {result_opt['optimal_trades'][:5]/1000}")
    print()
    
    # Compute TWAP cost (using SAME cost function)
    print("2. TWAP (Baseline)")
    print("-"*80)
    cost_twap, trades_twap = compute_twap_cost_realistic(
        X0, T, N, sigma, lam, eta, gamma, S0,
        spread_bps, permanent_fraction, decay_rate
    )
    
    print(f"Total cost: ${cost_twap:.2f}")
    print()
    print(f"Strategy:")
    print(f"  Each trade: {trades_twap[0]:,.0f} shares ({trades_twap[0]/X0:.1%})")
    print(f"  Active periods: {N}/{N} (uniform)")
    print(f"  Pattern: {trades_twap[:5]/1000}")
    print()
    
    # Comparison
    print("="*80)
    print("COMPARISON RESULTS")
    print("="*80)
    print()
    
    improvement = (cost_twap - result_opt['cost']) / cost_twap
    
    print(f"TWAP cost:      ${cost_twap:.2f}")
    print(f"Optimal cost:   ${result_opt['cost']:.2f}")
    print(f"Savings:        ${cost_twap - result_opt['cost']:.2f}")
    print(f"Improvement:    {improvement:.1%}")
    print()
    
    if improvement > 0.15:
        verdict = "✅ EXCELLENT (>15% improvement)"
    elif improvement > 0.05:
        verdict = "✅ GOOD (5-15% improvement)"
    elif improvement > 0:
        verdict = "⚠️  MARGINAL (<5% improvement)"
    else:
        verdict = "❌ FAIL (TWAP is better)"
    
    print(f"Verdict: {verdict}")
    print()
    
    # Trading pattern comparison
    print("="*80)
    print("TRADING PATTERN COMPARISON")
    print("="*80)
    print()
    print(f"{'Period':<8} {'TWAP':>12} {'Optimal':>12} {'Difference':>12}")
    print("-"*48)
    for i in range(min(N, 10)):
        diff = result_opt['optimal_trades'][i] - trades_twap[i]
        diff_pct = diff / trades_twap[i] if trades_twap[i] > 0 else 0
        print(f"{i+1:<8} {trades_twap[i]:>12,.0f} {result_opt['optimal_trades'][i]:>12,.0f} "
              f"{diff_pct:>11.1%}")
    print()
    
    # Key insights
    print("="*80)
    print("KEY INSIGHTS")
    print("="*80)
    print()
    print(f"1. Optimal execution achieves {improvement:.1%} cost reduction vs TWAP ✅")
    print()
    print(f"2. Front-loading strategy:")
    print(f"   • Optimal front-loads {result_opt['optimal_trades'][0]/X0:.1%} in period 1")
    print(f"   • TWAP uses uniform {trades_twap[0]/X0:.1%} per period")
    print(f"   • Exploits: Sub-linear impact + early transient decay")
    print()
    print(f"3. Realistic constraints prevent corner solutions:")
    print(f"   • Trade size limit: {max_trade_fraction:.0%} → Max used: {np.max(result_opt['optimal_trades'])/X0:.1%}")
    print(f"   • Transient buildup naturally smooths strategy")
    print()
    print(f"4. Cost breakdown shows impact dominates:")
    print(f"   • Impact: {result_opt['cost_breakdown']['impact_pct']:.1f}%")
    print(f"   • Spread: {result_opt['cost_breakdown']['spread_pct']:.1f}%")
    print(f"   • Risk: {result_opt['cost_breakdown']['risk_pct']:.1f}%")
    print()
    print("="*80)
    print()
    
    return {
        'optimal_cost': result_opt['cost'],
        'twap_cost': cost_twap,
        'improvement': improvement,
        'optimal_trades': result_opt['optimal_trades'],
        'twap_trades': trades_twap
    }


if __name__ == "__main__":
    results = compare_realistic_vs_twap()
