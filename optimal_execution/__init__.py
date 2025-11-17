"""
Optimal Execution Library
=========================

A production-ready library for institutional optimal execution strategies
using Differential Evolution global optimization.

Key Components:
    - solvers: Optimization algorithms (DE, SQP, DP, Hybrid)
    - models: Cost models (impact, spread, risk, transient)
    - calibration: Parameter calibration from market data
    - constraints: Trading constraints (liquidity, regulatory, risk)
    - utils: Utilities for validation, logging, plotting

Example:
    >>> from optimal_execution.solvers import DifferentialEvolutionSolver
    >>> solver = DifferentialEvolutionSolver(X0=100000, T=1.0, N=10)
    >>> result = solver.solve()
    >>> print(f"Total cost: ${result.total_cost:.2f}")
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__license__ = "MIT"

from optimal_execution.solvers.differential_evolution import OptimalExecutionRealistic

__all__ = ["OptimalExecutionRealistic", "__version__"]
