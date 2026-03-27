# ---- Per-batch chromosome maps (robust IDs + T0/T120 facets + CIS/TRANS facets) ----
suppressPackageStartupMessages({
  library(tidyverse)
})

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

num_to_roman <- function(x) {
  roman_map <- c('I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII','XIV','XV','XVI')
  xi <- suppressWarnings(as.integer(readr::parse_number(as.character(x))))
  ifelse(is.na(xi) | xi < 1 | xi > 16, as.character(x), roman_map[xi])
}

to_numeric_locus <- function(x) {
  x <- normalize_locus_id_batchmap(x)
  chr_tok <- stringr::str_extract(x, '^[^_]+')
  rest <- stringr::str_replace(x, '^[^_]+_?', '')
  chr_num <- roman_to_int_local(chr_tok)
  ifelse(is.na(chr_num), x, ifelse(rest == '', as.character(chr_num), paste0(chr_num, '_', rest)))
}

if (!exists('dat_focus')) {
  stop('dat_focus is missing. Run the upstream 3C data-load/prep cells first.')
}

df_map <- dat_focus %>%
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
    )
  ) %>%
  dplyr::filter(is.finite(time_point), is.finite(count), !is.na(batch), batch != '', !is.na(allele), allele != '')

plot_timepoints <- c(0, 120)
if (!all(plot_timepoints %in% unique(df_map$time_point))) {
  plot_timepoints <- sort(unique(df_map$time_point))
}
message('Using time points for faceted maps: ', paste0('T', plot_timepoints, collapse = ', '))

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
  primer_csv_candidates <- c(
    file.path(getwd(), 'data', 'raw', 'Insertion_Primers_for_Locations_of_DSBs.csv'),
    file.path(getwd(), 'Insertion_Primers_for_Locations_of_DSBs.csv'),
    file.path(getwd(), 'data', 'csv', 'Insertion_Primers_for_Locations_of_DSBs.csv')
  )
  primer_csv <- primer_csv_candidates[file.exists(primer_csv_candidates)][1]
  if (is.na(primer_csv) || is.null(primer_csv)) primer_csv <- primer_csv_candidates[1]
  if (!file.exists(primer_csv)) stop('Missing primer CSV for coordinate mapping. Tried: ', paste(primer_csv_candidates, collapse = ' | '))

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
    dplyr::summarise(midpoint = mean(midpoint, na.rm = TRUE), .groups = 'drop') %>%
    dplyr::filter(!is.na(locus_id), locus_id != '', !is.na(chrom), is.finite(midpoint))
}

chr_lengths <- tibble::tribble(
  ~chrom, ~chr_len,
  'I', 230218,
  'II', 813184,
  'III', 316620,
  'IV', 1531933,
  'V', 576874,
  'VI', 270161,
  'VII', 1090940,
  'VIII', 562643,
  'IX', 439888,
  'X', 745751,
  'XI', 666816,
  'XII', 1078177,
  'XIII', 924431,
  'XIV', 784333,
  'XV', 1091291,
  'XVI', 948066
)

centromeres <- tibble::tribble(
  ~chrom, ~cen_bp,
  'I', 151583,
  'II', 238323,
  'III', 114385,
  'IV', 449711,
  'V', 151465,
  'VI', 148510,
  'VII', 497038,
  'VIII', 105703,
  'IX', 355629,
  'X', 436425,
  'XI', 440246,
  'XII', 150947,
  'XIII', 268031,
  'XIV', 628758,
  'XV', 326584,
  'XVI', 556070
)

chr_order <- c('I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII','XIV','XV','XVI')
chr_layout_batch <- chr_lengths %>%
  dplyr::mutate(chrom = factor(chrom, levels = chr_order)) %>%
  dplyr::arrange(chrom) %>%
  dplyr::mutate(y = dplyr::row_number()) %>%
  dplyr::left_join(centromeres, by = 'chrom')

base_locus <- df_map %>%
  dplyr::filter(time_point %in% plot_timepoints) %>%
  dplyr::group_by(batch, time_point, locus_id = allele, pair_class) %>%
  dplyr::summarise(count_t = sum(count, na.rm = TRUE), .groups = 'drop') %>%
  dplyr::inner_join(coords_tbl_batch, by = 'locus_id') %>%
  dplyr::inner_join(chr_layout_batch %>% dplyr::select(chrom, y, chr_len), by = 'chrom') %>%
  dplyr::mutate(pos_mb = midpoint / 1e6)

if (nrow(base_locus) == 0) {
  stop('No plottable loci for per-batch chromosome maps at selected time points.')
}

batch_locus_time <- base_locus %>%
  dplyr::group_by(batch, time_point) %>%
  dplyr::mutate(
    total_by_time = sum(count_t, na.rm = TRUE),
    pct_of_time = dplyr::if_else(total_by_time > 0, 100 * count_t / total_by_time, NA_real_),
    time_label = paste0('T', as.integer(time_point))
  ) %>%
  dplyr::ungroup()

batch_locus_class <- base_locus %>%
  dplyr::filter(!is.na(pair_class), pair_class %in% c('CIS', 'TRANS')) %>%
  dplyr::group_by(batch, pair_class, time_point) %>%
  dplyr::mutate(
    total_by_class_time = sum(count_t, na.rm = TRUE),
    pct_of_class_time = dplyr::if_else(total_by_class_time > 0, 100 * count_t / total_by_class_time, NA_real_),
    time_label = paste0('T', as.integer(time_point))
  ) %>%
  dplyr::ungroup()

out_dir <- file.path(getwd(), 'Outputs', '3C', 'figures')
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

batches <- sort(unique(batch_locus_time$batch))
saved_batch_maps <- character(0)

for (b in batches) {
  db_time <- batch_locus_time %>% dplyr::filter(batch == b)
  top_labels <- db_time %>%
    dplyr::group_by(time_label) %>%
    dplyr::arrange(dplyr::desc(pct_of_time), .by_group = TRUE) %>%
    dplyr::slice_head(n = 10) %>%
    dplyr::ungroup()

  p_time_facets <- ggplot() +
    geom_segment(
      data = chr_layout_batch,
      aes(x = 0, xend = chr_len / 1e6, y = y, yend = y),
      linewidth = 2.2,
      color = 'grey72'
    ) +
    geom_segment(
      data = chr_layout_batch %>% dplyr::filter(is.finite(cen_bp)),
      aes(x = cen_bp / 1e6, xend = cen_bp / 1e6, y = y - 0.22, yend = y + 0.22),
      linewidth = 0.7,
      color = 'black'
    ) +
    geom_point(
      data = db_time,
      aes(x = pos_mb, y = y, size = count_t, color = pct_of_time),
      alpha = 0.9,
      stroke = 0.25
    ) +
    geom_text(
      data = top_labels,
      aes(x = pos_mb, y = y + 0.28, label = locus_id),
      size = 2.3,
      check_overlap = TRUE
    ) +
    facet_wrap(~time_label, nrow = 1) +
    scale_y_continuous(
      breaks = chr_layout_batch$y,
      labels = as.character(chr_layout_batch$chrom),
      expand = expansion(mult = c(0.03, 0.08))
    ) +
    scale_color_viridis_c(option = 'magma', na.value = 'grey40') +
    scale_size_continuous(range = c(1.4, 5.8)) +
    theme_bw(base_size = 11) +
    theme(panel.grid.major.y = element_blank()) +
    labs(
      title = paste0('Batch ', b, ': chromosome maps faceted by time point'),
      subtitle = 'T0 vs T120 facets; color = % within timepoint, size = counts',
      x = 'Position within chromosome (Mb)',
      y = 'Chromosome',
      color = '% within time',
      size = 'Counts'
    )

  print(p_time_facets)
  out_time <- file.path(out_dir, paste0('3C_chrmap_batch_', b, '_t0_t120_faceted.png'))
  ggplot2::ggsave(filename = out_time, plot = p_time_facets, width = 12, height = 6, dpi = 320, units = 'in')
  saved_batch_maps <- c(saved_batch_maps, out_time)

  db_class <- batch_locus_class %>% dplyr::filter(batch == b, time_point == max(plot_timepoints, na.rm = TRUE))
  if (nrow(db_class) > 0) {
    top_labels_ct <- db_class %>%
      dplyr::group_by(pair_class) %>%
      dplyr::arrange(dplyr::desc(pct_of_class_time), .by_group = TRUE) %>%
      dplyr::slice_head(n = 10) %>%
      dplyr::ungroup()

    p_class_facets <- ggplot() +
      geom_segment(
        data = chr_layout_batch,
        aes(x = 0, xend = chr_len / 1e6, y = y, yend = y),
        linewidth = 2.2,
        color = 'grey72'
      ) +
      geom_segment(
        data = chr_layout_batch %>% dplyr::filter(is.finite(cen_bp)),
        aes(x = cen_bp / 1e6, xend = cen_bp / 1e6, y = y - 0.22, yend = y + 0.22),
        linewidth = 0.7,
        color = 'black'
      ) +
      geom_point(
        data = db_class,
        aes(x = pos_mb, y = y, size = count_t, color = pct_of_class_time),
        alpha = 0.9,
        stroke = 0.25
      ) +
      geom_text(
        data = top_labels_ct,
        aes(x = pos_mb, y = y + 0.28, label = locus_id),
        size = 2.3,
        check_overlap = TRUE
      ) +
      facet_wrap(~pair_class, nrow = 1) +
      scale_y_continuous(
        breaks = chr_layout_batch$y,
        labels = as.character(chr_layout_batch$chrom),
        expand = expansion(mult = c(0.03, 0.08))
      ) +
      scale_color_viridis_c(option = 'plasma', na.value = 'grey40') +
      scale_size_continuous(range = c(1.4, 5.8)) +
      theme_bw(base_size = 11) +
      theme(panel.grid.major.y = element_blank()) +
      labs(
        title = paste0('Batch ', b, ': CIS vs TRANS chromosome maps at T', max(plot_timepoints, na.rm = TRUE)),
        subtitle = 'Facets split by molecular class; color = % within class, size = counts',
        x = 'Position within chromosome (Mb)',
        y = 'Chromosome',
        color = '% within class',
        size = 'Counts'
      )

    print(p_class_facets)
    out_ct <- file.path(out_dir, paste0('3C_chrmap_batch_', b, '_cis_trans_faceted_t', max(plot_timepoints, na.rm = TRUE), '.png'))
    ggplot2::ggsave(filename = out_ct, plot = p_class_facets, width = 12, height = 6, dpi = 320, units = 'in')
    saved_batch_maps <- c(saved_batch_maps, out_ct)
  }
}

readr::write_csv(
  batch_locus_time %>% dplyr::arrange(batch, time_point, dplyr::desc(pct_of_time), chrom, locus_id),
  file.path(getwd(), 'Outputs', '3C', '3C_batch_chrmap_table_t0_t120.csv')
)

readr::write_csv(
  batch_locus_class %>% dplyr::arrange(batch, time_point, pair_class, dplyr::desc(pct_of_class_time), chrom, locus_id),
  file.path(getwd(), 'Outputs', '3C', '3C_batch_chrmap_cis_trans_table_t0_t120.csv')
)

message('Saved per-batch faceted chromosome maps:')
message(paste0(' - ', normalizePath(saved_batch_maps, winslash = '/', mustWork = FALSE), collapse = '\n'))