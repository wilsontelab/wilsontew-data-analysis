#!/usr/bin/env python3
"""
Clean up all instances of bad escape sequences in the notebook
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
notebook_path = ROOT / "notebooks" / "FourC_OneShot_Python_Report.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace 'f\"{...}\"' with 'f\'{...}\''
# This fixes escaped double quotes in f-strings
content = content.replace('f\\"', "f'")
content = content.replace('\\"', "'")

with open(notebook_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Cleaned up escape sequences")
