#!/usr/bin/env python
"""
Simple text-based refactoring (no regex, no split issues).
"""
import json

print("Loading notebook...")
with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

# FIX 1: Cell 8 - Manufacturer adoption + 50% floor
print("\nFix 1: Cell 8 (manufacturer adoption)...")
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        
        if "class WTBHybridModel" in source:
            print(f"  Found at index {i}")
            
            # Simple string replacement - manufacturer adoption
            if '"manufacturer_adoption_probability",' in source:
                source = source.replace(
                    '"manufacturer_adoption_probability",\n        }',
                    '"manufacturer_adoption_probability",\n            "manufacturer_realized_adoption_share",\n        }'
                )
            
            # Remove 50% floor
            if "max(0.50 * current_capacity," in source:
                source = source.replace(
                    "max(0.50 * current_capacity,",
                    "max(0.0 * current_capacity,"
                )
            
            # Keep as single string, don't split
            cell["source"] = source
            print("    [OK] Applied")
            break

# FIX 2: Cell 22 - N_RUNS
print("\nFix 2: Cell 22 (N_RUNS)...")
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        
        if "N_RUNS" in source and "monte" in source.lower():
            print(f"  Found at index {i}")
            
            if "N_RUNS = 30" in source:
                source = source.replace("N_RUNS = 30", "N_RUNS = 500")
            
            cell["source"] = source
            print("    [OK] Applied")
            break

# FIX 3: Cell 7 - INITIAL_PATHWAY_SHARES (simple version)
print("\nFix 3: Cell 7 (recycler init)...")
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        
        if "_initialize_recycler_population" in source:
            print(f"  Found at index {i}")
            
            # Simple replacement of probabilities
            old_probs = "initial_technology_probabilities = np.array([\n            0.45,\n            0.15,\n            0.40,\n        ])"
            
            new_probs = """initial_technology_probabilities = np.array([
            0.376,  # mechanical_recycling from INITIAL_PATHWAY_SHARES
            0.020,  # pyrolysis from INITIAL_PATHWAY_SHARES  
            0.544,  # recovery from INITIAL_PATHWAY_SHARES
        ])"""
            
            if old_probs in source:
                source = source.replace(old_probs, new_probs)
                print("    [OK] Applied")
            else:
                print("    [SKIP] Pattern not found")
            
            cell["source"] = source
            break

# Save
print("\nSaving notebook...")
with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("\nAll fixes applied!")
