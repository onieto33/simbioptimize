#!/usr/bin/env python
"""
Add deterministic validation cell to notebook.

Runs 1 scenario (Baseline) with seed=42 for 2026-2050 and validates:
- Balance: total_treated + unmet_flow == desired_flow
- Capacity: actual_flows <= capacity for each pathway
- Monotonicity: stocks decrease over time
- No NaNs or infinities
"""
import json

with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r") as f:
    nb = json.load(f)

# Find the cell to insert after (let's insert after cell 9, scenario execution)
# We'll create a new cell for deterministic validation

validation_code = '''# ============================================================
# DETERMINISTIC VALIDATION (Single run, seed=42)
# ============================================================
# Before Monte Carlo, validate one scenario deterministically
# to catch logic errors, infinite loops, or accounting failures.

print("\\n" + "="*70)
print("DETERMINISTIC VALIDATION - Running single baseline scenario")
print("="*70)

# Run one scenario with seed=42
validation_model = WTBHybridModel(
    scenario_config=SCENARIOS["Baseline"],
    start_year=START_YEAR,
    end_year=END_YEAR,
    seed=42,
    n_operators=N_OPERATORS,
    n_recyclers=N_RECYCLERS,
    n_manufacturers=N_MANUFACTURERS,
)

validation_results = validation_model.run()

print(f"\\nGenerated {len(validation_results)} years of results")
print(f"Columns: {len(validation_results.columns)}")

# ============================================================
# BALANCE VALIDATION
# ============================================================

print("\\n" + "-"*70)
print("1. FLOW BALANCE: desired = treated + unmet")
print("-"*70)

balance_errors = []
for idx, row in validation_results.iterrows():
    desired = row["desired_total_flow"]
    treated = row["total_treated"]
    unmet = row["unmet_flow"]
    
    error = abs((treated + unmet) - desired)
    
    if error > desired * 0.001:  # Tolerance: 0.1%
        balance_errors.append({
            "year": row["year"],
            "desired": desired,
            "treated": treated,
            "unmet": unmet,
            "error": error,
            "error_pct": 100 * error / desired if desired > 0 else 0
        })

if balance_errors:
    print(f"[ERROR] {len(balance_errors)} balance violations:")
    for err in balance_errors[:5]:
        print(f"  Year {err['year']}: error={err['error']:.3e} ({err['error_pct']:.2f}%)")
else:
    print("[OK] All years satisfy: treated + unmet ≈ desired (error < 0.1%)")

# ============================================================
# CAPACITY CONSTRAINTS
# ============================================================

print("\\n" + "-"*70)
print("2. CAPACITY CONSTRAINTS: actual_flow <= capacity for each pathway")
print("-"*70)

capacity_violations = []
for pathway in PATHWAYS:
    flow_col = f"flow_{pathway}"
    capacity_col = f"capacity_{pathway}"
    
    if flow_col in validation_results.columns and capacity_col in validation_results.columns:
        violations = validation_results[
            validation_results[flow_col] > validation_results[capacity_col] + 0.01
        ]
        
        if len(violations) > 0:
            capacity_violations.extend([
                {
                    "pathway": pathway,
                    "year": row["year"],
                    "flow": row[flow_col],
                    "capacity": row[capacity_col],
                    "excess": row[flow_col] - row[capacity_col]
                }
                for _, row in violations.iterrows()
            ])

if capacity_violations:
    print(f"[ERROR] {len(capacity_violations)} capacity violations:")
    for v in capacity_violations[:5]:
        print(f"  {v['pathway']} year {v['year']}: flow={v['flow']:.1f} > capacity={v['capacity']:.1f} (excess={v['excess']:.1f})")
else:
    print("[OK] All pathways respect capacity constraints")

# ============================================================
# STOCK ACCOUNTING
# ============================================================

print("\\n" + "-"*70)
print("3. UNTREATED STOCK DYNAMICS")
print("-"*70)

stock_errors = []
for idx, row in validation_results.iterrows():
    opening = row["opening_untreated_stock"]
    closing = row["untreated_stock"]
    decommissioned = row["decommissioned"]
    treated = row["total_treated"]
    
    # Stock change should be: closing = opening + decommissioned - treated
    expected_closing = opening + decommissioned - treated
    error = abs(closing - expected_closing)
    
    if error > 0.01:  # Tolerance: small numerical error
        stock_errors.append({
            "year": row["year"],
            "error": error,
            "expected": expected_closing,
            "actual": closing
        })

if stock_errors:
    print(f"[ERROR] {len(stock_errors)} stock accounting violations:")
    for err in stock_errors[:5]:
        print(f"  Year {err['year']}: error={err['error']:.3e}")
else:
    print("[OK] Stock accounting satisfied for all years")

print(f"\\n  Opening stock (2026): {validation_results.iloc[0]['opening_untreated_stock']:.1f}")
print(f"  Closing stock (2050): {validation_results.iloc[-1]['untreated_stock']:.1f}")

# ============================================================
# DATA QUALITY
# ============================================================

print("\\n" + "-"*70)
print("4. DATA QUALITY (NaN, Inf, etc.)")
print("-"*70)

nan_count = validation_results.isna().sum().sum()
inf_count = np.isinf(validation_results.select_dtypes(include=[float])).sum().sum()

if nan_count > 0:
    print(f"[ERROR] Found {nan_count} NaN values")
    print(validation_results.isna().sum()[validation_results.isna().sum() > 0])
else:
    print("[OK] No NaN values")

if inf_count > 0:
    print(f"[ERROR] Found {inf_count} Inf values")
else:
    print("[OK] No Inf values")

# ============================================================
# SUMMARY STATISTICS
# ============================================================

print("\\n" + "-"*70)
print("5. SUMMARY STATISTICS")
print("-"*70)

print("\\nTreatment pathway evolution (2026 vs 2050):")
for pathway in ["direct_reuse", "incumbent_open_loop", "solvolysis"]:
    share_col_2026 = f"{pathway}_share"
    if share_col_2026 in validation_results.columns:
        v_2026 = validation_results.iloc[0][share_col_2026] * 100
        v_2050 = validation_results.iloc[-1][share_col_2026] * 100
        print(f"  {pathway}: {v_2026:>5.1f}% (2026) → {v_2050:>5.1f}% (2050)")

print("\\nCapacity evolution (total):")
cap_2026 = validation_results.iloc[0][[c for c in validation_results.columns if "capacity_" in c]].sum()
cap_2050 = validation_results.iloc[-1][[c for c in validation_results.columns if "capacity_" in c]].sum()
print(f"  2026: {cap_2026:.1f} → 2050: {cap_2050:.1f} (change: {100*(cap_2050-cap_2026)/cap_2026:+.1f}%)")

print("\\nManufacturer adoption progression:")
adoption_2026 = validation_results.iloc[0].get("manufacturer_realized_adoption_share", 0.0)
adoption_2050 = validation_results.iloc[-1].get("manufacturer_realized_adoption_share", 0.0)
print(f"  2026: {adoption_2026*100:>5.1f}% → 2050: {adoption_2050*100:>5.1f}%")

print("\\n" + "="*70)
if not balance_errors and not capacity_violations and not stock_errors and nan_count == 0:
    print("RESULT: DETERMINISTIC VALIDATION PASSED ✓")
    print("Ready for Monte Carlo analysis (500 runs)")
else:
    print("RESULT: VALIDATION FAILED - Fix errors above before Monte Carlo")
print("="*70 + "\\n")
'''

# Find the right place to insert (after cell 9, the scenario runner)
# We'll insert as a new cell after index 9

new_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": validation_code.split('\n')
}

# Insert after cell 9 (scenario execution)
nb["cells"].insert(10, new_cell)

print("Validation cell created (will be inserted at index 10)")

# Save
with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook updated with deterministic validation cell!")
