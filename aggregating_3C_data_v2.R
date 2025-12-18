########################
# 0. Packages
########################

library(tidyverse)

########################
# 1. Read and combine ALL CSVs
########################

folder <- "C:/Users/dunnmk/Downloads/C_summary"   # adjust as needed
files  <- list.files(folder, pattern = "_summary\\.csv$", full.names = TRUE)

raw_list <- lapply(files, read_csv)

# add batch / time / condition from file names
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

# cis: A_to_B and C_to_D
dat <- dat %>%
  group_by(batch, time, condition, allele) %>%
  mutate(
    Cis_Location_Counts = sum(count[cis_trans == "CIS"], na.rm = TRUE),
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

View(dat)

