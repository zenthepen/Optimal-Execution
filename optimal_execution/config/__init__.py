"""
Configuration
=============

Default parameters and configuration settings.
"""

# Default parameters from literature (Almgren-Chriss, Curato et al.)
DEFAULT_PARAMS = {
    "eta": 3.5e-2,      # Impact coefficient (Curato et al. 2014)
    "gamma": 0.67,      # Power law exponent
    "lambda": 1e-6,     # Risk aversion parameter
    "sigma": 0.02,      # Volatility (2% daily)
    "N": 10,            # Number of trading periods
    "permanent_ratio": 0.4,  # 40% permanent, 60% transient
    "decay_rate": 7.92, # Exponential decay rate for transient impact
}

__all__ = ["DEFAULT_PARAMS"]
