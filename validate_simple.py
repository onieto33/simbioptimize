#!/usr/bin/env python
"""
Simple deterministic validation - run all notebook code and validate results.
"""
import json
import sys
import pandas as pd

print("="*70)
print("DETERMINISTIC VALIDATION")
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

print("Executing notebook code...")

# Execute
namespace = {}
try:
    exec(code, namespace)
except Exception as e:
    error_msg = str(e)
    # Ignore Jupyter-specific errors
    if "display" not in error_msg and "jupyter" not in error_msg.lower():
        print(f"Error: {type(e).__name__}: {error_msg[:150]}")

# Get results
results = None
if "results" in namespace:
    results = namespace["results"]
    print(f"\n[OK] Got results: {len(results)} rows, {len(results.columns)} columns")
elif "results_df" in namespace:
    results = namespace["mc_results"]
    print(f"\n[OK] Got mc_results: {len(results)} rows, {len(results.columns)} columns")
else:
    print("\n[ERROR] No results found in namespace")
    print(f"Available objects: {[k for k in namespace.keys() if not k.startswith('_')][:20]}")
    sys.exit(1)

# VALIDATION
print("\n" + "-"*70)
print("VALIDATING RESULTS")
print("-"*70)

# Check required columns
required = ["desired_total_flow", "total_treated", "unmet_flow", "year"]
missing = [c for c in required if c not in results.columns]
if missing:
    print(f"[FAIL] Missing columns: {missing}")
    sys.exit(1)

# Balance validation
print("\n1. Balance Check (desired = treated + unmet)")
balance_errors = []
for idx, row in results.iterrows():
    desired = row["desired_total_flow"]
    treated = row["total_treated"]
    unmet = row["unmet_flow"]
    
    error = abs((treated + unmet) - desired)
    
    if error > max(desired * 0.001, 0.01):
        balance_errors.append(row["year"])

if balance_errors:
    print(f"   [FAIL] {len(balance_errors)} years with balance errors: {set(balance_errors)}")
else:
    print(f"   [PASS] All {len(results)} rows satisfy balance (error < 0.1%)")

# Data quality
print("\n2. Data Quality")
nans = results.isna().sum().sum()
infs = 0
for col in results.select_dtypes(include=['float64']).columns:
    infs += (results[col] == float('inf')).sum()
    infs += (results[col] == float('-inf')).sum()

if nans == 0:
    print(f"   [PASS] No NaN values")
else:
    print(f"   [FAIL] Found {nans} NaN values")

if infs == 0:
    print(f"   [PASS] No Inf values")
else:
    print(f"   [FAIL] Found {infs} Inf values")

# Summary
print("\n" + "-"*70)
print("SUMMARY")
print("-"*70)
print(f"Results: {len(results)} rows, {len(results.columns)} columns")
print(f"Years: {results['year'].min()} - {results['year'].max()}")
print(f"Scenarios: {results.get('scenario', pd.Series()).nunique() if 'scenario' in results else 'N/A'}")

# Final verdict
print("\n" + "="*70)
if not balance_errors and nans == 0 and infs == 0:
    print("RESULT: VALIDATION PASSED")
    print("Model balances are consistent - ready for production runs")
else:
    print("RESULT: VALIDATION FAILED")
    print(f"Errors: {len(balance_errors)} balance, {nans} NaNs, {infs} Infs")
print("="*70)

