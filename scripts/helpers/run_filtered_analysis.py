#!/usr/bin/env python3
"""
Filtered Analysis: Excluding Q1 (Lowest AS scores - Self-Ligation Artifacts)
Run this script in the notebook kernel context to generate Q1-filtered plots
"""
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# ==============================================================================
# FILTERED ANALYSIS: Excluding Q1 (Lowest AS scores - Self-Ligation Artifacts)
# ==============================================================================
print('\n' + '='*80)
print('FILTERED 4C ANALYSIS: Excluding Q1 (Lowest Alignment Scores)')
print('='*80 + '\n')

# Step 1: Identify Q1 threshold
as_clean_q1 = readlen_df_with_quality.dropna(subset=['AS']).copy()
as_clean_q1['qscore_quantile'] = pd.qcut(as_clean_q1['AS'], q=5, labels=False, duplicates='drop')

# Get Q1 (lowest quintile) max value
q1_max = as_clean_q1[as_clean_q1['qscore_quantile'] == 0]['AS'].max()
q1_min = as_clean_q1[as_clean_q1['qscore_quantile'] == 0]['AS'].min()
print(f'Q1 AS range: {q1_min:.0f} - {q1_max:.0f}')
print(f'Filtering out reads with AS <= {q1_max:.0f}\n')

# Step 2: Filter out Q1 from best_alignments
best_alignments_filtered = best_alignments[best_alignments['AS'] > q1_max].copy()
n_removed = len(best_alignments) - len(best_alignments_filtered)
pct_removed = 100.0 * n_removed / len(best_alignments)

print(f'Original alignment count: {len(best_alignments):,}')
print(f'After Q1 removal: {len(best_alignments_filtered):,}')
print(f'Reads removed: {n_removed:,} ({pct_removed:.1f}%)\n')

# Step 3: ChrV analysis before and after filtering
chrv_before = len(best_alignments[best_alignments['chrom'] == 'chrV'])
chrv_after = len(best_alignments_filtered[best_alignments_filtered['chrom'] == 'chrV'])
chrv_removed = chrv_before - chrv_after
chrv_pct_before = 100.0 * chrv_before / len(best_alignments)
chrv_pct_after = 100.0 * chrv_after / len(best_alignments_filtered)

print(f'ChrV analysis:')
print(f'  Before filtering: {chrv_before:,} reads ({chrv_pct_before:.2f}%)')
print(f'  After filtering: {chrv_after:,} reads ({chrv_pct_after:.2f}%)')
print(f'  ChrV reads removed: {chrv_removed:,} ({100.0*chrv_removed/chrv_before:.1f}% of chrV reads)')
print(f'  Improvement: {chrv_pct_before - chrv_pct_after:.2f} percentage points reduction in chrV dominance\n')

# Step 4: Rebuild binned contacts for filtered data
df_filt = best_alignments_filtered.copy()
df_filt = df_filt[df_filt['chrom'].notna() & (df_filt['chrom'] != '*')].copy()
df_filt['bin_start'] = ((df_filt['pos'] - 1) // BIN_SIZE) * BIN_SIZE + 1
df_filt['bin_end'] = df_filt['bin_start'] + BIN_SIZE - 1
df_filt['bin_id'] = df_filt['chrom'].astype(str) + ':' + df_filt['bin_start'].astype(str) + '-' + df_filt['bin_end'].astype(str)

bin_counts_filtered = (
    df_filt.groupby(['sample', 'time_point', 'chrom', 'bin_start', 'bin_end', 'bin_id'], as_index=False)
      .size()
      .rename(columns={'size': 'count'})
)
bin_counts_filtered['freq'] = bin_counts_filtered.groupby('sample')['count'].transform(lambda x: x / x.sum())

print(f'Binned contacts (filtered): {len(bin_counts_filtered):,} bins')

# Step 5: Generate TOP CONTACT BINS plot (filtered)
print('\nGenerating top contact bins plot (Q1-filtered)...\n')

def _short_bin_label_filt(bin_id: str):
    if ':' not in str(bin_id):
        return str(bin_id)
    chrom, span = str(bin_id).split(':', 1)
    if '-' not in span:
        return str(bin_id)
    start_s, end_s = span.split('-', 1)
    try:
        start_k = int(start_s) // 1000
        end_k = int(end_s) // 1000
        return f"{chrom}:{start_k}k-{end_k}k"
    except ValueError:
        return str(bin_id)

chrom_order_index = {c: i for i, c in enumerate(CHROM_ORDER)}
fallback_colors = sns.color_palette('husl', 24).as_hex()

for sample_name, sdf in bin_counts_filtered.groupby('sample'):
    chrom_rank = (
        sdf.groupby('chrom', as_index=False)['count'].sum()
        .sort_values('count', ascending=False)
        .head(CONTACT_PLOT_TOP_CHROMS)
    )
    chosen_chroms = set(chrom_rank['chrom'].tolist())

    candidate = sdf[sdf['chrom'].isin(chosen_chroms)].copy()
    candidate = candidate.sort_values(['chrom', 'count'], ascending=[True, False])
    per_chrom_top = candidate.groupby('chrom', as_index=False).head(CONTACT_PLOT_BINS_PER_CHROM).copy()

    p = per_chrom_top.sort_values('count', ascending=False).head(CONTACT_PLOT_MAX_BARS).copy()
    p['bin_label_short'] = p['bin_id'].map(_short_bin_label_filt)

    p['chrom_order'] = p['chrom'].map(lambda x: chrom_order_index.get(x, 10_000))
    p = p.sort_values(['chrom_order', 'count'], ascending=[True, False]).reset_index(drop=True)

    hue_order = [c for c in CHROM_ORDER if c in set(p['chrom'])]
    extra_chroms = sorted([c for c in pd.unique(p['chrom']) if c not in set(hue_order)])
    hue_order.extend(extra_chroms)

    palette_map = {}
    for i, chrom in enumerate(hue_order):
        palette_map[chrom] = CHROM_PALETTE.get(chrom, fallback_colors[i % len(fallback_colors)])

    x_order = p['bin_label_short'].tolist()

    plt.figure(figsize=(15, 5))
    ax = sns.barplot(
        data=p,
        x='bin_label_short',
        y='count',
        hue='chrom',
        order=x_order,
        hue_order=hue_order,
        dodge=False,
        palette=palette_map
    )
    ax.set_title(f'Top contact bins (Q1-filtered, balanced by chromosome) | {sample_name}')
    ax.set_xlabel('Genomic bin (short label)')
    ax.set_ylabel('Read count (best-hit)')

    n_labels = len(p)
    step = max(1, n_labels // 16)
    for i, tick in enumerate(ax.get_xticklabels()):
        tick.set_rotation(70)
        tick.set_fontsize(8)
        tick.set_visible(i % step == 0)

    top_n_annot = min(8, len(p))
    top_rows = p.sort_values('count', ascending=False).head(top_n_annot)
    x_lookup = {lab: idx for idx, lab in enumerate(x_order)}
    for _, row in top_rows.iterrows():
        x_idx = x_lookup.get(row['bin_label_short'])
        if x_idx is not None:
            ax.text(
                x_idx,
                row['count'],
                f"{int(row['count']):,}",
                ha='center',
                va='bottom',
                fontsize=8,
                rotation=90
            )

    plt.legend(title='chrom', bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()
    plt.show()

# Step 6: Generate ALL BINS plot (filtered)
print('Generating all contact bins plot (Q1-filtered)...\n')

for sample_name, sdf in bin_counts_filtered.groupby('sample'):
    p_all = sdf.copy()
    p_all['chrom_order'] = p_all['chrom'].map(lambda x: chrom_order_index.get(x, 10_000))
    p_all = p_all.sort_values(['chrom_order', 'chrom', 'bin_start'], ascending=[True, True, True]).reset_index(drop=True)
    p_all['bin_label_short'] = p_all['bin_id'].map(_short_bin_label_filt)

    hue_order_all = [c for c in CHROM_ORDER if c in set(p_all['chrom'])]
    extra_chroms_all = sorted([c for c in pd.unique(p_all['chrom']) if c not in set(hue_order_all)])
    hue_order_all.extend(extra_chroms_all)

    palette_map_all = {}
    for i, chrom in enumerate(hue_order_all):
        palette_map_all[chrom] = CHROM_PALETTE.get(chrom, fallback_colors[i % len(fallback_colors)])

    x_order_all = p_all['bin_label_short'].tolist()

    fig_w = max(18, min(46, 0.16 * len(p_all)))
    plt.figure(figsize=(fig_w, 6))
    ax_all = sns.barplot(
        data=p_all,
        x='bin_label_short',
        y='count',
        hue='chrom',
        order=x_order_all,
        hue_order=hue_order_all,
        dodge=False,
        palette=palette_map_all
    )
    ax_all.set_title(f'All contact bins (Q1-filtered, color-coded by chromosome) | {sample_name}')
    ax_all.set_xlabel('Genomic bin (short label)')
    ax_all.set_ylabel('Read count (best-hit)')

    n_labels_all = len(p_all)
    step_all = max(1, n_labels_all // 35)
    for i, tick in enumerate(ax_all.get_xticklabels()):
        tick.set_rotation(80)
        tick.set_fontsize(7)
        tick.set_visible(i % step_all == 0)

    plt.legend(title='chrom', bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()
    plt.show()

print('✓ Filtered contact bin analysis complete!')
