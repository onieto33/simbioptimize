import json

with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r") as f:
    nb = json.load(f)

# Find validation/diagnostics cells
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        
        # Look for validation/balance checks
        if any(x in source for x in ["assert", "balance", "unmet_flow"]):
            if len(source) > 200:  # Skip trivial cells
                print(f"Cell {i}: {source[:150]}...")
                print()
