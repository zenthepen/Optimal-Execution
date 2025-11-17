"""Pytest configuration and fixtures"""

import pytest
import numpy as np


@pytest.fixture
def solver_params():
    """Standard solver parameters for testing"""
    return {
        "X0": 100000,
        "T": 1.0,
        "N": 10,
        "eta": 0.035,
        "lam": 1e-6,
        "sigma": 0.02,
        "gamma": 0.67,
        "S0": 10.0,
    }


@pytest.fixture
def seed():
    """Fixed random seed for reproducibility"""
    np.random.seed(42)
    return 42
