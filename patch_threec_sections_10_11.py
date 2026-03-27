#!/usr/bin/env python3
"""Patch ThreeC_OneShot_Report.ipynb Section 10–11 plots to use dodged T0/T120 bars.

This targets the code cell containing:
  "Batch-wise CIS/TRANS locus frequencies + region broken/unbroken comparisons (T0 vs T120)"

It replaces the entire cell source with an updated R block where:
- time_label (T0/T120) is used as bar fill and shown side-by-side
- broken_status is moved into facets
- top loci are selected consistently across timepoints (max pct across T0/T120)

Outputs are cleared for that cell so the notebook reflects the new code cleanly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
NB_PATH = ROOT / "ThreeC_OneShot_Report.ipynb"

MARKER = "Batch-wise CIS/TRANS locus frequencies + region broken/unbroken comparisons (T0 vs T120)"


def _line_list(text: str) -> list[str]:
    if not text:
        return []
    # Keep line endings so Jupyter source rendering is stable.
    return text.splitlines(keepends=True)


NEW_R_CODE = r"""# ---- Batch-wise CIS/TRANS locus frequencies + region broken/unbroken comparisons (T0 vs T120) ----
suppressPackageStartupMessages({
  library(tidyverse)
})

if (!exists('dat_focus')) {
  stop('dat_focus is missing. Run the upstream 3C data-load/prep cells first.')
}

normalize_locus_id_batchmap <- function(x) {
  x <- as.character(x)
  x <- stringr::str_trim(x)
  x <- stringr::str_to_upper(x)
  x <- stringr::str_replace(x, '^CHR', '')
  x <- stringr::str_replace(x, '_1PERCENT_CONTROL$', '')
  x
}

roman_to_int_local <- function(x) {
  x <- toupper(as.character(x))
  map <- c(I=1, II=2, III=3, IV=4, V=5, VI=6, VII=7, VIII=8, IX=9, X=10, XI=11, XII=12, XIII=13, XIV=14, XV=15, XVI=16)
  out <- suppressWarnings(as.integer(x))
  bad <- is.na(out)
  out[bad] <- unname(map[x[bad]])
  out
}

to_numeric_locus <- function(x) {
  x <- normalize_locus_id_batchmap(x)
  chr_tok <- stringr::str_extract(x, '^[^_]+')
  rest <- stringr::str_replace(x, '^[^_]+_?', '')
  chr_num <- roman_to_int_local(chr_tok)
  ifelse(is.na(chr_num), x, ifelse(rest == '', as.character(chr_num), paste0(chr_num, '_', rest)))
}

num_to_roman <- function(x) {
  roman_map <- c('I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII','XIV','XV','XVI')
  xi <- suppressWarnings(as.integer(readr::parse_number(as.character(x))))
  ifelse(is.na(xi) | xi < 1 | xi > 16, as.character(x), roman_map[xi])
}

coords_tbl_batch <- NULL
if (exists('break_loci') && is.data.frame(break_loci)) {
  coords_tbl_batch <- break_loci %>%
    dplyr::transmute(
      locus_id = to_numeric_locus(locus_id),
      chrom = num_to_roman(stringr::str_extract(locus_id, '^[^_]+')),
      midpoint = as.numeric(midpoint)
    ) %>%
    dplyr::filter(!is.na(locus_id), locus_id != '', !is.na(chrom), is.finite(midpoint))
} else {
  primer_csv <- file.path(getwd(), 'Insertion_Primers_for_Locations_of_DSBs.csv')
  if (!file.exists(primer_csv)) stop('Missing primer CSV for coordinate mapping: ', primer_csv)

  primer_raw <- readr::read_csv(primer_csv, show_col_types = FALSE, col_types = readr::cols(.default = readr::col_character()))
  coord_cols <- grep('^Chromosome Coordinate', names(primer_raw), value = TRUE)
  if (length(coord_cols) < 2) stop('Primer CSV does not have two Chromosome Coordinate columns.')

  coords_tbl_batch <- primer_raw %>%
    dplyr::mutate(
      locus_id = to_numeric_locus(stringr::str_replace(stringr::str_to_upper(as.character(.data[['Primer Name']])), '_(FWD|REV)$', '')),
      chrom = num_to_roman(stringr::str_extract(locus_id, '^[^_]+')),
      c1 = readr::parse_number(as.character(.data[[coord_cols[1]]])),
      c2 = readr::parse_number(as.character(.data[[coord_cols[2]]])),
      midpoint = rowMeans(cbind(c1, c2), na.rm = TRUE)
    ) %>%
    dplyr::group_by(locus_id, chrom) %>%
    dplyr::summarise(midpoint = mean(midpoint, na.rm = TRUE), .groups = 'drop')
}

chr_lengths <- tibble::tribble(
  ~chrom, ~chr_len,
  'I', 230218, 'II', 813184, 'III', 316620, 'IV', 1531933,
  'V', 576874, 'VI', 270161, 'VII', 1090940, 'VIII', 562643,
  'IX', 439888, 'X', 745751, 'XI', 666816, 'XII', 1078177,
  'XIII', 924431, 'XIV', 784333, 'XV', 1091291, 'XVI', 948066
)

centromeres <- tibble::tribble(
  ~chrom, ~cen_bp,
  'I', 151583, 'II', 238323, 'III', 114385, 'IV', 449711,
  'V', 151465, 'VI', 148510, 'VII', 497038, 'VIII', 105703,
  'IX', 355629, 'X', 436425, 'XI', 440246, 'XII', 150947,
  'XIII', 268031, 'XIV', 628758, 'XV', 326584, 'XVI', 556070
)

analysis_tp <- c(0, 120)

df_loc <- dat_focus %>%
  dplyr::mutate(
    batch = as.character(batch),
    time_point = readr::parse_number(as.character(time_point)),
    allele = to_numeric_locus(allele),
    count = readr::parse_number(as.character(count)),
    pair_class = dplyr::case_when(
      toupper(as.character(cis_trans)) %in% c('CIS', 'TRANS') ~ toupper(as.character(cis_trans)),
      combo %in% c('A_to_B', 'C_to_D') ~ 'CIS',
      combo %in% c('A_to_D', 'C_to_B') ~ 'TRANS',
      TRUE ~ NA_character_
    ),
    broken_status = dplyr::if_else(toupper(as.character(DSB)) %in% c('DSB1', 'DSB2'), 'broken', 'unbroken')
  ) %>%
  dplyr::filter(time_point %in% analysis_tp, is.finite(count), !is.na(allele), allele != '') %>%
  dplyr::inner_join(coords_tbl_batch, by = c('allele' = 'locus_id')) %>%
  dplyr::inner_join(chr_lengths, by = 'chrom') %>%
  dplyr::inner_join(centromeres, by = 'chrom') %>%
  dplyr::mutate(
    telomere_flag = midpoint <= (0.10 * chr_len) | midpoint >= (0.90 * chr_len),
    centromere_flag = abs(midpoint - cen_bp) <= pmax(0.05 * chr_len, 30000),
    left_arm_len = cen_bp,
    right_arm_len = chr_len - cen_bp,
    on_left = midpoint < cen_bp,
    arm_type = dplyr::case_when(
      on_left & left_arm_len >= right_arm_len ~ 'long_arm',
      on_left & left_arm_len < right_arm_len ~ 'short_arm',
      !on_left & right_arm_len >= left_arm_len ~ 'long_arm',
      TRUE ~ 'short_arm'
    ),
    region_class = dplyr::case_when(
      centromere_flag ~ 'centromere',
      telomere_flag ~ 'telomere',
      TRUE ~ arm_type
    ),
    time_label = paste0('T', as.integer(time_point))
  )

if (nrow(df_loc) == 0) {
  stop('No rows available for T0/T120 locus-frequency regional analysis.')
}

region_summary <- df_loc %>%
  dplyr::filter(!is.na(pair_class), pair_class %in% c('CIS', 'TRANS')) %>%
  dplyr::group_by(batch, pair_class, broken_status, region_class, time_point, time_label) %>%
  dplyr::summarise(count_sum = sum(count, na.rm = TRUE), .groups = 'drop') %>%
  # Denominator is (starting + repaired) = (T0 + T120) within each region grouping
  dplyr::group_by(batch, pair_class, broken_status, region_class) %>%
  dplyr::mutate(
    denom = sum(count_sum, na.rm = TRUE),
    # T0 = starting (intact), T120 = repaired; each region sums to 100 across T0+T120
    pct_intact_repaired = ifelse(denom > 0, 100 * count_sum / denom, NA_real_)
  ) %>%
  dplyr::ungroup() %>%
  dplyr::select(-denom)

locus_summary <- df_loc %>%
  dplyr::filter(!is.na(pair_class), pair_class %in% c('CIS', 'TRANS')) %>%
  dplyr::group_by(batch, time_point, time_label, pair_class, broken_status, allele) %>%
  dplyr::summarise(count_sum = sum(count, na.rm = TRUE), .groups = 'drop_last') %>%
  dplyr::mutate(
    denom = sum(count_sum, na.rm = TRUE),
    pct_within_group = ifelse(denom > 0, 100 * count_sum / denom, NA_real_)
  ) %>%
  dplyr::select(-denom) %>%
  dplyr::ungroup()

plot_dir <- file.path(getwd(), 'Outputs', '3C', 'figures')
out_dir <- file.path(getwd(), 'Outputs', '3C')
dir.create(plot_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

TIME_COLORS <- c('T0' = '#bdbdbd', 'T120' = '#3182bd')
TIME_LEVELS <- c('T0', 'T120')

saved_extra_plots <- character(0)
for (b in sort(unique(locus_summary$batch))) {
  cis_rank <- locus_summary %>%
    dplyr::filter(batch == b, pair_class == 'CIS') %>%
    dplyr::group_by(broken_status, allele) %>%
    dplyr::summarise(max_pct = max(pct_within_group, na.rm = TRUE), .groups = 'drop') %>%
    dplyr::group_by(broken_status) %>%
    dplyr::slice_max(order_by = max_pct, n = 12, with_ties = FALSE) %>%
    dplyr::select(broken_status, allele) %>%
    dplyr::ungroup()

  cis_top <- locus_summary %>%
    dplyr::filter(batch == b, pair_class == 'CIS') %>%
    dplyr::inner_join(cis_rank, by = c('broken_status', 'allele')) %>%
    dplyr::mutate(time_label = factor(time_label, levels = TIME_LEVELS)) %>%
    dplyr::mutate(allele = forcats::fct_reorder(allele, pct_within_group, .fun = max))

  if (nrow(cis_top) > 0) {
    p_cis <- ggplot(cis_top, aes(x = allele, y = pct_within_group, fill = time_label)) +
      geom_col(position = position_dodge(width = 0.85), width = 0.8) +
      coord_flip() +
      facet_wrap(~broken_status, nrow = 1, scales = 'free_y') +
      scale_fill_manual(values = TIME_COLORS, drop = FALSE) +
      theme_bw(base_size = 11) +
      labs(
        title = paste0('Batch ', b, ': top CIS loci frequencies (T0 vs T120)'),
        subtitle = 'Bars show % within CIS; panels show broken vs unbroken',
        x = 'Locus', y = '% within CIS', fill = 'Time'
      )
    print(p_cis)
    f_cis <- file.path(plot_dir, paste0('3C_batch_', b, '_cis_loci_t0_t120.png'))
    ggplot2::ggsave(f_cis, p_cis, width = 12, height = 6, dpi = 320, units = 'in')
    saved_extra_plots <- c(saved_extra_plots, f_cis)
  }

  trans_rank <- locus_summary %>%
    dplyr::filter(batch == b, pair_class == 'TRANS') %>%
    dplyr::group_by(broken_status, allele) %>%
    dplyr::summarise(max_pct = max(pct_within_group, na.rm = TRUE), .groups = 'drop') %>%
    dplyr::group_by(broken_status) %>%
    dplyr::slice_max(order_by = max_pct, n = 12, with_ties = FALSE) %>%
    dplyr::select(broken_status, allele) %>%
    dplyr::ungroup()

  trans_top <- locus_summary %>%
    dplyr::filter(batch == b, pair_class == 'TRANS') %>%
    dplyr::inner_join(trans_rank, by = c('broken_status', 'allele')) %>%
    dplyr::mutate(time_label = factor(time_label, levels = TIME_LEVELS)) %>%
    dplyr::mutate(allele = forcats::fct_reorder(allele, pct_within_group, .fun = max))

  if (nrow(trans_top) > 0) {
    p_trans <- ggplot(trans_top, aes(x = allele, y = pct_within_group, fill = time_label)) +
      geom_col(position = position_dodge(width = 0.85), width = 0.8) +
      coord_flip() +
      facet_wrap(~broken_status, nrow = 1, scales = 'free_y') +
      scale_fill_manual(values = TIME_COLORS, drop = FALSE) +
      theme_bw(base_size = 11) +
      labs(
        title = paste0('Batch ', b, ': top TRANS loci frequencies (T0 vs T120)'),
        subtitle = 'Bars show % within TRANS; panels show broken vs unbroken',
        x = 'Locus', y = '% within TRANS', fill = 'Time'
      )
    print(p_trans)
    f_trans <- file.path(plot_dir, paste0('3C_batch_', b, '_trans_loci_t0_t120.png'))
    ggplot2::ggsave(f_trans, p_trans, width = 12, height = 6, dpi = 320, units = 'in')
    saved_extra_plots <- c(saved_extra_plots, f_trans)
  }

  reg_b <- region_summary %>%
    dplyr::filter(batch == b) %>%
    dplyr::mutate(time_label = factor(time_label, levels = TIME_LEVELS))

  if (nrow(reg_b) > 0) {
    p_region <- ggplot(reg_b, aes(x = region_class, y = pct_intact_repaired, fill = time_label)) +
      geom_col(position = position_dodge(width = 0.85), width = 0.8) +
      facet_grid(broken_status ~ pair_class) +
      scale_fill_manual(values = TIME_COLORS, drop = FALSE) +
      theme_bw(base_size = 11) +
      labs(
        title = paste0('Batch ', b, ': region frequency comparison (T0 vs T120)'),
        subtitle = 'Within each region: T0 = intact (starting), T120 = repaired; split by broken vs unbroken',
        x = 'Region class', y = '% of (T0 + T120) within region', fill = 'Time'
      )
    print(p_region)
    f_region <- file.path(plot_dir, paste0('3C_batch_', b, '_region_broken_unbroken_t0_t120.png'))
    ggplot2::ggsave(f_region, p_region, width = 12, height = 7, dpi = 320, units = 'in')
    saved_extra_plots <- c(saved_extra_plots, f_region)
  }
}

readr::write_csv(region_summary, file.path(out_dir, '3C_batch_region_broken_unbroken_t0_t120.csv'))
readr::write_csv(locus_summary, file.path(out_dir, '3C_batch_locus_freq_broken_unbroken_t0_t120.csv'))

if (length(saved_extra_plots) > 0) {
  message('Saved batch-wise CIS/TRANS and region plots:')
  message(paste0(' - ', normalizePath(saved_extra_plots, winslash = '/', mustWork = FALSE), collapse = '\\n'))
}

message('Saved summary tables in Outputs/3C for region and locus frequencies.')
"""


def main() -> int:
    if not NB_PATH.exists():
        raise SystemExit(f"Notebook not found: {NB_PATH}")

    nb: dict[str, Any]
    with NB_PATH.open("r", encoding="utf-8") as f:
        nb = json.load(f)

    hit = None
    for idx, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", [])
        text = "".join(src) if isinstance(src, list) else str(src)
        if MARKER in text:
            hit = idx
            break

    if hit is None:
        raise SystemExit(f"Did not find target cell containing marker: {MARKER!r}")

    cell = nb["cells"][hit]
    cell["source"] = _line_list(NEW_R_CODE)

    # Clear outputs to avoid stale plots.
    if "outputs" in cell:
        cell["outputs"] = []
    if "execution_count" in cell:
        cell["execution_count"] = None

    with NB_PATH.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(nb, f, indent=4, ensure_ascii=False)
        f.write("\n")

    print(f"Patched cell index {hit} in {NB_PATH.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
