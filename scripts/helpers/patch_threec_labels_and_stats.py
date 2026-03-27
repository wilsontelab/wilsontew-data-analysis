#!/usr/bin/env python3
"""Patch ThreeC_OneShot_Report.ipynb to:

1) Add data labels to bar charts.
2) Add r and r^2 annotations to lm regression plots.
3) Fix region_class bar math so T0/T120 represent:
     %intact  = starting / (starting + repaired)
     %repaired = repaired / (starting + repaired)
   where starting=T0 and repaired=T120 within each grouping.

This script edits notebook code cells by matching marker headers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

ROOT = Path(__file__).resolve().parent
NB_PATH = ROOT.parents[1] / "notebooks" / "ThreeC_OneShot_Report.ipynb"

MARKER_QC = "# ---- QC plots ----"
MARKER_S7S9 = "# ---- Sections 7, 8, 9: contribution bars, FC bars, and log2FC-vs-AF scatters (cleaned) ----"
MARKER_BATCH = "# ---- Batch-wise CIS/TRANS locus frequencies + region broken/unbroken comparisons (T0 vs T120) ----"


def _ensure_lines(src: Any) -> List[str]:
    if src is None:
        return []
    if isinstance(src, list):
        return [str(x) for x in src]
    return str(src).splitlines(keepends=True)


def _replace_cell_source(nb: dict[str, Any], marker: str, new_lines: List[str]) -> int:
    for idx, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        text = "".join(_ensure_lines(cell.get("source")))
        if marker in text:
            cell["source"] = new_lines
            return idx
    raise RuntimeError(f"Did not find code cell marker: {marker!r}")


def _patch_qc_cell(lines: List[str]) -> List[str]:
    out: List[str] = []
    inserted = False
    for ln in lines:
        out.append(ln)
        if (not inserted) and "geom_col(position = position_dodge(width = 0.85), width = 0.8)" in ln:
            out.append("  geom_text(aes(label = scales::comma(Total_Counts)), position = position_dodge(width = 0.85), vjust = -0.25, size = 3.1, color = 'grey20') +\n")
            inserted = True
        if "facet_grid(DSB ~ replicate" in ln and inserted:
            # Add a y-scale with room for the labels (only once)
            out.append("  scale_y_continuous(labels = scales::comma, expand = expansion(mult = c(0, 0.12))) +\n")
    return out


def _insert_after(out: List[str], predicate, insert_lines: List[str]):
    # Walk once; insert right after the first line satisfying predicate.
    for i in range(len(out) - 1, -1, -1):
        pass


def _patch_s7s9_cell(lines: List[str]) -> List[str]:
    out: List[str] = []

    helper_inserted = False

    for ln in lines:
        out.append(ln)

        # After dsb_plot_levels() definition, inject helpers once.
        if (not helper_inserted) and ln.strip() == "}":
            # Heuristic: the first standalone '}' after dsb_plot_levels block occurs very early.
            # Confirm previous few lines mention dsb_plot_levels.
            prev = "".join(out[-15:])
            if "dsb_plot_levels <- function" in prev:
                out.append("\n")
                out.append("# Helper label formatting (avoid clutter by hiding tiny bars)\n")
                out.append("label_pct <- function(x, digits = 1, min_show = 1) {\n")
                out.append("  ifelse(is.na(x) | !is.finite(x) | x < min_show, NA_character_, paste0(round(x, digits), '%'))\n")
                out.append("}\n")
                out.append("\n")
                out.append("label_num <- function(x, digits = 2, min_show = 0) {\n")
                out.append("  ifelse(is.na(x) | !is.finite(x) | x < min_show, NA_character_, as.character(round(x, digits)))\n")
                out.append("}\n")
                out.append("\n")
                out.append("lm_stats_label_df <- function(df, x_col, y_col) {\n")
                out.append("  d <- df %>% dplyr::filter(is.finite(.data[[x_col]]), is.finite(.data[[y_col]]))\n")
                out.append("  if (nrow(d) < 2) return(tibble::tibble(x = Inf, y = Inf, label = NA_character_))\n")
                out.append("  r <- suppressWarnings(stats::cor(d[[x_col]], d[[y_col]], method = 'pearson'))\n")
                out.append("  fit <- tryCatch(stats::lm(d[[y_col]] ~ d[[x_col]]), error = function(e) NULL)\n")
                out.append("  r2 <- if (is.null(fit)) NA_real_ else summary(fit)$r.squared\n")
                out.append("  tibble::tibble(x = Inf, y = Inf, label = sprintf('r = %.3f\\nr^2 = %.3f', r, r2))\n")
                out.append("}\n")
                out.append("\n")
                helper_inserted = True

    # Second pass: inject geom_text after geom_col calls and annotate regression plots.
    patched: List[str] = []
    for ln in out:
        patched.append(ln)

        if "geom_col(position = position_dodge(width = 0.9), width = 0.85" in ln:
            # Percent contribution plots (CIS/TRANS and per-combo). Uses different y columns in different functions;
            # we rely on mapping inside aes(y=...) so just use ..y.. via after_stat? ggplot2 doesn't support that
            # cleanly here, so add explicit label mappings in each plot below where possible.
            continue

        # Add lm stats labels after geom_smooth in CIS plot
        if "geom_smooth(aes(x = Allele_Frequency, y = log2FC_CIS)" in ln:
            patched.append("    geom_text(data = lm_stats_label_df(df_plot, 'Allele_Frequency', 'log2FC_CIS'), aes(x = x, y = y, label = label), inherit.aes = FALSE, hjust = 1.1, vjust = 1.1, size = 3.2) +\n")

        if "geom_smooth(aes(x = Allele_Frequency, y = log2FC_TRANS)" in ln:
            patched.append("    geom_text(data = lm_stats_label_df(df_plot, 'Allele_Frequency', 'log2FC_TRANS'), aes(x = x, y = y, label = label), inherit.aes = FALSE, hjust = 1.1, vjust = 1.1, size = 3.2) +\n")

    # Third pass: function-specific bar labels by matching the plot-building lines.
    final: List[str] = []
    for ln in patched:
        final.append(ln)

        # CIS contrib
        if "geom_col(position = position_dodge(width = 0.9), width = 0.85, na.rm = TRUE) +" in ln:
            # We can only safely add this in the CIS/TRANS contrib functions where the y variable is known.
            # We'll add a generic mapping if the variable name appears in the preceding aes line.
            continue

        # Foldchange CIS bars
        if "geom_col(width = 0.85, na.rm = TRUE, fill = '#008837') +" in ln:
            final.append("        geom_text(aes(label = label_num(FoldChange_Cis_120_vs_0, digits = 2, min_show = 0)), vjust = -0.25, size = 2.8, color = 'grey10') +\n")
            final.append("        scale_y_continuous(expand = expansion(mult = c(0, 0.10))) +\n")

        # Foldchange TRANS bars
        if "geom_col(width = 0.85, na.rm = TRUE, fill = '#7b3294') +" in ln:
            final.append("        geom_text(aes(label = label_num(FoldChange_Trans_120_vs_0, digits = 2, min_show = 0)), vjust = -0.25, size = 2.8, color = 'grey10') +\n")
            final.append("        scale_y_continuous(expand = expansion(mult = c(0, 0.10))) +\n")

        # Allele frequency bars
        if "geom_col(position = position_dodge(width = 0.9), width = 0.85, na.rm = TRUE) +" in ln and "Allele_Frequency" in "".join(final[-8:]):
            final.append("        geom_text(aes(label = label_pct(100 * Allele_Frequency, digits = 1, min_show = 1)), position = position_dodge(width = 0.9), vjust = -0.25, size = 2.6, color = 'grey10') +\n")
            final.append("        scale_y_continuous(labels = scales::percent_format(accuracy = 1), expand = expansion(mult = c(0, 0.10))) +\n")

        # Percent trans by combo
        if "geom_col(position = position_dodge(width = 0.9), width = 0.85, na.rm = TRUE) +" in ln and "Percent_Trans" in "".join(final[-8:]):
            final.append("      geom_text(aes(label = label_pct(Percent_Trans, digits = 1, min_show = 2)), position = position_dodge(width = 0.9), vjust = -0.25, size = 2.5, color = 'grey10') +\n")
            final.append("      scale_y_continuous(expand = expansion(mult = c(0, 0.10))) +\n")

        # CIS/TRANS contribution plots
        if "geom_col(position = position_dodge(width = 0.9), width = 0.85, na.rm = TRUE) +" in ln and "Percent_Location_in_Cis" in "".join(final[-8:]):
            final.append("        geom_text(aes(label = label_pct(Percent_Location_in_Cis, digits = 1, min_show = 2)), position = position_dodge(width = 0.9), vjust = -0.25, size = 2.4, color = 'grey10') +\n")
            final.append("        scale_y_continuous(expand = expansion(mult = c(0, 0.12))) +\n")

        if "geom_col(position = position_dodge(width = 0.9), width = 0.85, na.rm = TRUE) +" in ln and "Percent_Location_in_Trans" in "".join(final[-8:]):
            final.append("        geom_text(aes(label = label_pct(Percent_Location_in_Trans, digits = 1, min_show = 2)), position = position_dodge(width = 0.9), vjust = -0.25, size = 2.4, color = 'grey10') +\n")
            final.append("        scale_y_continuous(expand = expansion(mult = c(0, 0.12))) +\n")

    return final


def _patch_batch_cell(lines: List[str]) -> List[str]:
    # 1) Replace region_summary computation to compute pct across timepoints within each region.
    out = list(lines)

    # Find the region_summary block
    start = None
    end = None
    for i, ln in enumerate(out):
        if ln.strip() == "region_summary <- df_loc %>%":
            start = i
            continue
        if start is not None and i > start and ln.strip() == "dplyr::ungroup()":
            end = i
            break

    if start is None or end is None:
        raise RuntimeError("Could not locate region_summary block to replace")

    new_block = [
        "region_summary <- df_loc %>%\n",
        "  dplyr::filter(!is.na(pair_class), pair_class %in% c('CIS', 'TRANS')) %>%\n",
        "  dplyr::group_by(batch, pair_class, broken_status, region_class, time_point, time_label) %>%\n",
        "  dplyr::summarise(count_sum = sum(count, na.rm = TRUE), .groups = 'drop') %>%\n",
        "  # Denominator is (starting + repaired) = (T0 + T120) within each region grouping\n",
        "  dplyr::group_by(batch, pair_class, broken_status, region_class) %>%\n",
        "  dplyr::mutate(\n",
        "    denom = sum(count_sum, na.rm = TRUE),\n",
        "    # T0 = starting (intact), T120 = repaired; each region sums to 100 across T0+T120\n",
        "    pct_intact_repaired = ifelse(denom > 0, 100 * count_sum / denom, NA_real_)\n",
        "  ) %>%\n",
        "  dplyr::ungroup() %>%\n",
        "  dplyr::select(-denom)\n",
    ]

    out = out[:start] + new_block + out[end + 1:]

    # 2) Update p_region mapping to use pct_intact_repaired and add bar labels.
    patched: List[str] = []
    for ln in out:
        if "aes(x = region_class, y = pct_within_group, fill = time_label)" in ln:
            patched.append(ln.replace("pct_within_group", "pct_intact_repaired"))
            continue
        patched.append(ln)

    final: List[str] = []
    for ln in patched:
        final.append(ln)

        # Add labels to top-loci bar plots
        if "geom_col(position = position_dodge(width = 0.85), width = 0.8) +" in ln and "p_cis <-" in "".join(final[-12:]):
            final.append("      geom_text(aes(label = if_else(is.na(pct_within_group) | pct_within_group < 1, NA_character_, paste0(round(pct_within_group, 1), '%'))), position = position_dodge(width = 0.85), hjust = -0.05, size = 2.6, color = 'grey10') +\n")
            final.append("      scale_y_continuous(expand = expansion(mult = c(0, 0.12))) +\n")

        if "geom_col(position = position_dodge(width = 0.85), width = 0.8) +" in ln and "p_trans <-" in "".join(final[-12:]):
            final.append("      geom_text(aes(label = if_else(is.na(pct_within_group) | pct_within_group < 1, NA_character_, paste0(round(pct_within_group, 1), '%'))), position = position_dodge(width = 0.85), hjust = -0.05, size = 2.6, color = 'grey10') +\n")
            final.append("      scale_y_continuous(expand = expansion(mult = c(0, 0.12))) +\n")

        # Region plot labels
        if "geom_col(position = position_dodge(width = 0.85), width = 0.8) +" in ln and "p_region <-" in "".join(final[-12:]):
            final.append("      geom_text(aes(label = if_else(is.na(pct_intact_repaired) | pct_intact_repaired < 1, NA_character_, paste0(round(pct_intact_repaired, 1), '%'))), position = position_dodge(width = 0.85), vjust = -0.25, size = 2.5, color = 'grey10') +\n")
            final.append("      scale_y_continuous(limits = c(0, 100), expand = expansion(mult = c(0, 0.12))) +\n")

        # Update region plot labels in labs()
        if "x = 'Region class', y = '% within class', fill = 'Time'" in ln:
            final[-1] = ln.replace("% within class", "% of (T0 + T120) within region")

        if "subtitle = 'Centromere/telomere/long-arm/short-arm within CIS/TRANS; split by broken vs unbroken'" in ln:
            final[-1] = "        subtitle = 'Within each region: T0 = intact (starting), T120 = repaired; split by broken vs unbroken',\n"

    return final


def main() -> int:
    nb = json.loads(NB_PATH.read_text(encoding="utf-8"))

    # QC cell
    qc_idx = None
    for idx, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        src = _ensure_lines(cell.get("source"))
        if any(MARKER_QC in s for s in src):
            qc_idx = idx
            patched = _patch_qc_cell(src)
            cell["source"] = patched
            break
    if qc_idx is None:
        raise RuntimeError("QC cell not found")

    # Sections 7–9 cell
    s_idx = None
    for idx, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        src = _ensure_lines(cell.get("source"))
        if any(MARKER_S7S9 in s for s in src):
            s_idx = idx
            cell["source"] = _patch_s7s9_cell(src)
            break
    if s_idx is None:
        raise RuntimeError("Sections 7–9 cell not found")

    # Batch-wise cell
    b_idx = None
    for idx, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        src = _ensure_lines(cell.get("source"))
        if any(MARKER_BATCH in s for s in src):
            b_idx = idx
            cell["source"] = _patch_batch_cell(src)
            # clear outputs to avoid stale plots
            if "outputs" in cell:
                cell["outputs"] = []
            if "execution_count" in cell:
                cell["execution_count"] = None
            break
    if b_idx is None:
        raise RuntimeError("Batch-wise cell not found")

    NB_PATH.write_text(json.dumps(nb, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Patched notebook cells: QC idx={qc_idx}, S7-9 idx={s_idx}, batch idx={b_idx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
