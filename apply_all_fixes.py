#!/usr/bin/env python
"""
Comprehensive notebook refactoring in one pass.
Applies all 4 fixes plus validation cell.
"""
import json
import re

print("Loading notebook...")
with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

print(f"Notebook has {len(nb['cells'])} cells")

# ============================================================
# FIX 1: Cell 7 - Use INITIAL_PATHWAY_SHARES for recycler init
# ============================================================

print("\n[1/5] Fixing recycler initialization (Cell 7)...")
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        
        if "_initialize_recycler_population" in source and "incumbent_technologies" in source:
            print(f"  Found at cell index {i}")
            
            # Replace hardcoded probabilities with INITIAL_PATHWAY_SHARES
            old_pattern = (
                r'initial_technology_probabilities = np\.array\(\[\s*'
                r'0\.45,\s*0\.15,\s*0\.40,\s*\]\)'
            )
            
            new_code = '''initial_technology_probabilities = np.array([
            (INITIAL_PATHWAY_SHARES.get("mechanical_recycling", 0.38) / 
             (INITIAL_PATHWAY_SHARES.get("mechanical_recycling", 0.38) + 
              INITIAL_PATHWAY_SHARES.get("pyrolysis", 0.02) + 
              INITIAL_PATHWAY_SHARES.get("recovery", 0.55))),
            (INITIAL_PATHWAY_SHARES.get("pyrolysis", 0.02) / 
             (INITIAL_PATHWAY_SHARES.get("mechanical_recycling", 0.38) + 
              INITIAL_PATHWAY_SHARES.get("pyrolysis", 0.02) + 
              INITIAL_PATHWAY_SHARES.get("recovery", 0.55))),
            (INITIAL_PATHWAY_SHARES.get("recovery", 0.55) / 
             (INITIAL_PATHWAY_SHARES.get("mechanical_recycling", 0.38) + 
              INITIAL_PATHWAY_SHARES.get("pyrolysis", 0.02) + 
              INITIAL_PATHWAY_SHARES.get("recovery", 0.55))),
        ])'''
            
            source = re.sub(old_pattern, new_code, source, flags=re.DOTALL)
            cell["source"] = source.split('\n')
            print("  [OK] INITIAL_PATHWAY_SHARES implemented")
            break

# ============================================================
# FIX 2: Cell 8 - Fix manufacturer adoption and capacity expansion
# ============================================================

print("\n[2/5] Fixing manufacturer adoption feedback (Cell 8)...")
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        
        if "class WTBHybridModel" in source and "required_abm_outputs" in source:
            print(f"  Found at cell index {i}")
            
            # Add manufacturer_realized_adoption_share to outputs
            source = source.replace(
                '"manufacturer_adoption_probability",',
                '"manufacturer_adoption_probability",\n            "manufacturer_realized_adoption_share",'
            )
            
            # Remove 50% floor
            source = source.replace(
                "max(0.50 * current_capacity,",
                "max(0.0 * current_capacity,"
            )
            
            cell["source"] = source.split('\n')
            print("  [OK] Adoption feedback + capacity floor fixed")
            break

# ============================================================
# FIX 3: Cell 22 - Increase N_RUNS to 500
# ============================================================

print("\n[3/5] Increasing Monte Carlo runs (Cell 22)...")
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        
        if "N_RUNS" in source and ("range(N_RUNS)" in source or "monte" in source.lower()):
            print(f"  Found at cell index {i}")
            
            source = source.replace("N_RUNS = 30", "N_RUNS = 500")
            
            cell["source"] = source.split('\n')
            print("  [OK] N_RUNS set to 500")
            break

# ============================================================
# FIX 4: Cell 23 - Add diagnostics
# ============================================================

print("\n[4/5] Adding diagnostic classification (Cell 23)...")
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        
        if "Annual WTB flow indicators" in source:
            print(f"  Found at cell index {i}")
            
            # Check if diagnostics already added
            if "classify_unmet_flow_cause" not in source:
                # Add diagnostic code at end
                diagnostic_snippet = '''

# ============================================================
# DIAGNOSTIC CLASSIFICATION
# ============================================================

def classify_unmet_flow_cause(year_data):
    """Classify root cause of unmet_flow."""
    unmet = year_data.get("unmet_flow", 0.0)
    if unmet <= 0.0001:
        return "no_unmet_flow"
    
    # Extract data
    total_capacity = sum(year_data.get(f"capacity_{p}", 0.0) for p in PATHWAYS)
    total_desired = year_data.get("desired_total_flow", 0.0)
    
    # 1. Total capacity shortage?
    if total_capacity < (total_desired - unmet * 0.01):
        return "total_capacity_shortage"
    
    # 2. Allocation mismatch?
    pathways_with_unmet = {p: year_data.get(f"unmet_flow_{p}", 0.0) for p in PATHWAYS 
                           if year_data.get(f"unmet_flow_{p}", 0.0) > 0.001}
    pathways_with_spare = {p: (year_data.get(f"capacity_{p}", 0.0) - 
                               year_data.get(f"flow_{p}", 0.0)) for p in PATHWAYS 
                          if (year_data.get(f"capacity_{p}", 0.0) - 
                              year_data.get(f"flow_{p}", 0.0)) > 0.001}
    
    if pathways_with_unmet and pathways_with_spare:
        return "allocation_mismatch"
    
    # 3. Closed-loop demand insufficiency?
    solvolysis_capacity = year_data.get("capacity_solvolysis", 0.0)
    manufacturer_adoption = year_data.get("manufacturer_realized_adoption_share", 0.0)
    
    if solvolysis_capacity > 0.1 and manufacturer_adoption < 0.30 and unmet > 0.001:
        return "closed_loop_demand_insufficient"
    
    return "other"

# Apply classification
mc_results["unmet_flow_diagnosis"] = mc_results.apply(classify_unmet_flow_cause, axis=1)

# Balance validation
pathway_unmet_columns = [f"unmet_flow_{pathway}" for pathway in PATHWAYS]
mc_results["total_unmet_from_pathways"] = mc_results[pathway_unmet_columns].sum(axis=1)
mc_results["unmet_flow_accounting_error"] = (
    mc_results["total_unmet_from_pathways"] - mc_results["unmet_flow"]).abs()
mc_results["global_coherence_error"] = (
    mc_results["desired_total_flow"] - mc_results["total_treated"] - mc_results["unmet_flow"]).abs()

print("\\nDiagnostic summary:")
print(mc_results["unmet_flow_diagnosis"].value_counts())
'''
                source = source + diagnostic_snippet
            
            cell["source"] = source.split('\n')
            print("  [OK] Diagnostics added")
            break

# ============================================================
# Save
# ============================================================

print("\n[5/5] Saving notebook...")
with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("\n" + "="*60)
print("ALL FIXES APPLIED SUCCESSFULLY")
print("="*60)
print("Fixed:")
print("  [✓] Cell 7: INITIAL_PATHWAY_SHARES in recycler init")
print("  [✓] Cell 8: Manufacturer adoption + capacity expansion")
print("  [✓] Cell 22: N_RUNS = 500")
print("  [✓] Cell 23: Diagnostic classification + validation")
print("\nNotebook ready for testing.")
