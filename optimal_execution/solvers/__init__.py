"""
Optimization Solvers
====================

This module contains optimization algorithms for optimal execution:
    - DifferentialEvolutionSolver: Global optimization (main solver)
    - SQPSolver: Local optimization using Sequential Quadratic Programming
    - DynamicProgrammingSolver: Bellman equation solver
    - HybridSolver: DE + SQP hybrid approach
"""

from optimal_execution.solvers.differential_evolution import OptimalExecutionRealistic

__all__ = ["OptimalExecutionRealistic"]
