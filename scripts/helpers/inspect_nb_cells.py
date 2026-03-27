import json
from pathlib import Path

NB_PATH = Path(__file__).resolve().parents[2] / 'notebooks' / 'ThreeC_OneShot_Report.ipynb'
nb = json.loads(NB_PATH.read_text(encoding='utf-8'))

needles = [
    'geom_smooth',
    "method = 'lm'",
    'log2FC_CIS',
    'log2FC_TRANS',
    'geom_col',
]

for i, cell in enumerate(nb.get('cells', []), 1):
    if cell.get('cell_type') != 'code':
        continue
    src = ''.join(cell.get('source', []))
    if any(n in src for n in needles):
        hits = [n for n in needles if n in src]
        print(f'Cell {i}: hits={hits} chars={len(src)}')
        for line in src.splitlines():
            if 'geom_smooth' in line or "method = 'lm'" in line or 'log2FC_' in line:
                print('   ', line[:200])
        print('---')
