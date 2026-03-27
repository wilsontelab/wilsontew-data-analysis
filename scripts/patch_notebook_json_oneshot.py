#!/usr/bin/env python3
"""
One-shot notebook JSON patch + canonicalization sweep.

What it does:
1) Replaces the Q1-filtered analysis cell in FourC_OneShot_Python_Report.ipynb
   with code from run_filtered_analysis.py.
2) Canonicalizes every cell with:
   - metadata.id
   - metadata.language
   while preserving top-level cell id for Jupyter compatibility.
3) Writes deterministic JSON formatting for stable diffs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TARGET_NOTEBOOK = ROOT / "FourC_OneShot_Python_Report.ipynb"
FILTERED_SOURCE_SCRIPT = ROOT / "run_filtered_analysis.py"


def _line_list(text: str) -> list[str]:
    """Return Jupyter-style source list preserving newline endings."""
    if not text:
        return []
    return text.splitlines(keepends=True)


def _normalize_source(cell: dict[str, Any]) -> None:
    src = cell.get("source", [])
    if isinstance(src, str):
        cell["source"] = _line_list(src)
        return
    if isinstance(src, list):
        normalized: list[str] = []
        for item in src:
            if item is None:
                continue
            s = str(item)
            normalized.append(s)
        cell["source"] = normalized
        return
    cell["source"] = _line_list(str(src))


def _canonical_id_for_cell(cell: dict[str, Any], idx: int) -> str:
    explicit = cell.get("id")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()

    meta = cell.get("metadata")
    if isinstance(meta, dict):
        mid = meta.get("id")
        if isinstance(mid, str) and mid.strip():
            return mid.strip()

    if isinstance(cell.get("source"), list):
        src_joined = "".join(cell.get("source", []))
    else:
        src_joined = str(cell.get("source", ""))

    digest = hashlib.sha1(
        src_joined.encode("utf-8", errors="replace")
    ).hexdigest()[:8]
    return f"cell-{idx + 1:03d}-{digest}"


def _canonical_language(cell: dict[str, Any]) -> str:
    ctype = str(cell.get("cell_type", "")).strip().lower()
    if ctype == "markdown":
        return "markdown"
    if ctype == "code":
        return "python"

    meta = cell.get("metadata")
    if isinstance(meta, dict):
        lang = meta.get("language")
        if isinstance(lang, str) and lang.strip():
            return lang.strip().lower()
    return "text"


def _canonicalize_cells(nb: dict[str, Any]) -> dict[str, int]:
    changed = 0
    total = 0
    for idx, cell in enumerate(nb.get("cells", [])):
        total += 1
        before = json.dumps(cell, sort_keys=True, ensure_ascii=False)

        if not isinstance(cell.get("metadata"), dict):
            cell["metadata"] = {}

        _normalize_source(cell)

        cid = _canonical_id_for_cell(cell, idx)
        cell["id"] = cid
        cell["metadata"]["id"] = cid
        cell["metadata"]["language"] = _canonical_language(cell)

        if cell.get("cell_type") == "code":
            if (
                "outputs" not in cell
                or not isinstance(cell.get("outputs"), list)
            ):
                cell["outputs"] = []
            if "execution_count" not in cell:
                cell["execution_count"] = None

        after = json.dumps(cell, sort_keys=True, ensure_ascii=False)
        if before != after:
            changed += 1

    return {"changed_cells": changed, "total_cells": total}


def _is_filtered_analysis_cell(cell: dict[str, Any]) -> bool:
    if cell.get("cell_type") != "code":
        return False
    source = cell.get("source", [])
    text = "".join(source) if isinstance(source, list) else str(source)
    return "FILTERED ANALYSIS: Excluding Q1" in text


def _patch_filtered_cell(
    nb: dict[str, Any],
    replacement_source: list[str],
) -> bool:
    for cell in nb.get("cells", []):
        if _is_filtered_analysis_cell(cell):
            cell["source"] = replacement_source
            cell["execution_count"] = None
            cell["outputs"] = []
            return True
    return False


def _fix_mojibake(nb: dict[str, Any]) -> int:
    """Fix common UTF-8 mojibake remnants in markdown/code source."""
    fixes = {
        "â€”": "—",
        "â€“": "–",
        "â€˜": "‘",
        "â€™": "’",
        "â€œ": "“",
        "â€": "”",
    }
    changed = 0
    for cell in nb.get("cells", []):
        src = cell.get("source", [])
        if not isinstance(src, list):
            continue
        new_src: list[str] = []
        local_change = False
        for line in src:
            original = str(line)
            fixed = original
            for bad, good in fixes.items():
                fixed = fixed.replace(bad, good)
            new_src.append(fixed)
            if fixed != original:
                local_change = True
        if local_change:
            cell["source"] = new_src
            changed += 1
    return changed


def _collect_notebooks_all() -> list[Path]:
    notebooks: list[Path] = []
    for p in sorted(ROOT.rglob("*.ipynb")):
        if ".ipynb_checkpoints" in p.parts:
            continue
        notebooks.append(p)
    return notebooks


def _process_notebook(
    notebook_path: Path,
    replacement_source: list[str] | None,
) -> dict[str, Any]:
    try:
        with notebook_path.open("r", encoding="utf-8") as f:
            nb = json.load(f)
    except json.JSONDecodeError as ex:
        return {
            "path": notebook_path,
            "changed": False,
            "patched": False,
            "mojibake_fixed_cells": 0,
            "changed_cells": 0,
            "total_cells": 0,
            "skipped": True,
            "skip_reason": f"invalid JSON: {ex}",
        }

    patched = False
    if (
        replacement_source is not None
        and notebook_path.resolve() == TARGET_NOTEBOOK.resolve()
    ):
        patched = _patch_filtered_cell(nb, replacement_source)

    mojibake_fixed_cells = _fix_mojibake(nb)
    stats = _canonicalize_cells(nb)

    changed = (
        patched
        or mojibake_fixed_cells > 0
        or stats["changed_cells"] > 0
    )

    if changed:
        with notebook_path.open("w", encoding="utf-8", newline="\n") as f:
            json.dump(nb, f, indent=1, ensure_ascii=False)
            f.write("\n")

    return {
        "path": notebook_path,
        "changed": changed,
        "patched": patched,
        "mojibake_fixed_cells": mojibake_fixed_cells,
        "changed_cells": stats["changed_cells"],
        "total_cells": stats["total_cells"],
        "skipped": False,
        "skip_reason": "",
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Patch and canonicalize notebook JSON files."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Sweep all notebooks in the repository.",
    )
    return parser.parse_args()


def run() -> None:
    args = _parse_args()

    if not FILTERED_SOURCE_SCRIPT.exists():
        raise FileNotFoundError(
            "Replacement source script not found: "
            f"{FILTERED_SOURCE_SCRIPT}"
        )

    replacement_source = _line_list(
        FILTERED_SOURCE_SCRIPT.read_text(encoding="utf-8")
    )

    if args.all:
        notebooks = _collect_notebooks_all()
    else:
        if not TARGET_NOTEBOOK.exists():
            raise FileNotFoundError(
                f"Notebook not found: {TARGET_NOTEBOOK}"
            )
        notebooks = [TARGET_NOTEBOOK]

    results: list[dict[str, Any]] = []
    for nb_path in notebooks:
        results.append(
            _process_notebook(
                notebook_path=nb_path,
                replacement_source=replacement_source,
            )
        )

    changed = [r for r in results if r["changed"]]
    skipped = [r for r in results if r.get("skipped")]
    total_changed_cells = sum(int(r["changed_cells"]) for r in results)
    total_cells = sum(int(r["total_cells"]) for r in results)
    total_mojibake = sum(int(r["mojibake_fixed_cells"]) for r in results)
    patched_targets = [r for r in results if r["patched"]]

    mode = "repo-wide sweep" if args.all else "single-notebook"
    print("=== Notebook patch complete ===")
    print(f"Mode: {mode}")
    print(f"Notebooks scanned: {len(results)}")
    print(f"Notebooks changed: {len(changed)}")
    print(f"Notebooks skipped: {len(skipped)}")
    print(f"Cells with mojibake fixes: {total_mojibake}")
    print(
        f"Canonicalized cells: {total_changed_cells} / "
        f"{total_cells}"
    )
    print(
        "Filtered analysis cell patched: "
        f"{'yes' if len(patched_targets) > 0 else 'no'}"
    )

    if changed:
        print("Changed notebook files:")
        for entry in changed:
            rel = Path(entry["path"]).resolve().relative_to(ROOT.resolve())
            print(f" - {rel}")

    if skipped:
        print("Skipped notebook files:")
        for entry in skipped:
            rel = Path(entry["path"]).resolve().relative_to(ROOT.resolve())
            print(f" - {rel} ({entry['skip_reason']})")


if __name__ == "__main__":
    run()
