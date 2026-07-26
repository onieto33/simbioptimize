import json

with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r") as f:
    nb = json.load(f)

# Search for key markers
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        
        if "N_RECYCLERS" in source and "INITIAL_PATHWAY_SHARES" in source:
            print(f"Celda 3 (params): idx={i}")
        
        if "def run_monte_carlo" in source or ("N_RUNS" in source and "range(N_RUNS)" in source):
            print(f"Celda 22 (MC runner): idx={i}, has N_RUNS={('N_RUNS' in source)}")
            
        if "unmet_flow" in source and ("assert" in source or "balance" in source):
            print(f"Celda 23 (validation): idx={i}")
            
        if "pathway_flow_balance" in source or "wtb_stock_balance" in source:
            print(f"Celda 23 validation functions: idx={i}")
