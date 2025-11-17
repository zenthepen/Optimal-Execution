"""
Parameter Calibration
====================

Tools for calibrating model parameters from market data:
    - impact_calibrator: Zarinelli regression for η and γ
    - liquidity_calibrator: ADV-based liquidity classification
    - data_fetcher: Yahoo Finance data retrieval
"""

from optimal_execution.calibration.liquidity_calibrator import LiquidityCalibrator

__all__ = ["LiquidityCalibrator"]
