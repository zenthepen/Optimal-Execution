"""Setup script for optimal-execution-de package"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="optimal-execution-de",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Optimal execution strategies using Differential Evolution",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/optimal-execution-de",
    packages=find_packages(exclude=["tests*", "docs*", "examples*", "notebooks*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "numpy<2.0.0",
        "scipy>=1.11.0",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0",
        "pandas>=2.0.0",
        "yfinance>=0.2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    include_package_data=True,
    package_data={
        "optimal_execution": ["data/calibration/*.json"],
    },
)
