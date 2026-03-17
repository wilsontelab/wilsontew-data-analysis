#!/usr/bin/env python3
"""
Fix: Remove problematic backslash escapes in cell 19
"""
import json

notebook_path = r"c:\Users\dunnmk\wilsontew-data-analysis\FourC_OneShot_Python_Report.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Get cell 19 (index 18)
cell = nb['cells'][18]
source_list = cell['source']

# Fix each line - convert them back to proper strings
fixed_list = []
for line in source_list:
    if isinstance(line, str):
        line = line.replace('\\"', '"')
    fixed_list.append(line)

cell['source'] = fixed_list

# Write back
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Fixed cell 19")
