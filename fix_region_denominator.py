import json
from pathlib import Path

NB_PATH = Path(__file__).resolve().parent / "ThreeC_OneShot_Report.ipynb"
MARKER = "# ---- Batch-wise CIS/TRANS locus frequencies + region broken/unbroken comparisons (T0 vs T120) ----"

REPLACEMENT_BLOCK = [
    "region_summary <- df_loc %>%\n",
    "  dplyr::filter(!is.na(pair_class), pair_class %in% c('CIS', 'TRANS')) %>%\n",
    "  dplyr::group_by(batch, pair_class, broken_status, region_class, time_point, time_label) %>%\n",
    "  dplyr::summarise(count_sum = sum(count, na.rm = TRUE), .groups = 'drop') %>%\n",
    "  # Denominator is (starting + repaired) = (T0 + T120) within each region grouping\n",
    "  dplyr::group_by(batch, pair_class, broken_status, region_class) %>%\n",
    "  dplyr::mutate(\n",
    "    denom = sum(count_sum, na.rm = TRUE),\n",
    "    pct_intact_repaired = ifelse(denom > 0, 100 * count_sum / denom, NA_real_)\n",
    "  ) %>%\n",
    "  dplyr::ungroup() %>%\n",
    "  dplyr::select(-denom)\n",
]


def patch_cell_source(src: list[str]) -> list[str]:
    out: list[str] = []

    i = 0
    while i < len(src):
        line = src[i]

        if line.strip() == "region_summary <- df_loc %>%":
            # Find the end of the existing region_summary pipeline.
            j = i + 1
            while j < len(src):
                if src[j].strip() == "dplyr::ungroup()":
                    break
                j += 1
            if j >= len(src):
                raise RuntimeError("Could not find end of region_summary block (dplyr::ungroup())")

            out.extend(REPLACEMENT_BLOCK)
            # Skip the old block INCLUDING the terminating ungroup line.
            i = j + 1
            continue

        # Update plot y-axis label if present
        if "y = '% intact/repaired" in line:
            out.append("        x = 'Region class', y = '% of (T0 + T120) within region', fill = 'Time'\n")
            i += 1
            continue

        out.append(line)
        i += 1

    return out


def main() -> None:
    nb = json.loads(NB_PATH.read_text(encoding="utf-8"))

    patched = False
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source")
        if not isinstance(src, list):
            continue
        text = "".join(src)
        if MARKER not in text:
            continue

        cell["source"] = patch_cell_source(src)
        patched = True
        break

    if not patched:
        raise SystemExit("Did not find target cell to patch")

    NB_PATH.write_text(json.dumps(nb, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Patched region_summary denominator logic in", NB_PATH)


if __name__ == "__main__":
    main()
