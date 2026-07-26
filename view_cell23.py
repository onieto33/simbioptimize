import json

with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r") as f:
    nb = json.load(f)

# Get cell 23
cell_23 = nb["cells"][23]
if cell_23["cell_type"] == "code":
    source = "".join(cell_23["source"]) if isinstance(cell_23["source"], list) else cell_23["source"]
    print("CELL 23 CONTENT:")
    print("="*60)
    print(source)
