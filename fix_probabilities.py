#!/usr/bin/env python
"""
Fix probability normalization.

mechanical_recycling: 0.38 / (0.38 + 0.02 + 0.55) = 0.38 / 0.95 = 0.40000
pyrolysis: 0.02 / 0.95 = 0.02105
recovery: 0.55 / 0.95 = 0.57895
"""
import json

print("Calculating normalized probabilities...")
total = 0.38 + 0.02 + 0.55
p_mech = 0.38 / total
p_pyro = 0.02 / total
p_recov = 0.55 / total

print(f"mechanical_recycling: {p_mech:.6f}")
print(f"pyrolysis: {p_pyro:.6f}")
print(f"recovery: {p_recov:.6f}")
print(f"Sum: {p_mech + p_pyro + p_recov:.6f}")

print("\nUpdating notebook...")
with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

# Fix Cell 7
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        
        if "_initialize_recycler_population" in source:
            print(f"Found at index {i}")
            
            # Replace old probabilities
            old = """initial_technology_probabilities = np.array([
            0.376,  # mechanical_recycling from INITIAL_PATHWAY_SHARES
            0.020,  # pyrolysis from INITIAL_PATHWAY_SHARES  
            0.544,  # recovery from INITIAL_PATHWAY_SHARES
        ])"""
            
            new = f"""initial_technology_probabilities = np.array([
            {p_mech:.5f},  # mechanical_recycling: 0.38/(0.38+0.02+0.55)
            {p_pyro:.5f},  # pyrolysis: 0.02/(0.38+0.02+0.55)
            {p_recov:.5f},  # recovery: 0.55/(0.38+0.02+0.55)
        ])"""
            
            if old in source:
                source = source.replace(old, new)
                cell["source"] = source
                print("Updated probabilities")
            else:
                print("Pattern not found - checking current content...")
                if "initial_technology_probabilities" in source:
                    print("Found probabilities section, manual inspection needed")
            
            break

with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Done!")
