#!/usr/bin/env python
"""
Refactor Celda 23: Add diagnostic classification and enhanced balance validation.

Add 3 diagnostic categories:
1. Total capacity shortage
2. Allocation mismatch (desired pathway has no capacity)
3. Closed-loop demand insufficiency
"""
import json

with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r") as f:
    nb = json.load(f)

# Find cell 23
cell_23_idx = None
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        if "Annual WTB flow indicators" in source or "Pathway-flow validation" in source:
            cell_23_idx = i
            break

if cell_23_idx is None:
    print("ERROR: Could not find cell 23")
    exit(1)

print(f"Found cell 23 at index {cell_23_idx}")

# Get the cell
cell = nb["cells"][cell_23_idx]
source_list = cell["source"] if isinstance(cell["source"], list) else [cell["source"]]
source = "".join(source_list)

# Add diagnostic functions at the end of the cell
diagnostic_code = '''

# ============================================================
# DIAGNOSTIC CLASSIFICATION
# ============================================================
# Classify unmet flow causes into three categories:
# 1. Total capacity shortage: all available capacity < total demand
# 2. Allocation mismatch: desired pathway selected but lacks capacity; other pathways have spare
# 3. Closed-loop demand insufficiency: solvolysis available but manufacturer adoption insufficient

def classify_unmet_flow_cause(year_data):
    """
    Classify the root cause of unmet_flow for a given year/scenario.
    
    Returns one of:
    - 'total_capacity_shortage': Total demand exceeds all available capacity
    - 'allocation_mismatch': Desired pathways lack capacity but others have spare
    - 'closed_loop_demand_insufficient': Solvolysis supply available but adoption too low
    - 'no_unmet_flow': No unmet flow this year
    """
    unmet = year_data.get("unmet_flow", 0.0)
    
    if unmet <= 0.0001:
        return "no_unmet_flow"
    
    # Get pathway-specific data
    desired_flows = {}
    actual_flows = {}
    unmet_by_pathway = {}
    capacities = {}
    
    for pathway in PATHWAYS:
        desired_flows[pathway] = year_data.get(f"desired_flow_{pathway}", 0.0)
        actual_flows[pathway] = year_data.get(f"flow_{pathway}", 0.0)
        unmet_by_pathway[pathway] = year_data.get(f"unmet_flow_{pathway}", 0.0)
        capacities[pathway] = year_data.get(f"capacity_{pathway}", 0.0)
    
    total_desired = sum(desired_flows.values())
    total_capacity = sum(capacities.values())
    
    # 1. Total capacity shortage?
    if total_capacity < (total_desired - unmet * 0.01):
        return "total_capacity_shortage"
    
    # 2. Check for allocation mismatch: some pathways have unmet demand while others have spare capacity
    pathways_with_unmet = {p: unmet_by_pathway[p] for p in PATHWAYS if unmet_by_pathway[p] > 0.001}
    pathways_with_spare = {p: capacities[p] - actual_flows[p] for p in PATHWAYS 
                          if (capacities[p] - actual_flows[p]) > 0.001}
    
    if pathways_with_unmet and pathways_with_spare:
        return "allocation_mismatch"
    
    # 3. Closed-loop demand insufficiency?
    # If solvolysis has capacity but manufacturer adoption is low
    solvolysis_capacity = capacities.get("solvolysis", 0.0)
    solvolysis_flow = actual_flows.get("solvolysis", 0.0)
    manufacturer_adoption = year_data.get("manufacturer_realized_adoption_share", 0.0)
    
    if solvolysis_capacity > 0.1 and manufacturer_adoption < 0.30 and unmet > 0.001:
        return "closed_loop_demand_insufficient"
    
    return "other"

# Apply diagnostic classification
mc_results["unmet_flow_diagnosis"] = mc_results.apply(
    classify_unmet_flow_cause,
    axis=1
)

# ============================================================
# BALANCE AND COHERENCE VALIDATION
# ============================================================

# Unmet flow accounting: sum of pathway-specific unmet flows should equal total
pathway_unmet_columns = [
    f"unmet_flow_{pathway}"
    for pathway in PATHWAYS
]

mc_results["total_unmet_from_pathways"] = mc_results[
    pathway_unmet_columns
].sum(axis=1)

mc_results["unmet_flow_accounting_error"] = (
    mc_results["total_unmet_from_pathways"]
    - mc_results["unmet_flow"]
).abs()

# Flag rows where accounting error exceeds tolerance (1% of demand)
mc_results["unmet_flow_accounting_invalid"] = (
    mc_results["unmet_flow_accounting_error"] > 
    (mc_results["desired_total_flow"] * 0.01)
)

# Material coherence: desired_flow should partition into actual_flow + unmet_flow
for pathway in PATHWAYS:
    mc_results[f"coherence_error_{pathway}"] = (
        mc_results[f"desired_flow_{pathway}"]
        - mc_results[f"flow_{pathway}"]
        - mc_results[f"unmet_flow_{pathway}"]
    ).abs()

# Global coherence: total_desired = total_treated + total_unmet
mc_results["global_coherence_error"] = (
    mc_results["desired_total_flow"]
    - mc_results["total_treated"]
    - mc_results["unmet_flow"]
).abs()

# Flag coherence violations (tolerance: 0.1% of desired flow)
tolerance = mc_results["desired_total_flow"] * 0.001
mc_results["coherence_valid"] = (
    mc_results["global_coherence_error"] <= tolerance
)

# Summary of diagnostics
print("\\n" + "="*60)
print("DIAGNOSTIC SUMMARY")
print("="*60)

print("\\nUnmet flow classification:")
print(mc_results["unmet_flow_diagnosis"].value_counts())

print("\\nAccountancy errors (unmet_flow):")
print(f"  Max error: {mc_results['unmet_flow_accounting_error'].max():.6f}")
print(f"  Invalid rows: {mc_results['unmet_flow_accounting_invalid'].sum()}")

print("\\nGlobal coherence errors:")
print(f"  Max error: {mc_results['global_coherence_error'].max():.6f}")
print(f"  Valid rows: {mc_results['coherence_valid'].sum()} / {len(mc_results)}")

if not mc_results["coherence_valid"].all():
    print("\\n[WARNING] Coherence violations detected:")
    invalid = mc_results[~mc_results["coherence_valid"]]
    print(invalid[["scenario", "year", "global_coherence_error"]].head())

print("\\n" + "="*60)
'''

# Append diagnostic code to cell
source = source + diagnostic_code

# Update cell
if isinstance(cell["source"], list):
    cell["source"] = source.split('\n')
else:
    cell["source"] = source

print(f"  [OK] Added diagnostic classification and balance validation")

# Save
with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "w") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Done! Notebook updated with diagnostics.")
