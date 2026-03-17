import json

with open('FourC_OneShot_Python_Report.ipynb', 'r') as f:
    nb = json.load(f)

# Get cell 23 (0-indexed)
cell = nb['cells'][23]
source = ''.join(cell['source'])
print(source)
