import json

with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r") as f:
    nb = json.load(f)

# Find INITIAL_PATHWAY_SHARES
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        
        if "INITIAL_PATHWAY_SHARES" in source:
            print(f"Found at cell {i}")
            # Find the dictionary and print
            start = source.find("INITIAL_PATHWAY_SHARES")
            end = source.find("}", start) + 1
            
            shares_def = source[start:end]
            print(shares_def)
            print("\n" + "="*60)
            
        if "RESOURCE_RECOVERY_PATHWAYS" in source:
            print(f"RESOURCE_RECOVERY_PATHWAYS at cell {i}:")
            start = source.find("RESOURCE_RECOVERY_PATHWAYS")
            end = source.find(")", start) + 1
            recovery_def = source[start:end]
            print(recovery_def)
