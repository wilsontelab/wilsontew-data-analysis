import json
from pathlib import Path

NOTEBOOK_PATH = Path(__file__).resolve().parents[2] / 'notebooks' / 'FourC_OneShot_Python_Report.ipynb'

with open(NOTEBOOK_PATH, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Get cell 23 (0-indexed)
cell = nb['cells'][23]
source = ''.join(cell['source'])
print(source)
