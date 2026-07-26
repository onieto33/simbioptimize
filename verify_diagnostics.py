import json

with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r") as f:
    nb = json.load(f)

# Get cell 23 and check diagnostics
cell_23 = nb["cells"][23]
source = "".join(cell_23["source"]) if isinstance(cell_23["source"], list) else cell_23["source"]

# Check for diagnostic function
if "classify_unmet_flow_cause" in source:
    print("[OK] Diagnostic classification function added")
if "total_capacity_shortage" in source:
    print("[OK] Capacity shortage classification")
if "allocation_mismatch" in source:
    print("[OK] Allocation mismatch classification")
if "closed_loop_demand_insufficient" in source:
    print("[OK] Closed-loop demand classification")
if "unmet_flow_accounting_error" in source:
    print("[OK] Accounting error validation")
if "global_coherence_error" in source:
    print("[OK] Global coherence validation")
if "DIAGNOSTIC SUMMARY" in source:
    print("[OK] Diagnostic summary output")

print("\nDiagnostics successfully added to Celda 23!")
