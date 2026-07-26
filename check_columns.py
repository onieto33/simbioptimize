#!/usr/bin/env python
"""
Check available columns in results.
"""
import json
import pandas as pd

print("Loading notebook...")
with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

code = ""
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        if "!pip" not in source:
            code += source + "\n"

namespace = {}
try:
    exec(code, namespace)
except NameError as e:
    # display() is Jupyter-specific, ignore
    if "display" in str(e):
        pass
    else:
        raise
except Exception as e:
    pass
results = namespace["results"]

print(f"\nColumns in results ({len(results.columns)} total):")
for i, col in enumerate(results.columns, 1):
    print(f"  {i:3}. {col}")

print(f"\nShape: {results.shape}")
print(f"Scenarios: {results['scenario'].unique() if 'scenario' in results else 'N/A'}")
print(f"Years: {results['year'].min()}-{results['year'].max() if 'year' in results else 'N/A'}")
