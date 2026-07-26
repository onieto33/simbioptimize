#!/usr/bin/env python
"""
Direct model execution and validation (bypassing notebook parsing issues).

Creates a minimal test that:
1. Imports all dependencies
2. Runs one deterministic model instance
3. Validates balances
"""
import sys
import json
import numpy as np
import pandas as pd

print("="*70)
print("DETERMINISTIC VALIDATION - DIRECT EXECUTION")
print("="*70)

# Extract key code from notebook cells
print("\nLoading notebook code...")
with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

# Collect all code
code = ""
cell_count = 0
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        cell_count += 1
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        
        # Skip pip installs
        if "!pip" not in source:
            code += f"\n# ===== CELL {cell_count} =====\n"
            code += source
            code += "\n"

# Write combined code to file
with open("_combined_notebook_code.py", "w", encoding="utf-8") as f:
    f.write(code)

print(f"Extracted {cell_count} code cells")

# Now execute carefully, catching errors
namespace = {}
try:
    exec(code, namespace)
except Exception as e:
    error_msg = str(e)
    # Ignore Jupyter-specific errors
    if "display" not in error_msg and "jupyter" not in error_msg.lower():
        print(f"\nExecution error: {type(e).__name__}: {error_msg[:200]}")

# Check if WTBHybridModel was defined
if "WTBHybridModel" not in namespace:
    print("[FAIL] WTBHybridModel not defined")
    sys.exit(1)

# Check if we already have results from run_all_scenarios
if "results_df" in namespace or "mc_results" in namespace:
    results = namespace.get("results_df") or namespace.get("mc_results")
    print(f"\n✓ Found existing results: {len(results)} rows")
    
    # Skip model execution and go to validation
    print("\nSKIPPING MODEL INSTANCE (using existing results)")
else:
    # Create and run one model instance
    WTBHybridModel = namespace["WTBHybridModel"]
    SCENARIOS = namespace.get("SCENARIOS", {})
    START_YEAR = namespace.get("START_YEAR", 2026)
    END_YEAR = namespace.get("END_YEAR", 2050)
    N_OPERATORS = namespace.get("N_OPERATORS", 100)
    N_RECYCLERS = namespace.get("N_RECYCLERS", 40)
    N_MANUFACTURERS = namespace.get("N_MANUFACTURERS", 60)
    
    if "Baseline" not in SCENARIOS:
        print("[ERROR] Baseline scenario not found")
        sys.exit(1)
    
    print(f"Running Baseline scenario (2026-2050, seed=42)...")
    
    model = WTBHybridModel(
        scenario_config=SCENARIOS["Baseline"],
        start_year=START_YEAR,
        end_year=END_YEAR,
        seed=42,
        n_operators=N_OPERATORS,
        n_recyclers=N_RECYCLERS,
        n_manufacturers=N_MANUFACTURERS,
    )
    
    results = model.run()
    print(f"✓ Model completed. Generated {len(results)} years of results")
    
except Exception as e:
    print(f"[FAIL] Model execution failed:")
    print(f"  {type(e).__name__}: {str(e)[:300]}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# VALIDATION
print("\n" + "-"*70)
print("VALIDATING RESULTS")
print("-"*70)

# Balance check
print("\n1. Balance: desired = treated + unmet")
balance_errors = 0
for idx, row in results.iterrows():
    desired = row.get("desired_total_flow", 0)
    treated = row.get("total_treated", 0)
    unmet = row.get("unmet_flow", 0)
    
    error = abs((treated + unmet) - desired)
    if error > max(desired * 0.001, 0.01):  # Tolerance: 0.1% or 0.01 absolute
        balance_errors += 1

if balance_errors == 0:
    print("   [PASS] All years satisfy balance")
else:
    print(f"   [FAIL] {balance_errors} balance violations")

# Capacity check
print("2. Capacity constraints")
PATHWAYS = namespace.get("PATHWAYS", [])
capacity_violations = 0

for pathway in PATHWAYS:
    flow_col = f"flow_{pathway}"
    cap_col = f"capacity_{pathway}"
    
    if flow_col in results.columns and cap_col in results.columns:
        violations = (results[flow_col] > results[cap_col] + 0.01).sum()
        capacity_violations += violations

if capacity_violations == 0:
    print("   [PASS] All flows <= capacity")
else:
    print(f"   [FAIL] {capacity_violations} capacity violations")

# Data quality
print("3. Data quality")
nans = results.isna().sum().sum()
if nans == 0:
    print("   [PASS] No NaN values")
else:
    print(f"   [FAIL] {nans} NaN values found")

# Summary
print("\n" + "-"*70)
print("SUMMARY")
print("-"*70)
print(f"Results shape: {results.shape}")
print(f"Columns: {len(results.columns)}")
print(f"Years: {results['year'].min()} - {results['year'].max()}")

print("\n" + "="*70)
if balance_errors == 0 and capacity_violations == 0 and nans == 0:
    print("RESULT: VALIDATION PASSED - Ready for Monte Carlo")
else:
    print("RESULT: VALIDATION FAILED - Check errors above")
print("="*70)
