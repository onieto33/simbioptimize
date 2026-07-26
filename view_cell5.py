import json

with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r") as f:
    nb = json.load(f)

# Get cell 5 (recycler creation)
cell_5 = nb["cells"][5]
if cell_5["cell_type"] == "code":
    source = "".join(cell_5["source"]) if isinstance(cell_5["source"], list) else cell_5["source"]
    print(source[:5000])
