library(ggplot2)
install.packages("plotly")  # once
library(plotly)

# Example: bar plot of percent in cis by location, faceted by batch
ggplot(dat, aes(x = allele, y = Percent_Location_in_Cis)) +
  geom_col() +
  facet_wrap(~ batch, scales = "free_x") +
  theme_bw() +
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust = 1)) +
  labs(
    title = "Percent of reads in cis by location, separated by batch",
    x = "Location",
    y = "Percent in cis"
  )

# collapse across batch to get overall cis/trans percent per location
dat_overall_loc <- dat %>%
  group_by(allele) %>%
  summarise(
    Cis_Location_Counts_overall   = sum(Cis_Location_Counts,   na.rm = TRUE),
    Trans_Location_Counts_overall = sum(Trans_Location_Counts, na.rm = TRUE),
    Total_Location_Counts_overall = Cis_Location_Counts_overall + Trans_Location_Counts_overall,
    Percent_Location_in_Cis_overall   = 100 * Cis_Location_Counts_overall   / Total_Location_Counts_overall,
    Percent_Location_in_Trans_overall = 100 * Trans_Location_Counts_overall / Total_Location_Counts_overall
  )


# 1. Compute correlation (Pearson by default)
cor_res <- cor.test(
  dat_overall_loc$Percent_Location_in_Cis_overall,
  dat_overall_loc$Percent_Location_in_Trans_overall
)

R_value <- unname(cor_res$estimate)   # numeric R
p_value <- cor_res$p.value

# 2. Create a label
label_text <- paste0("R = ", round(R_value, 2),
                     "\nP = ", signif(p_value, 2))

ggplot(dat_overall_loc,
       aes(x = Percent_Location_in_Cis_overall,
           y = Percent_Location_in_Trans_overall,
           label = allele)) +
  geom_point() +
  geom_smooth(method = "lm", se = FALSE, color = "red") +
  geom_text(vjust = -0.5, size = 3) +
  annotate("text",
           x = Inf, y = Inf,
           label = label_text,
           hjust = 1.1, vjust = 1.1,
           size = 4) +
  theme_bw() +
  labs(
    title = "Correlation between cis and trans percentage by location (overall)",
    x = "Percent in cis (overall)",
    y = "Percent in trans (overall)"
  )

ggplot(dat,
       aes(x = Percent_Location_in_Cis,
           y = Percent_Location_in_Trans,
           color = batch)) +
  geom_point(alpha = 0.7) +
  theme_bw() +
  labs(
    title = "Percent in cis vs trans by location, colored by batch",
    x = "Percent in cis",
    y = "Percent in trans"
  )

######################## PCA, clustering by location

########################
# 0. Packages
########################

library(tidyverse)
library(ggplot2)

########################
# 1. Read and combine ALL CSVs
########################

folder <- "C:/Users/dunnmk/Downloads/C_summary"   # adjust as needed
files  <- list.files(folder, pattern = "_summary\\.csv$", full.names = TRUE)

raw_list <- lapply(files, read_csv)

# Add batch / time / condition from file names
add_meta <- function(df, fname) {
  base <- basename(fname)
  
  batch     <- stringr::str_extract(base, "batch\\d+")
  time      <- stringr::str_extract(base, "T\\d+")
  condition <- ifelse(stringr::str_detect(base, "_3C_"), "3C", "no3C")
  
  df %>%
    mutate(
      batch     = batch,
      time      = time,
      condition = condition
    )
}

dat <- purrr::map2_dfr(raw_list, files, add_meta)

########################
# 2. Extract location from alignment_name
########################

dat <- dat %>%
  mutate(
    # example: "CIS_A_to_B_DSB1_Chr12_L01" -> "Chr12_L01"
    location = stringr::str_extract(alignment_name, "Chr[^,]+")
  )

########################
# 3. Add batch-level totals & percents onto dat
########################

dat <- dat %>%
  group_by(batch, time, condition) %>%
  mutate(
    Total_Counts = sum(count, na.rm = TRUE),
    
    Cis_Counts   = sum(count[cis_trans == "CIS"],   na.rm = TRUE),
    Trans_Counts = sum(count[cis_trans == "TRANS"], na.rm = TRUE),
    
    A_to_B_Counts = sum(count[combo == "A_to_B"], na.rm = TRUE),
    C_to_D_Counts = sum(count[combo == "C_to_D"], na.rm = TRUE),
    A_to_D_Counts = sum(count[combo == "A_to_D"], na.rm = TRUE),
    C_to_B_Counts = sum(count[combo == "C_to_B"], na.rm = TRUE),
    
    Percent_Cis   = 100 * Cis_Counts   / Total_Counts,
    Percent_Trans = 100 * Trans_Counts / Total_Counts,
    
    Percent_A_to_B = 100 * A_to_B_Counts / Total_Counts,
    Percent_C_to_D = 100 * C_to_D_Counts / Total_Counts,
    Percent_A_to_D = 100 * A_to_D_Counts / Total_Counts,
    Percent_C_to_B = 100 * C_to_B_Counts / Total_Counts
  ) %>%
  ungroup()

########################
# 4. Add per-location cis/trans counts & percents onto dat
########################

dat <- dat %>%
  group_by(batch, time, condition, location) %>%
  mutate(
    Cis_Location_Counts   = sum(count[cis_trans == "CIS"],   na.rm = TRUE),
    Trans_Location_Counts = sum(count[cis_trans == "TRANS"], na.rm = TRUE)
  ) %>%
  group_by(batch, time, condition) %>%
  mutate(
    Total_Cis_Location_Counts   = sum(Cis_Location_Counts,   na.rm = TRUE),
    Total_Trans_Location_Counts = sum(Trans_Location_Counts, na.rm = TRUE),
    Percent_Location_in_Cis     = ifelse(
      Total_Cis_Location_Counts > 0,
      100 * Cis_Location_Counts   / Total_Cis_Location_Counts,
      NA_real_
    ),
    Percent_Location_in_Trans   = ifelse(
      Total_Trans_Location_Counts > 0,
      100 * Trans_Location_Counts / Total_Trans_Location_Counts,
      NA_real_
    )
  ) %>%
  ungroup()

########################
# 5. Make a per-location summary table (across all batches)
########################

loc_overall <- dat %>%
  group_by(location) %>%
  summarise(
    Cis_Location_Counts_overall   = sum(Cis_Location_Counts,   na.rm = TRUE),
    Trans_Location_Counts_overall = sum(Trans_Location_Counts, na.rm = TRUE),
    Total_Location_Counts_overall =
      Cis_Location_Counts_overall + Trans_Location_Counts_overall,
    Percent_Location_in_Cis_overall =
      100 * Cis_Location_Counts_overall /
      Total_Location_Counts_overall,
    Percent_Location_in_Trans_overall =
      100 * Trans_Location_Counts_overall /
      Total_Location_Counts_overall,
    .groups = "drop"
  )

########################
# 6. PCA on location features
########################

loc_features <- loc_overall %>%
  mutate(
    log_total = log10(Total_Location_Counts_overall + 1)
  ) %>%
  select(
    Percent_Location_in_Cis_overall,
    Percent_Location_in_Trans_overall,
    log_total
  )

pca_res <- prcomp(loc_features, scale. = TRUE)

loc_pca <- as.data.frame(pca_res$x) %>%
  bind_cols(loc_overall %>% select(location))

########################
# 7. PCA plot: locations clustered in PC space, regardless of batch
########################

ggplot(loc_pca, aes(x = PC1, y = PC2, label = location)) +
  geom_point(size = 2) +
  geom_text(vjust = -0.5, size = 3) +
  theme_bw() +
  labs(
    title = "PCA of locations (cis/trans + total counts)",
    x = "PC1",
    y = "PC2"
  )

install.packages("plotly")  # once
library(plotly)

plot_ly(
  data = loc_pca,
  x = ~PC1,
  y = ~PC2,
  z = ~PC3,
  type = "scatter3d",
  mode = "markers+text",
  text = ~location,
  textposition = "top center"
) %>%
  layout(
    title = "3D PCA of locations (PC1–PC3)",
    scene = list(
      xaxis = list(title = "PC1"),
      yaxis = list(title = "PC2"),
      zaxis = list(title = "PC3")
    )
  )

######################## PCA, clustering by Time

########################
# 0. Packages
########################

library(tidyverse)
library(ggplot2)

########################
# 1. Read and combine ALL CSVs
########################

folder <- "C:/Users/dunnmk/Downloads/C_summary"   # adjust as needed
files  <- list.files(folder, pattern = "_summary\\.csv$", full.names = TRUE)

raw_list <- lapply(files, read_csv)

# Add batch / time / condition from file names
add_meta <- function(df, fname) {
  base <- basename(fname)
  
  batch     <- stringr::str_extract(base, "batch\\d+")
  time      <- stringr::str_extract(base, "T\\d+")          # e.g. T0, T120
  condition <- ifelse(stringr::str_detect(base, "_3C_"), "3C", "no3C")
  
  df %>%
    mutate(
      batch     = batch,
      time      = time,
      condition = condition
    )
}

dat <- purrr::map2_dfr(raw_list, files, add_meta)

########################
# 2. Extract location from alignment_name
########################

dat <- dat %>%
  mutate(
    # e.g. CIS_A_to_B_DSB1_Chr12_L01 -> Chr12_L01
    location = stringr::str_extract(alignment_name, "Chr[^,]+")
  )

########################
# 3. Add per-location cis/trans counts by batch/time
########################

dat <- dat %>%
  group_by(batch, time, condition, location) %>%
  mutate(
    Cis_Location_Counts   = sum(count[cis_trans == "CIS"],   na.rm = TRUE),
    Trans_Location_Counts = sum(count[cis_trans == "TRANS"], na.rm = TRUE)
  ) %>%
  ungroup()

########################
# 4. Build per-location × time feature table
########################

loc_time <- dat %>%
  group_by(location, time) %>%
  summarise(
    Cis_Location_Counts   = sum(Cis_Location_Counts,   na.rm = TRUE),
    Trans_Location_Counts = sum(Trans_Location_Counts, na.rm = TRUE),
    Total_Location_Counts = Cis_Location_Counts + Trans_Location_Counts,
    Percent_Location_in_Cis   = 100 * Cis_Location_Counts   /
      Total_Location_Counts,
    Percent_Location_in_Trans = 100 * Trans_Location_Counts /
      Total_Location_Counts,
    .groups = "drop"
  )

########################
# 5. Wide table: one row per location, T0 & T120 features
########################

loc_time_wide <- loc_time %>%
  tidyr::pivot_wider(
    id_cols    = location,
    names_from = time,     # e.g. T0, T120
    values_from = c(
      Cis_Location_Counts,
      Trans_Location_Counts,
      Total_Location_Counts,
      Percent_Location_in_Cis,
      Percent_Location_in_Trans
    ),
    names_sep = "_"
  )

########################
# 6. Compute Δcis and Δtrans on the wide table
########################

loc_time_wide <- loc_time_wide %>%
  mutate(
    dCis   = Percent_Location_in_Cis_T120   - Percent_Location_in_Cis_T0,
    dTrans = Percent_Location_in_Trans_T120 - Percent_Location_in_Trans_T0
  )

########################
# 7. PCA using T0 & T120 features
########################

# after step where loc_time_wide (with dTrans) is defined:

loc_features <- loc_time_wide %>%
  mutate(
    log_total_T0   = log10(Total_Location_Counts_T0   + 1),
    log_total_T120 = log10(Total_Location_Counts_T120 + 1)
  ) %>%
  dplyr::select(
    Percent_Location_in_Cis_T0,
    Percent_Location_in_Trans_T0,
    Percent_Location_in_Cis_T120,
    Percent_Location_in_Trans_T120,
    log_total_T0,
    log_total_T120
  )

pca_res_time <- prcomp(loc_features, scale. = TRUE)

loc_pca_time <- as.data.frame(pca_res_time$x) %>%
  dplyr::bind_cols(loc_time_wide %>% dplyr::select(location, dTrans))


pca_res_time <- prcomp(loc_features, scale. = TRUE)

loc_pca_time <- as.data.frame(pca_res_time$x) %>%
  bind_cols(loc_time_wide %>% select(location, dCis, dTrans))

########################
# 8. PCA plot: locations in PC space,
#    colored by Δcis (T120 - T0)
########################

ggplot(loc_pca_time,
       aes(x = PC1, y = PC2,
           color = dCis,
           label = location)) +
  geom_point(size = 2) +
  geom_text(vjust = -0.5, size = 3, show.legend = FALSE) +
  scale_color_gradient2(
    low = "blue", mid = "white", high = "red",
    midpoint = 0,
    name = "Δ cis% (T120 - T0)"
  ) +
  theme_bw() +
  labs(
    title = "PCA clustering of locations (T0 & T120 features)",
    x = "PC1",
    y = "PC2"
  )
########################
# 8.5 PCA plot: locations in PC space,
#    colored by Δtrans (T120 - T0)
########################

library(ggrepel)  # if not installed: install.packages("ggrepel")

ggplot(loc_pca_time,
       aes(x = PC1, y = PC2,
           color = dTrans,
           label = location)) +
  geom_point(size = 2) +
  geom_text_repel(size = 3, show.legend = FALSE, max.overlaps = 50) +
  scale_color_gradient2(
    low = "blue", mid = "white", high = "red",
    midpoint = 0,
    name = "Δ trans% (T120 - T0)"
  ) +
  theme_bw() +
  labs(
    title = "PCA clustering of locations colored by Δtrans (T120 - T0)",
    x = "PC1",
    y = "PC2"
  )


########################
# 9. Alternative PCA: show separate T0 and T120 clouds,
#    colored by time
########################

loc_features_long <- loc_time %>%
  mutate(
    log_total = log10(Total_Location_Counts + 1)
  ) %>%
  select(location, time,
         Percent_Location_in_Cis,
         Percent_Location_in_Trans,
         log_total)

pca_res_long <- prcomp(
  loc_features_long %>% select(-location, -time),
  scale. = TRUE
)

loc_pca_long <- as.data.frame(pca_res_long$x) %>%
  bind_cols(loc_features_long %>% select(location, time))

install.packages("ggrepel")  # run once
library(ggrepel)

ggplot(loc_pca_long,
       aes(x = PC1, y = PC2,
           color = time)) +
  geom_point(size = 2) +
  geom_text_repel(aes(label = location),
                  size = 3,
                  max.overlaps = 50) +
  theme_bw() +
  labs(
    title = "PCA of locations colored by time (T0 vs T120)",
    x = "PC1",
    y = "PC2",
    color = "Time"
  )
library(tidyverse)

# start from your combined table
# dat has: alignment_name, cis_trans, combo, count, batch, condition, time, ...

# 1) Per-sample CIS / TRANS totals
cis_trans_feats <- dat %>%
  group_by(alignment_name) %>%
  summarise(
    cis_total   = sum(count[cis_trans == "CIS"],   na.rm = TRUE),
    trans_total = sum(count[cis_trans == "TRANS"], na.rm = TRUE)
  )

# 2) Per-sample specific trans combos
combo_feats <- dat %>%
  group_by(alignment_name) %>%
  summarise(
    trans_A_to_D = sum(count[cis_trans == "TRANS" & combo == "A_to_D"], na.rm = TRUE),
    trans_C_to_B = sum(count[cis_trans == "TRANS" & combo == "C_to_B"], na.rm = TRUE)
  )

# 3) Join into one feature matrix
feature_mat <- cis_trans_feats %>%
  left_join(combo_feats, by = "alignment_name") %>%
  replace_na(list(
    cis_total = 0, trans_total = 0,
    trans_A_to_D = 0, trans_C_to_B = 0
  ))

View(feature_mat)

# 11. Save all ggplots to the same folder as the CSVs

# list of plots you want to save
plot_list <- list(
  CT_time        = p_CT_time,
  loc_time_batch = p_loc_time_batch,
  fc_overall     = p_fc_overall,
  pca_freq       = p_pca_freq,
  pca_fc         = p_pca_fc,
  pca_trans      = p_pca_trans
)

# save each as PNG in the same folder
for (nm in names(plot_list)) {
  outfile <- file.path(folder, paste0(nm, ".png"))
  ggsave(filename = outfile,
         plot     = plot_list[[nm]],
         width    = 8,
         height   = 6,
         dpi      = 300)
}


