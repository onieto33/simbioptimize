#!/usr/bin/env python
"""
Refactor notebook cells 3, 8, 22, 23 according to plan.
"""
import json

with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r") as f:
    nb = json.load(f)

# ============================================================
# REFACTOR CELL 3: Parameters
# Keep INITIAL_PATHWAY_SHARES as-is (used in recycler initialization)
# ============================================================

cell_3_found = False
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        if "N_RECYCLERS" in source and "INITIAL_PATHWAY_SHARES" in source:
            cell_3_found = True
            print(f"Celda 3 confirmed at idx={i}")
            break

# ============================================================
# REFACTOR CELL 8: Hybrid Model
# ============================================================

cell_8_idx = None
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        if "class WTBHybridModel" in source:
            cell_8_idx = i
            print(f"Celda 8 found at idx={i}")
            
            # Convert to string
            source_list = cell["source"] if isinstance(cell["source"], list) else [cell["source"]]
            source_str = "".join(source_list)
            
            # Fix 1: Add to required outputs
            if '"manufacturer_adoption_probability",' in source_str:
                source_str = source_str.replace(
                    '"manufacturer_adoption_probability",',
                    '"manufacturer_adoption_probability",\n            "manufacturer_realized_adoption_share",'
                )
            
            # Fix 2: Remove 50% floor
            source_str = source_str.replace(
                "max(0.50 * current_capacity,",
                "max(0.0 * current_capacity,"
            )
            
            # Update
            cell["source"] = source_str.split('\n')
            print("  Fixed manufacturer adoption + capacity expansion")
            break

# ============================================================
# REFACTOR CELL 22: Monte Carlo
# ============================================================

cell_22_idx = None
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        if "N_RUNS" in source and ("range(N_RUNS)" in source or "monte" in source.lower()):
            cell_22_idx = i
            print(f"Celda 22 found at idx={i}")
            
            source_list = cell["source"] if isinstance(cell["source"], list) else [cell["source"]]
            source_str = "".join(source_list)
            
            # Change N_RUNS
            source_str = source_str.replace("N_RUNS = 30", "N_RUNS = 500")
            
            cell["source"] = source_str.split('\n')
            print("  Changed N_RUNS to 500")
            break

print("\nNotebook updated. Saving...")
with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "w") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Done!")
