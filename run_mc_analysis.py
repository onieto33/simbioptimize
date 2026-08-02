#!/usr/bin/env python
"""
Monte Carlo analysis - 500 runs with convergence check.
"""
import json
import sys
import pandas as pd
import numpy as np

print("="*70)
print("MONTE CARLO ANALYSIS - 500 RUNS")
print("="*70)

# Extract and execute all code from notebook
print("\nLoading notebook...")
with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

# Combine all code
code = ""
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        if "!pip" not in source:
            code += source + "\n"

print("Executing notebook (Cell 22 with N_RUNS=500)...")

# Execute
namespace = {}
try:
    exec(code, namespace)
except Exception as e:
    error_msg = str(e)
    if "display" not in error_msg and "jupyter" not in error_msg.lower():
        print(f"Error: {type(e).__name__}: {error_msg[:200]}")

# Get results
if "results" not in namespace:
    print("\n[ERROR] No results found in namespace")
    sys.exit(1)

results = namespace["results"]
print(f"\n[OK] Got results: {len(results)} rows, {len(results.columns)} columns")

# Extract summary statistics per scenario
print("\n" + "="*70)
print("CONVERGENCE ANALYSIS")
print("="*70)

scenarios = results["scenario"].unique()
print(f"\nScenarios analyzed: {len(scenarios)}")

for scenario in scenarios:
    print(f"\n{scenario}")
    print("-" * 70)
    
    df_scen = results[results["scenario"] == scenario].copy()
    df_scen = df_scen.sort_values("run_id")
    
    # Key indicators
    indicators = [
        "unmet_flow", "total_treated", "manufacturer_cumulative_adoption",
        "recycler_adoption_rate", "pathway_capacity_recovery"
    ]
    
    # Check which indicators exist
    available = [ind for ind in indicators if ind in df_scen.columns]
    
    # Calculate percentiles for full dataset and final 5 runs
    for indicator in available[:3]:  # Show first 3
        full_50 = df_scen[indicator].median()
        final_5 = df_scen[df_scen["run_id"] > df_scen["run_id"].max() - 5][indicator].median()
        
        pct_diff = abs((final_5 - full_50) / max(abs(full_50), 0.001)) * 100
        status = "[PASS]" if pct_diff < 2 else "[WARN]"
        
        print(f"  {indicator}: full_med={full_50:.2f}, final5_med={final_5:.2f}, diff={pct_diff:.1f}% {status}")

# Summary statistics
print("\n" + "="*70)
print("SUMMARY STATISTICS (ALL RUNS)")
print("="*70)

for scenario in scenarios:
    print(f"\n{scenario}")
    print("-" * 70)
    
    df_scen = results[results["scenario"] == scenario]
    
    # Show key columns
    for col in ["unmet_flow", "total_treated", "manufacturer_cumulative_adoption"]:
        if col in df_scen.columns:
            mean = df_scen[col].mean()
            std = df_scen[col].std()
            p10 = df_scen[col].quantile(0.10)
            p50 = df_scen[col].quantile(0.50)
            p90 = df_scen[col].quantile(0.90)
            
            print(f"  {col}:")
            print(f"    Mean: {mean:.4f}, Std: {std:.4f}")
            print(f"    P10: {p10:.4f}, P50: {p50:.4f}, P90: {p90:.4f}")

# Save results
print("\n" + "="*70)
results.to_csv("mc_results_500runs.csv", index=False)
print(f"[OK] Saved results to mc_results_500runs.csv ({len(results)} rows)")

print("\n" + "="*70)
print("MONTE CARLO ANALYSIS COMPLETE")
print("="*70)
