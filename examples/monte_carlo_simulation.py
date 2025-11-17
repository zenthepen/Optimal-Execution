"""
COMPREHENSIVE MONTE CARLO SIMULATION WITH ADAPTIVE CONSTRAINTS

5-Stock Liquidity Spectrum Analysis:
- AAPL: Mega-cap (ultra-liquid ~50M ADV)
- NVDA: Large-cap (very liquid ~170M ADV)
- PLTR: Mid-cap (moderate liquidity)
- OPEN: Small-cap (lower liquidity)
- TOUR: Micro-cap (low liquidity ~2M ADV)

Features:
- Adaptive liquidity-based constraints
- Full DE solver with realistic market impact
- 10 Monte Carlo scenarios per stock
- Comprehensive visualization suite
- Statistical analysis and comparison
"""

import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime
import time
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats
from multiprocessing import Pool, cpu_count
import warnings
warnings.filterwarnings('ignore')  # Suppress warnings in parallel processes

# Add paths
sys.path.append(str(Path(__file__).parent.parent.parent / '00_SHARED'))
sys.path.append(str(Path(__file__).parent.parent))

from liquidity_calibrator import LiquidityCalibrator
from de_solver_adaptive import solve_with_adaptive_constraints


# Global wrapper for multiprocessing (must be picklable)
def _run_scenario_wrapper(args):
    """Wrapper to make run_single_scenario picklable for multiprocessing."""
    ticker, params, scenario_id, order_size, liq_info = args
    
    try:
        # Set unique seed for this scenario
        np.random.seed(scenario_id * 1000 + hash(ticker) % 1000)
        
        # Add Monte Carlo variation to parameters (±10% variation)
        sigma_varied = params['sigma'] * np.random.uniform(0.9, 1.1)
        eta_varied = params['eta'] * np.random.uniform(0.9, 1.1)
        S0_varied = params['S0'] * np.random.uniform(0.99, 1.01)  # ±1% price variation
        
        # Determine max_trade_fraction
        if liq_info is not None:
            use_adaptive = False
            manual_max_trade_fraction = liq_info['max_trade_fraction']
        else:
            use_adaptive = False
            manual_max_trade_fraction = 0.4  # Default fallback
        
        # Run the solver with adaptive constraints and varied parameters
        result = solve_with_adaptive_constraints(
            ticker=ticker,
            order_size=order_size,
            use_adaptive=use_adaptive,
            manual_max_trade_fraction=manual_max_trade_fraction,
            T=1.0,
            N=10,
            sigma=sigma_varied,
            lam=1e-6,
            eta=eta_varied,
            gamma=params['gamma'],  # Keep gamma constant (structural parameter)
            S0=S0_varied,
            seed=scenario_id,  # Pass seed for reproducibility
            verbose=False
        )
        
        return {
            'scenario_id': scenario_id,
            'ticker': ticker,
            'total_cost': result['cost'],  # DE solver returns 'cost' not 'total_cost'
            'solve_time': result['solve_time'],
            'success': True,
            'trades': result['optimal_trades'].tolist(),
            'cost_breakdown': result['cost_breakdown']
        }
    
    except Exception as e:
        return {
            'scenario_id': scenario_id,
            'ticker': ticker,
            'success': False,
            'error': str(e)
        }


class ComprehensiveMonteCarloSimulation:
    """
    Monte Carlo simulation with adaptive constraints across liquidity spectrum.
    """
    
    def __init__(self, 
                 tickers: list,
                 n_scenarios: int = 10,
                 order_size: float = 100000,
                 conservative_mode: bool = True):
        """
        Initialize simulation.
        
        Parameters
        ----------
        tickers : list
            Stock tickers to simulate
        n_scenarios : int
            Number of Monte Carlo scenarios per stock
        order_size : float
            Order size (shares) for all stocks
        conservative_mode : bool
            Use conservative liquidity constraints
        """
        self.tickers = tickers
        self.n_scenarios = n_scenarios
        self.order_size = order_size
        self.conservative_mode = conservative_mode
        
        # Results storage
        self.results = {}
        self.liquidity_info = {}
        self.all_scenarios = []
        
        # Paths
        self.calib_dir = Path(__file__).parent.parent.parent / '05_calibrated_data'
        self.output_dir = Path(__file__).parent.parent.parent / '06_results' / 'ADAPTIVE_MC_SIMULATION'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*80}")
        print(f"COMPREHENSIVE MONTE CARLO SIMULATION")
        print(f"{'='*80}")
        print(f"Stocks: {', '.join(tickers)}")
        print(f"Scenarios per stock: {n_scenarios}")
        print(f"Order size: {order_size:,.0f} shares")
        print(f"Constraint mode: {'Conservative' if conservative_mode else 'Aggressive'}")
        print(f"CPU cores: {cpu_count()} total, using {max(1, cpu_count()-1)} for parallel execution")
        print(f"{'='*80}\n")
    
    def load_calibration(self, ticker: str) -> dict:
        """Load calibrated parameters for a ticker."""
        calib_file = self.calib_dir / f'impact_calibration_{ticker}.json'
        
        if not calib_file.exists():
            raise FileNotFoundError(f"Calibration file not found: {calib_file}")
        
        with open(calib_file, 'r') as f:
            params = json.load(f)
        
        # Handle different param formats
        if 'sigma' not in params and 'std_return' in params:
            params['sigma'] = params['std_return']
        
        return params
    
    def calibrate_liquidity(self, ticker: str) -> dict:
        """Calibrate liquidity-based constraints for a ticker."""
        calibrator = LiquidityCalibrator(
            lookback_days=30,
            conservative_mode=self.conservative_mode
        )
        
        return calibrator.get_max_trade_fraction(
            ticker=ticker,
            order_size=self.order_size,
            verbose=True
        )
    
    def run_single_scenario(self, 
                           ticker: str, 
                           params: dict,
                           scenario_id: int) -> dict:
        """Run a single Monte Carlo scenario."""
        
        # Solve with adaptive constraints
        result = solve_with_adaptive_constraints(
            ticker=ticker,
            order_size=self.order_size,
            T=1.0,
            N=10,
            sigma=params['sigma'],
            lam=1e-6,
            eta=params['eta'],
            gamma=params['gamma'],
            S0=params['S0'],
            use_adaptive=True,
            conservative_mode=self.conservative_mode,
            verbose=False  # Silent for Monte Carlo
        )
        
        # Add scenario metadata
        result['scenario_id'] = scenario_id
        result['ticker'] = ticker
        result['order_size'] = self.order_size
        
        return result
    
    def run_stock(self, ticker: str):
        """Run all scenarios for a single stock."""
        
        print(f"\n{'='*80}")
        print(f"STOCK: {ticker}")
        print(f"{'='*80}\n")
        
        start_time = time.time()
        
        # Load parameters
        try:
            params = self.load_calibration(ticker)
            print(f"✅ Loaded calibration:")
            print(f"   η = {params['eta']:.2e}")
            print(f"   γ = {params['gamma']:.4f}")
            print(f"   σ = {params['sigma']:.4f}")
            print(f"   S₀ = ${params['S0']:.2f}\n")
        except FileNotFoundError as e:
            print(f"❌ {e}")
            print(f"   Skipping {ticker}\n")
            return None
        
        # Calibrate liquidity
        try:
            liq_info = self.calibrate_liquidity(ticker)
            self.liquidity_info[ticker] = liq_info
        except Exception as e:
            print(f"⚠️  Liquidity calibration failed: {e}")
            print(f"   Using default 40% constraint\n")
            liq_info = None
        
        # Run scenarios in parallel
        stock_results = []
        
        print(f"Running {self.n_scenarios} Monte Carlo scenarios in parallel...")
        print(f"-"*80)
        
        # Prepare arguments for parallel execution
        args_list = [
            (ticker, params, i+1, self.order_size, liq_info) 
            for i in range(self.n_scenarios)
        ]
        
        # Use multiprocessing pool
        n_workers = max(1, cpu_count() - 1)
        scenario_start = time.time()
        
        with Pool(processes=n_workers) as pool:
            results = pool.map(_run_scenario_wrapper, args_list)
        
        # Process results
        for i, result in enumerate(results):
            if result['success']:
                # Convert to expected format (DE solver only returns trades and cost_breakdown)
                stock_results.append({
                    'cost': result['total_cost'],
                    'solve_time': result['solve_time'],
                    'trades': result['trades'],
                    'cost_breakdown': result['cost_breakdown']
                })
                print(f"Scenario {i+1:2d}/{self.n_scenarios}: "
                      f"Cost = ${result['total_cost']:>10,.2f} | "
                      f"Time = {result['solve_time']:>5.1f}s | "
                      f"✅")
            else:
                print(f"Scenario {i+1:2d}/{self.n_scenarios}: ❌ Failed: {result.get('error', 'Unknown')}")
        
        parallel_time = time.time() - scenario_start
        total_time = time.time() - start_time
        
        # Summary statistics
        if stock_results:
            costs = [r['cost'] for r in stock_results]
            
            print(f"-"*80)
            print(f"✅ Completed {len(stock_results)}/{self.n_scenarios} scenarios")
            print(f"   Parallel execution time: {parallel_time:.1f}s")
            print(f"   Total time (incl. calibration): {total_time:.1f}s")
            print(f"   Speedup: ~{self.n_scenarios * 35 / parallel_time:.1f}x vs sequential (est)")
            print(f"   Cost stats:")
            print(f"     Mean:   ${np.mean(costs):,.2f}")
            print(f"     Std:    ${np.std(costs):,.2f}")
            print(f"     Min:    ${np.min(costs):,.2f}")
            print(f"     Max:    ${np.max(costs):,.2f}")
            
            self.results[ticker] = stock_results
            self.all_scenarios.extend(stock_results)
            
            return stock_results
        else:
            print(f"❌ All scenarios failed for {ticker}")
            return None
    
    def run_all(self):
        """Run simulation for all stocks."""
        
        overall_start = time.time()
        
        for ticker in self.tickers:
            self.run_stock(ticker)
        
        overall_time = time.time() - overall_start
        
        print(f"\n{'='*80}")
        print(f"SIMULATION COMPLETE")
        print(f"{'='*80}")
        print(f"Total time: {overall_time/60:.1f} minutes")
        print(f"Total scenarios: {len(self.all_scenarios)}")
        print(f"Success rate: {len(self.all_scenarios)}/{len(self.tickers)*self.n_scenarios} "
              f"({100*len(self.all_scenarios)/(len(self.tickers)*self.n_scenarios):.1f}%)")
        print(f"{'='*80}\n")
    
    def analyze_results(self) -> dict:
        """Compute statistical analysis of results."""
        
        print(f"\n{'='*80}")
        print(f"STATISTICAL ANALYSIS")
        print(f"{'='*80}\n")
        
        analysis = {}
        
        for ticker, scenarios in self.results.items():
            if not scenarios:
                continue
            
            costs = np.array([s['cost'] for s in scenarios])
            
            # Basic statistics
            analysis[ticker] = {
                'n': len(scenarios),
                'mean_cost': float(np.mean(costs)),
                'std_cost': float(np.std(costs)),
                'min_cost': float(np.min(costs)),
                'max_cost': float(np.max(costs)),
                'median_cost': float(np.median(costs)),
                'cv': float(np.std(costs) / np.mean(costs)),  # Coefficient of variation
            }
            
            # Liquidity info
            if ticker in self.liquidity_info:
                liq = self.liquidity_info[ticker]
                analysis[ticker]['adv'] = liq['adv']
                analysis[ticker]['order_to_adv'] = liq['order_to_adv']
                analysis[ticker]['liquidity_tier'] = liq['liquidity_tier']
                analysis[ticker]['max_trade_fraction'] = liq['max_trade_fraction']
            
            # Print summary
            print(f"{ticker}:")
            print(f"  Scenarios: {analysis[ticker]['n']}")
            print(f"  Mean cost: ${analysis[ticker]['mean_cost']:,.2f} ± ${analysis[ticker]['std_cost']:,.2f}")
            print(f"  Range: ${analysis[ticker]['min_cost']:,.2f} - ${analysis[ticker]['max_cost']:,.2f}")
            if ticker in self.liquidity_info:
                print(f"  ADV: {analysis[ticker]['adv']:,.0f} shares/day")
                print(f"  Order/ADV: {analysis[ticker]['order_to_adv']:.3%}")
                print(f"  Constraint: {analysis[ticker]['max_trade_fraction']:.1%}")
            print()
        
        return analysis
    
    def visualize_results(self, analysis: dict):
        """Create comprehensive visualization suite."""
        
        print(f"{'='*80}")
        print(f"GENERATING VISUALIZATIONS")
        print(f"{'='*80}\n")
        
        # Set publication style
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.rcParams['figure.dpi'] = 300
        plt.rcParams['font.size'] = 10
        
        # Create 6 visualizations
        self._plot_1_cost_distributions(analysis)
        self._plot_2_liquidity_spectrum(analysis)
        self._plot_3_cost_vs_liquidity(analysis)
        self._plot_4_constraint_comparison(analysis)
        self._plot_5_trading_strategies(analysis)
        self._plot_6_summary_dashboard(analysis)
        
        print(f"✅ All visualizations saved to: {self.output_dir}\n")
    
    def _plot_1_cost_distributions(self, analysis: dict):
        """Plot 1: Cost distributions for each stock."""
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('Cost Distributions Across Liquidity Spectrum', 
                     fontsize=16, fontweight='bold')
        
        axes = axes.flatten()
        
        for idx, (ticker, scenarios) in enumerate(self.results.items()):
            if idx >= 6:
                break
            
            ax = axes[idx]
            costs = [s['cost'] for s in scenarios]
            
            # Histogram with KDE
            ax.hist(costs, bins=15, alpha=0.6, color='steelblue', edgecolor='black')
            ax.axvline(np.mean(costs), color='red', linestyle='--', linewidth=2, label=f'Mean: ${np.mean(costs):.2f}')
            ax.axvline(np.median(costs), color='green', linestyle=':', linewidth=2, label=f'Median: ${np.median(costs):.2f}')
            
            ax.set_title(f'{ticker} (n={len(costs)})', fontweight='bold')
            ax.set_xlabel('Total Cost ($)')
            ax.set_ylabel('Frequency')
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
        
        # Remove unused subplots
        for idx in range(len(self.results), 6):
            fig.delaxes(axes[idx])
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '01_cost_distributions.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Plot 1: Cost distributions")
    
    def _plot_2_liquidity_spectrum(self, analysis: dict):
        """Plot 2: Liquidity spectrum visualization."""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Liquidity Spectrum Analysis', fontsize=16, fontweight='bold')
        
        tickers = list(analysis.keys())
        advs = [analysis[t].get('adv', 0) for t in tickers]
        order_advs = [analysis[t].get('order_to_adv', 0)*100 for t in tickers]
        constraints = [analysis[t].get('max_trade_fraction', 0.4)*100 for t in tickers]
        
        # Plot 1: ADV comparison
        colors = plt.cm.viridis(np.linspace(0, 1, len(tickers)))
        bars1 = ax1.bar(tickers, advs, color=colors, edgecolor='black', linewidth=1.5)
        ax1.set_ylabel('Average Daily Volume (shares/day)', fontweight='bold')
        ax1.set_title('Stock Liquidity (ADV)', fontweight='bold')
        ax1.set_yscale('log')
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Add values on bars
        for bar, adv in zip(bars1, advs):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{adv/1e6:.1f}M',
                    ha='center', va='bottom', fontweight='bold')
        
        # Plot 2: Order/ADV ratios and constraints
        x = np.arange(len(tickers))
        width = 0.35
        
        bars2 = ax2.bar(x - width/2, order_advs, width, label='Order/ADV %', 
                       color='coral', edgecolor='black')
        bars3 = ax2.bar(x + width/2, constraints, width, label='Max Trade %', 
                       color='lightgreen', edgecolor='black')
        
        ax2.set_ylabel('Percentage (%)', fontweight='bold')
        ax2.set_title('Order Size vs Constraints', fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(tickers)
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Add values
        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}%',
                    ha='center', va='bottom', fontsize=8)
        
        for bar in bars3:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.0f}%',
                    ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '02_liquidity_spectrum.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Plot 2: Liquidity spectrum")
    
    def _plot_3_cost_vs_liquidity(self, analysis: dict):
        """Plot 3: Cost vs liquidity relationship."""
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        tickers = list(analysis.keys())
        advs = [analysis[t].get('adv', 1) for t in tickers]
        mean_costs = [analysis[t]['mean_cost'] for t in tickers]
        std_costs = [analysis[t]['std_cost'] for t in tickers]
        
        # Scatter plot with error bars
        colors = plt.cm.plasma(np.linspace(0, 1, len(tickers)))
        
        for i, ticker in enumerate(tickers):
            ax.errorbar(advs[i], mean_costs[i], yerr=std_costs[i],
                       fmt='o', markersize=15, capsize=5, capthick=2,
                       color=colors[i], label=ticker, linewidth=2)
        
        ax.set_xlabel('Average Daily Volume (shares/day)', fontweight='bold', fontsize=12)
        ax.set_ylabel('Mean Execution Cost ($)', fontweight='bold', fontsize=12)
        ax.set_title('Execution Cost vs Stock Liquidity', fontweight='bold', fontsize=14)
        ax.set_xscale('log')
        ax.legend(fontsize=10, loc='best')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '03_cost_vs_liquidity.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Plot 3: Cost vs liquidity")
    
    def _plot_4_constraint_comparison(self, analysis: dict):
        """Plot 4: Adaptive vs fixed constraints."""
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        tickers = list(analysis.keys())
        adaptive_constraints = [analysis[t].get('max_trade_fraction', 0.4)*100 for t in tickers]
        fixed_constraint = [40] * len(tickers)
        
        x = np.arange(len(tickers))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, adaptive_constraints, width, 
                      label='Adaptive (Liquidity-Based)', 
                      color='steelblue', edgecolor='black', linewidth=1.5)
        bars2 = ax.bar(x + width/2, fixed_constraint, width, 
                      label='Fixed (Traditional 40%)', 
                      color='lightcoral', edgecolor='black', linewidth=1.5)
        
        ax.set_ylabel('Max Trade per Period (%)', fontweight='bold', fontsize=12)
        ax.set_title('Adaptive vs Fixed Constraints', fontweight='bold', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels(tickers)
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add values and differences
        for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
            h1 = bar1.get_height()
            h2 = bar2.get_height()
            
            ax.text(bar1.get_x() + bar1.get_width()/2., h1,
                   f'{h1:.0f}%', ha='center', va='bottom', fontweight='bold')
            ax.text(bar2.get_x() + bar2.get_width()/2., h2,
                   f'{h2:.0f}%', ha='center', va='bottom', fontweight='bold')
            
            # Show difference
            diff = h1 - h2
            if abs(diff) > 1:
                ax.text(i, max(h1, h2) + 2, f'{diff:+.0f}%',
                       ha='center', va='bottom', fontsize=9,
                       color='red' if diff < 0 else 'green')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '04_constraint_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Plot 4: Constraint comparison")
    
    def _plot_5_trading_strategies(self, analysis: dict):
        """Plot 5: Example trading strategies."""
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('Optimal Trading Strategies (First Scenario)', 
                     fontsize=16, fontweight='bold')
        
        axes = axes.flatten()
        
        for idx, (ticker, scenarios) in enumerate(self.results.items()):
            if idx >= 6 or not scenarios:
                break
            
            ax = axes[idx]
            
            # Get first scenario's trades (stored as 'trades' not 'optimal_trades')
            trades = np.array(scenarios[0]['trades'])
            periods = np.arange(1, len(trades) + 1)
            
            # Bar chart
            bars = ax.bar(periods, trades, color='steelblue', edgecolor='black', alpha=0.7)
            
            # Color first trade differently (front-loading)
            bars[0].set_color('darkred')
            bars[0].set_alpha(0.9)
            
            # Cumulative line
            cumulative = np.cumsum(trades)
            ax2 = ax.twinx()
            ax2.plot(periods, cumulative, 'r-o', linewidth=2, markersize=6, label='Cumulative')
            ax2.axhline(self.order_size, color='green', linestyle='--', label='Target')
            
            ax.set_title(f'{ticker}', fontweight='bold')
            ax.set_xlabel('Period')
            ax.set_ylabel('Shares Traded', color='steelblue')
            ax2.set_ylabel('Cumulative Shares', color='red')
            ax.grid(True, alpha=0.3)
            
            # Add front-loading percentage
            front_load_pct = (trades[0] / self.order_size) * 100
            ax.text(0.95, 0.95, f'Front-load: {front_load_pct:.1f}%',
                   transform=ax.transAxes, ha='right', va='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                   fontweight='bold')
        
        # Remove unused subplots
        for idx in range(len(self.results), 6):
            fig.delaxes(axes[idx])
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '05_trading_strategies.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Plot 5: Trading strategies")
    
    def _plot_6_summary_dashboard(self, analysis: dict):
        """Plot 6: Summary dashboard."""
        
        fig = plt.figure(figsize=(16, 12))
        gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)
        
        fig.suptitle('Monte Carlo Simulation Dashboard', fontsize=18, fontweight='bold')
        
        tickers = list(analysis.keys())
        
        # Panel 1: Mean costs comparison
        ax1 = fig.add_subplot(gs[0, :])
        mean_costs = [analysis[t]['mean_cost'] for t in tickers]
        std_costs = [analysis[t]['std_cost'] for t in tickers]
        
        bars = ax1.barh(tickers, mean_costs, xerr=std_costs, capsize=5,
                       color=plt.cm.viridis(np.linspace(0, 1, len(tickers))),
                       edgecolor='black', linewidth=1.5)
        ax1.set_xlabel('Mean Execution Cost ($)', fontweight='bold')
        ax1.set_title('Cost Comparison Across Stocks', fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='x')
        
        for i, (ticker, bar) in enumerate(zip(tickers, bars)):
            width = bar.get_width()
            ax1.text(width, bar.get_y() + bar.get_height()/2,
                    f'  ${mean_costs[i]:,.0f}',
                    va='center', fontweight='bold')
        
        # Panel 2: Liquidity tiers
        ax2 = fig.add_subplot(gs[1, 0])
        tier_counts = {}
        for t in tickers:
            tier = analysis[t].get('liquidity_tier', 'unknown')
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
        ax2.pie(tier_counts.values(), labels=tier_counts.keys(), autopct='%1.0f%%',
               startangle=90, colors=plt.cm.Set3.colors)
        ax2.set_title('Liquidity Distribution', fontweight='bold')
        
        # Panel 3: Order/ADV ratios
        ax3 = fig.add_subplot(gs[1, 1])
        order_advs = [analysis[t].get('order_to_adv', 0)*100 for t in tickers]
        ax3.barh(tickers, order_advs, color='coral', edgecolor='black')
        ax3.set_xlabel('Order/ADV (%)', fontweight='bold')
        ax3.set_title('Order Size Relative to ADV', fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='x')
        ax3.axvline(1.0, color='red', linestyle='--', linewidth=2, label='1% threshold')
        ax3.legend(fontsize=8)
        
        # Panel 4: Coefficient of variation
        ax4 = fig.add_subplot(gs[1, 2])
        cvs = [analysis[t]['cv']*100 for t in tickers]
        ax4.barh(tickers, cvs, color='lightgreen', edgecolor='black')
        ax4.set_xlabel('Coefficient of Variation (%)', fontweight='bold')
        ax4.set_title('Cost Variability', fontweight='bold')
        ax4.grid(True, alpha=0.3, axis='x')
        
        # Panel 5: Summary statistics table
        ax5 = fig.add_subplot(gs[2, :])
        ax5.axis('off')
        
        table_data = []
        headers = ['Stock', 'N', 'Mean Cost', 'Std Dev', 'ADV', 'Order/ADV', 'Constraint']
        
        for ticker in tickers:
            a = analysis[ticker]
            row = [
                ticker,
                f"{a['n']}",
                f"${a['mean_cost']:,.0f}",
                f"${a['std_cost']:,.0f}",
                f"{a.get('adv', 0)/1e6:.1f}M",
                f"{a.get('order_to_adv', 0):.3%}",
                f"{a.get('max_trade_fraction', 0.4):.0%}"
            ]
            table_data.append(row)
        
        table = ax5.table(cellText=table_data, colLabels=headers,
                         cellLoc='center', loc='center',
                         bbox=[0, 0, 1, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # Style header
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Alternate row colors
        for i in range(1, len(table_data) + 1):
            for j in range(len(headers)):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#f0f0f0')
        
        plt.savefig(self.output_dir / '06_summary_dashboard.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Plot 6: Summary dashboard")
    
    def save_results(self, analysis: dict):
        """Save all results to JSON."""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Prepare data for JSON serialization
        export_data = {
            'metadata': {
                'timestamp': timestamp,
                'n_scenarios': self.n_scenarios,
                'order_size': self.order_size,
                'conservative_mode': self.conservative_mode,
                'tickers': self.tickers
            },
            'liquidity_info': {},
            'analysis': analysis,
            'all_scenarios': []
        }
        
        # Add liquidity info
        for ticker, liq in self.liquidity_info.items():
            export_data['liquidity_info'][ticker] = {
                'adv': float(liq['adv']),
                'order_to_adv': float(liq['order_to_adv']),
                'liquidity_tier': liq['liquidity_tier'],
                'max_trade_fraction': float(liq['max_trade_fraction'])
            }
        
        # Add scenario details (simplified)
        for scenario in self.all_scenarios:
            export_data['all_scenarios'].append({
                'ticker': scenario['ticker'],
                'scenario_id': scenario['scenario_id'],
                'cost': float(scenario['cost']),
                'optimal_trades': scenario['optimal_trades'].tolist() if hasattr(scenario['optimal_trades'], 'tolist') else scenario['optimal_trades'],
                'solve_time': float(scenario.get('solve_time', 0))
            })
        
        # Save to file
        output_file = self.output_dir / f'simulation_results_{timestamp}.json'
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Results saved to: {output_file}\n")
        
        return output_file


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    """
    Run comprehensive Monte Carlo simulation with adaptive constraints.
    """
    
    # Configuration
    TICKERS = ['AAPL', 'NVDA', 'PLTR', 'OPEN', 'TOUR']
    N_SCENARIOS = 10
    ORDER_SIZE = 100000
    CONSERVATIVE_MODE = True
    
    # Create and run simulation
    sim = ComprehensiveMonteCarloSimulation(
        tickers=TICKERS,
        n_scenarios=N_SCENARIOS,
        order_size=ORDER_SIZE,
        conservative_mode=CONSERVATIVE_MODE
    )
    
    # Run all simulations
    sim.run_all()
    
    # Analyze results
    analysis = sim.analyze_results()
    
    # Generate visualizations
    sim.visualize_results(analysis)
    
    # Save results
    results_file = sim.save_results(analysis)
    
    # Final summary
    print(f"{'='*80}")
    print(f"SIMULATION COMPLETE ✅")
    print(f"{'='*80}")
    print(f"Stocks analyzed: {len(sim.results)}")
    print(f"Total scenarios: {len(sim.all_scenarios)}")
    print(f"Results saved to: {sim.output_dir}")
    print(f"Visualizations: 6 PNG files")
    print(f"Data export: {results_file.name}")
    print(f"{'='*80}\n")
