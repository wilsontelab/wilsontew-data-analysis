import json

notebook_path = r"c:\Users\dunnmk\wilsontew-data-analysis\FourC_OneShot_Python_Report.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"Total cells: {len(nb['cells'])}\n")
print("All cell IDs:")
for i, cell in enumerate(nb['cells']):
    cell_id = cell.get('id', 'NO_ID')
    cell_type = cell.get('cell_type', 'unknown')
    print(f"{i}: {cell_id} ({cell_type})")

print("\nLooking for AS-stratified cell...")
for i, cell in enumerate(nb['cells']):
    if cell.get('cell_type') == 'code':
        sources = cell.get('source', [])
        source_text = ''.join(sources) if isinstance(sources, list) else str(sources)
        if 'Quality-stratified' in source_text or 'AS_stratified' in source_text:
            print(f"Found at index {i}: {cell.get('id')}")
            print(f"First 100 chars: {source_text[:100]}")
