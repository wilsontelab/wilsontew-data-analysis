# Quality-Stratified Read-Length Distribution Analysis

## Summary

This analysis stratifies read-length distributions by **alignment quality metrics** to compare how reads of different quality levels differ in their length profiles. This reveals whether quality score biases affect the observed length distributions.

---

## Key Findings

### Quality Metrics Distribution

| Metric | Mean | Std Dev | Min | Q25 | Median | Q75 | Max |
|--------|------|---------|-----|-----|--------|-----|-----|
| **MAPQ** (Mapping Quality) | 50.08 | 20.20 | 0 | 60 | 60 | 60 | 60 |
| **AS** (Alignment Score) | 555.59 | 407.93 | -117 | 250 | 432 | 720 | 5760 |
| **NM** (Edit Distance) | 13.64 | 25.91 | 0 | 1 | 5 | 12 | 516 |

**Key Observation**: MAPQ is nearly uniform (75% of reads have MAPQ=60, indicating very high mapping quality). **AS (Alignment Score)** shows substantial variation across the range [-117, 5760], making it a better metric for stratified comparison.

---

## Generated Plots

### 1. **MAPQ-Based Stratification**

Since MAPQ is uniform, all 299,630 reads fall into a single quantile (Q1: MAPQ=[0-60]). The plots generated are:

- **`read_length_kde_quantile_overlay_by_mapq_*.png`** — Overlay KDE plot showing combined distribution
- **`read_length_distribution_comparison_mapq_*.png`** — Violin and box plots (single quantile)

### 2. **AS-Based Stratification (5 Quantiles)**

AS scores are split into 5 quantiles, each containing ~60,000 reads:

| Quantile | AS Score Range | Read Count | Quality Level |
|----------|---|---|---|
| **Q1** | [-117, 236] | 61,433 | Low (weak alignments) |
| **Q2** | [237, 333] | 58,420 | Medium-Low |
| **Q3** | [334, 514] | 61,323 | Medium |
| **Q4** | [515, 818] | 58,693 | Medium-High |
| **Q5** | [819, 5760] | 59,761 | High (strong alignments) |

#### Generated Plots:

- **`read_length_kde_quantile_overlay_by_as_batch4_2_4C_t0_by_AS.png`** — Overlay KDE for all 5 AS quantiles (sample-level)
- **`read_length_kde_quantile_overlay_by_as_t0_by_AS.png`** — Overlay KDE for all 5 AS quantiles (timepoint-level)
- **`read_length_kde_facet_by_chromosome_as_*.png`** — Individual faceted KDE plots per chromosome for each AS quantile
- **`read_length_distribution_comparison_mapq_*.png`** — Violin and box plots comparing read-length distributions across AS quantiles

---

## Key Insights from Plots

### Overlay KDE by AS Quantile (batch4_2_4C_t0)

The overlay plot shows **distinct distribution shifts** across AS quantiles:

- **Q1 (Low AS)**: Narrow, sharp peak at ~250-300 bp (strong short-read bias in weaker alignments)
- **Q2**: Broader distribution, peak shifts to ~350-400 bp
- **Q3**: More complex bimodal pattern with peaks at ~400 bp and ~600-700 bp
- **Q4**: Additional long-read tail emerges; peaks at ~450-500 bp and ~700-800 bp
- **Q5 (High AS)**: Broadest distribution with multiple modes up to 1200+ bp (high-quality alignments include longer reads)

**Interpretation**: High-quality alignments (Q5) capture a wider range of fragment lengths, while lower-quality alignments are biased toward shorter fragments. This suggests:
1. Short reads are easier to align uniquely (high specificity)
2. Long reads are more challenging to align but when successful, align with high confidence
3. Length-based filtering without quality control could inadvertently select for weak alignments

---

## Files Generated

### Overlay Plots
```
read_length_kde_quantile_overlay_by_as_batch4_2_4C_t0_by_AS.png
read_length_kde_quantile_overlay_by_as_t0_by_AS.png
read_length_kde_quantile_overlay_by_mapq_batch4_2_4C_t0.png
read_length_kde_quantile_overlay_by_mapq_t0.png
```

### Distribution Comparison (Violin & Box Plots)
```
read_length_distribution_comparison_mapq_batch4_2_4C_t0.png
read_length_distribution_comparison_mapq_batch4_2_4C_t0_by_AS.png
read_length_distribution_comparison_mapq_t0.png
read_length_distribution_comparison_mapq_t0_by_AS.png
```

### Faceted Chromosome Plots (by AS Quantile)
```
read_length_kde_facet_by_chromosome_as_batch4_2_4C_t0_by_AS_Q1...Q5.png
read_length_kde_facet_by_chromosome_as_t0_by_AS_Q1...Q5.png
```

---

## Recommended Use

1. **Quality Control**: Use the AS-stratified distributions to identify if read-length filtering needs adjustment by quality level
2. **Comparative Analysis**: Compare the quantile overlays across samples/timepoints to detect quality-biased shifts
3. **Peak Analysis**: Examine per-chromosome KDE facets to understand if specific genomic regions are preferentially captured at certain quality levels
4. **Publication**: The overlay KDE plots are suitable for publication as supplementary figures showing quality effects

---

## Next Steps

If needed, you can:
- Add stratification by **NM (edit distance)** to see mismatch biases
- Generate statistics (mean, median, percentiles) for each quality quantile
- Create heatmaps showing how peak positions shift across quality/chromosome combinations
- Filter by quality tier and re-analyze contact maps to see if conclusions change

---

## Technical Details

**Code Location**: Cell `#VSC-bce8dccc` and `#VSC-3531e122` in notebook  
**Plotting Library**: seaborn (kdeplot, violinplot, boxplot)  
**Quantile Method**: `pd.qcut()` with `duplicates='drop'`  
**Binning**: Reads windsorized at 99.5th percentile for visualization clarity
