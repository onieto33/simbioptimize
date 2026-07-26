import json

with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r") as f:
    nb = json.load(f)

# Search for ABMLayer and recycler creation
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        
        if "class ABMLayer" in source:
            print(f"ABMLayer class at cell index {i}")
            # Print first 500 chars
            print(source[:1000])
            print("\n" + "="*60 + "\n")
            
        if "create_recycler" in source.lower():
            print(f"Recycler creation at cell index {i}")
            print(source[:500])
            print("\n" + "="*60 + "\n")
