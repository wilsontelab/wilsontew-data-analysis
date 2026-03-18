from __future__ import annotations

import json
import sys
from pathlib import Path


def clear_outputs(notebook_path: Path) -> int:
    nb = json.loads(notebook_path.read_text(encoding="utf-8"))
    changed = 0
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            if cell.get("outputs") or cell.get("execution_count") is not None:
                changed += 1
            cell["outputs"] = []
            cell["execution_count"] = None
    notebook_path.write_text(
        json.dumps(nb, indent=1, ensure_ascii=False),
        encoding="utf-8",
    )
    return changed


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python clear_notebook_outputs.py <notebook_path>"
        )

    path = Path(sys.argv[1]).resolve()
    changed_cells = clear_outputs(path)
    print(
        f"Cleared outputs in {path.name}; "
        f"updated {changed_cells} code cell(s)."
    )
