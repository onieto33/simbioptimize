import json
nb = json.load(open('HybridpaperV2_TFSC_realistic_recycler_adoption.ipynb'))
print(f'Cells: {len(nb["cells"])}')
print('Notebook valid!')
