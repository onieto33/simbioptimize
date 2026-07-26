import json

with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r") as f:
    nb = json.load(f)

# Verify recycler init uses INITIAL_PATHWAY_SHARES
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        
        if "_initialize_recycler_population" in source:
            print(f"Recycler init at cell {i}:")
            # Find the technologies section
            start = source.find("incumbent_technologies")
            end = source.find("technologies = self.rng.choice", start)
            
            section = source[start:end]
            print(section)
            
            # Check if INITIAL_PATHWAY_SHARES is mentioned
            if "INITIAL_PATHWAY_SHARES" in section:
                print("\n[OK] Using INITIAL_PATHWAY_SHARES!")
            else:
                print("\n[ERROR] Not using INITIAL_PATHWAY_SHARES")
            break
