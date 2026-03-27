#!/usr/bin/env python3
"""
Clean up the notebook - remove duplicate/problematic cells
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
notebook_path = ROOT / "notebooks" / "FourC_OneShot_Python_Report.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"Total cells before cleanup: {len(nb['cells'])}")

# Find and keep only one Q1-filtered cell (the good one from rebuild_cell.py)
cells_to_keep = []
found_filtered_cell = False

for i, cell in enumerate(nb['cells']):
    if cell.get('id') == '#VSC-60855c4c':
        # This is our target filtered cell
        if found_filtered_cell:
            # Skip duplicate
            print(f"Skipping duplicate Q1-filtered cell at index {i}")
            continue
        else:
            found_filtered_cell = True
            cells_to_keep.append(cell)
    else:
        cells_to_keep.append(cell)

nb['cells'] = cells_to_keep
print(f"Total cells after cleanup: {len(nb['cells'])}")

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Cleanup complete")
