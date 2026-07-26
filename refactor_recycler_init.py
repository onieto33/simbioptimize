#!/usr/bin/env python
"""
Refactor: Use INITIAL_PATHWAY_SHARES to initialize recycler population.

Instead of hardcoded initial_technology_probabilities, use INITIAL_PATHWAY_SHARES
for technologies that recyclers can operate (mechanical_recycling, pyrolysis, recovery, solvolysis).
"""
import json

with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r") as f:
    nb = json.load(f)

# Find and modify cell 7 (ABMLayer)
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        
        if "_initialize_recycler_population" in source:
            print(f"Found recycler init at cell {i}")
            
            # Old code:
            old_code = '''        incumbent_technologies = np.array([
            "mechanical_recycling",
            "pyrolysis",
            "recovery",
        ])

        initial_technology_probabilities = np.array([
            0.45,
            0.15,
            0.40,
        ])'''
            
            # New code using INITIAL_PATHWAY_SHARES
            new_code = '''        # Recycler technologies from INITIAL_PATHWAY_SHARES
        # (excluding reuse/repurposing which are operator-level, and solvolysis which starts at 0)
        incumbent_technologies = np.array([
            "mechanical_recycling",
            "pyrolysis",
            "recovery",
        ])
        
        # Extract initial shares and normalize to sum to 1.0
        # (excluding reuse/repurposing which are not recycler technologies)
        recycler_capable_pathways = {
            "mechanical_recycling": INITIAL_PATHWAY_SHARES.get("mechanical_recycling", 0.38),
            "pyrolysis": INITIAL_PATHWAY_SHARES.get("pyrolysis", 0.02),
            "recovery": INITIAL_PATHWAY_SHARES.get("recovery", 0.55),
        }
        
        total_share = sum(recycler_capable_pathways.values())
        initial_technology_probabilities = np.array([
            recycler_capable_pathways["mechanical_recycling"] / total_share,
            recycler_capable_pathways["pyrolysis"] / total_share,
            recycler_capable_pathways["recovery"] / total_share,
        ])'''
            
            # Replace in source
            source = source.replace(old_code, new_code)
            
            # Update cell
            if isinstance(cell["source"], list):
                cell["source"] = source.split('\n')
            else:
                cell["source"] = source
            
            print("  [OK] Updated to use INITIAL_PATHWAY_SHARES")
            break

# Save
with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "w") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Done! Notebook updated.")
