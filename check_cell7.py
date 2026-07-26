import json

with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

# Get cell 7
cell_7 = nb["cells"][7]
source = "".join(cell_7["source"]) if isinstance(cell_7["source"], list) else cell_7["source"]

# Find the problematic area
if "initial_technology_probabilities" in source:
    start = source.find("initial_technology_probabilities")
    end = source.find("technologies = self.rng.choice", start)
    
    section = source[start:end]
    print("Problematic section:")
    print(section[:500])
