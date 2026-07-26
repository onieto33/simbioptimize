import json

with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

# Find where results are stored after run_all_scenarios
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        
        if "run_all_scenarios" in source and "=" in source:
            # Find the assignment
            lines = source.split('\n')
            for line in lines:
                if "run_all_scenarios" in line and "=" in line:
                    print(f"Cell {i}: {line}")
        
        if "results" in source.lower() and "shape" in source.lower():
            print(f"Cell {i} has results analysis: {source[:200]}")
