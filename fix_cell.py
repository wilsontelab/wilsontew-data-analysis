import json
import re

notebook_path = r"c:\Users\dunnmk\wilsontew-data-analysis\FourC_OneShot_Python_Report.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Get cell 19 (index 18)
cell = nb['cells'][18]
source = cell['source']

# Fix the cell source by removing problematic backslashes
fixed_source = []
for line in source:
    # Replace \\\" with just \"
    fixed_line = line.replace('\\\"', '"')
    fixed_source.append(fixed_line)

cell['source'] = fixed_source

# Write the notebook back
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Fixed escape sequences in cell 19")
