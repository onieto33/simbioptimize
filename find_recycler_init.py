import json

with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r") as f:
    nb = json.load(f)

# Find where recyclers are created
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        
        # Look for recycler population initialization
        if "self.recyclers" in source and "rng" in source:
            print(f"Found recycler init at cell {i}")
            print(source[source.find("self.recyclers"):source.find("self.recyclers")+2000])
            break
