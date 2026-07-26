import json

with open("HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb", "r") as f:
    nb = json.load(f)

# Find the full _initialize_recycler_population method
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        
        if "_initialize_recycler_population" in source:
            print(f"Found at cell {i}")
            # Find the method and print everything until next def or class
            start = source.find("def _initialize_recycler_population")
            if start != -1:
                end = source.find("\n    def ", start + 1)
                if end == -1:
                    end = source.find("\nclass ", start + 1)
                if end == -1:
                    end = len(source)
                
                method = source[start:end]
                print(method[:3000])
            break
