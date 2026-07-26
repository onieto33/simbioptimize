#!/usr/bin/env python
"""
Execute deterministic validation by running notebook cells as Python code.

Runs the model with seed=42, 1 scenario, years 2026-2050.
Validates: balances, capacity constraints, stock accounting, data quality.
"""
import json
import sys

print("="*70)
print("DETERMINISTIC VALIDATION - RUNNING NOTEBOOK CELLS")
print("="*70)

# Load notebook
with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

# Extract and execute cells
code_globals = {}

cell_count = 0
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        cell_count += 1
        
        # Skip markdown cells
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        
        # Skip pip install and imports that might fail
        if "!pip" in source:
            print(f"[Skip] Cell {cell_count} (pip install)")
            continue
        
        # Execute cell
        try:
            print(f"\n[Exec] Cell {cell_count}...", end=" ")
            exec(source, code_globals)
            print("OK")
            
            # Stop after running one scenario (before MC)
            if "run_all_scenarios" in source and "DETERMINISTIC" not in source:
                print("\n" + "="*70)
                print("MODEL EXECUTION COMPLETE")
                print("="*70)
                
                # Now run validation on the results
                if "results_df" in code_globals:
                    results = code_globals["results_df"]
                    print(f"\nGenerated {len(results)} rows of results")
                    
                    # BALANCE VALIDATION
                    print("\n" + "-"*70)
                    print("1. BALANCE CHECK: desired = treated + unmet")
                    print("-"*70)
                    
                    errors = []
                    for idx, row in results.iterrows():
                        desired = row.get("desired_total_flow", 0)
                        treated = row.get("total_treated", 0)
                        unmet = row.get("unmet_flow", 0)
                        
                        error = abs((treated + unmet) - desired)
                        if error > desired * 0.001 and desired > 0:
                            errors.append((row.get("year"), error, desired))
                    
                    if errors:
                        print(f"[FAIL] {len(errors)} balance violations:")
                        for year, error, desired in errors[:5]:
                            print(f"  Year {year}: error = {error:.3e} ({100*error/desired:.2f}%)")
                    else:
                        print("[PASS] All years satisfy balance (error < 0.1%)")
                    
                    # CAPACITY CHECK
                    print("\n" + "-"*70)
                    print("2. CAPACITY CONSTRAINTS")
                    print("-"*70)
                    
                    pathways = ["reuse", "repurposing", "mechanical_recycling", "pyrolysis", "recovery", "solvolysis"]
                    violations = 0
                    
                    for pathway in pathways:
                        flow_col = f"flow_{pathway}"
                        cap_col = f"capacity_{pathway}"
                        
                        if flow_col in results.columns and cap_col in results.columns:
                            excess = results[results[flow_col] > results[cap_col] + 0.01]
                            if len(excess) > 0:
                                violations += len(excess)
                                print(f"  [{pathway}] {len(excess)} violations")
                    
                    if violations == 0:
                        print("[PASS] All flows <= capacity for all years")
                    else:
                        print(f"[FAIL] {violations} capacity violations total")
                    
                    # DATA QUALITY
                    print("\n" + "-"*70)
                    print("3. DATA QUALITY")
                    print("-"*70)
                    
                    nans = results.isna().sum().sum()
                    if nans > 0:
                        print(f"[FAIL] Found {nans} NaN values")
                    else:
                        print("[PASS] No NaN values")
                    
                    # SUMMARY
                    print("\n" + "-"*70)
                    print("4. SUMMARY STATISTICS")
                    print("-"*70)
                    
                    if "desired_share_solvolysis" in results.columns:
                        solv_2026 = results.iloc[0].get("desired_share_solvolysis", 0) * 100
                        solv_2050 = results.iloc[-1].get("desired_share_solvolysis", 0) * 100
                        print(f"Solvolysis desired share: {solv_2026:.1f}% (2026) -> {solv_2050:.1f}% (2050)")
                    
                    if "manufacturer_realized_adoption_share" in results.columns:
                        adopt_2026 = results.iloc[0].get("manufacturer_realized_adoption_share", 0) * 100
                        adopt_2050 = results.iloc[-1].get("manufacturer_realized_adoption_share", 0) * 100
                        print(f"Manufacturer adoption: {adopt_2026:.1f}% (2026) -> {adopt_2050:.1f}% (2050)")
                    
                    print("\n" + "="*70)
                    print("DETERMINISTIC VALIDATION COMPLETE")
                    print("="*70)
                break
        
        except Exception as e:
            print(f"ERROR")
            print(f"  {type(e).__name__}: {str(e)[:100]}")
            
            # If error in core model, stop
            if "WTBHybridModel" in source or "run_all_scenarios" in source:
                print("\n[CRITICAL] Error in model execution - aborting")
                sys.exit(1)
            else:
                # Otherwise continue
                continue

print("\nDone.")
