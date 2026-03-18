"""Patch FourC_Joey_Filtered.ipynb to add STATE_DISPLAY_LABELS to
the segment-map and heatmap cells so Q1/Q2 filtering intent is clear
in chart titles."""
import json
import pathlib

nb_path = pathlib.Path(__file__).parent.parent / "FourC_Joey_Filtered.ipynb"
nb = json.loads(nb_path.read_text(encoding="utf-8"))


def join_source(cell):
    return "".join(cell["source"])


def set_source(cell, text):
    lines = text.splitlines(keepends=True)
    cell["source"] = lines


STATE_DISPLAY_LABELS_CODE = """\
# Human-readable display labels for each filter state.
# "q1_q2_filtered" = Q1 and Q2 (the two LOWEST AS quintiles) were REMOVED;
# only Q3, Q4, Q5 (better-quality alignments) remain in these maps.
STATE_DISPLAY_LABELS = {
    'non_filtered': 'non-filtered (all reads)',
    'q1_q2_filtered': 'Q1+Q2 excluded (lowest AS quintiles removed – Q3-Q5 retained)',
}
"""

modified = 0
for cell in nb["cells"]:
    if cell.get("cell_type") != "code":
        continue
    src = join_source(cell)

    # ---- Segment chromosome map cell ----
    if (
        "_plot_chromosome_map" in src
        and "chr_map_figs" in src
        and "state_bin_sources" in src
    ):
        if "STATE_DISPLAY_LABELS" not in src:
            src = src.replace(
                "# Build state-aware datasets (fallback keeps compatibility if only bin_counts exists)\nstate_bin_sources = []",
                STATE_DISPLAY_LABELS_CODE
                + "# Build state-aware datasets (fallback keeps compatibility if only bin_counts exists)\nstate_bin_sources = []",
            )

        if "state_display = STATE_DISPLAY_LABELS" not in src:
            # Try loop with single-quoted groupby
            src = src.replace(
                "for state_label, bdf in state_bin_sources:\n    for sample_name, sdf in bdf.groupby('sample'):",
                "for state_label, bdf in state_bin_sources:\n    state_display = STATE_DISPLAY_LABELS.get(state_label, state_label)\n    for sample_name, sdf in bdf.groupby('sample'):",
            )
            # Also try double-quoted groupby fallback
            src = src.replace(
                'for state_label, bdf in state_bin_sources:\n    for sample_name, sdf in bdf.groupby("sample"):',
                'for state_label, bdf in state_bin_sources:\n    state_display = STATE_DISPLAY_LABELS.get(state_label, state_label)\n    for sample_name, sdf in bdf.groupby("sample"):',
            )

        # Fix title strings (both older and newer variants)
        src = src.replace(
            "f'all bins | {state_label}'", "f'all bins | {state_display}'"
        )
        src = src.replace(
            "f'top {CHR_MAP_TOP_HITS_N} bins by count | {state_label}'",
            "f'top {CHR_MAP_TOP_HITS_N} bins by count | {state_display}'",
        )
        src = src.replace(
            "_plot_chromosome_map(sdf, sample_name, 'all bins')",
            "_plot_chromosome_map(sdf, sample_name, f'all bins | {state_display}')",
        )
        src = src.replace(
            "f'top {CHR_MAP_TOP_HITS_N} bins by count'",
            "f'top {CHR_MAP_TOP_HITS_N} bins by count | {state_display}'",
        )
        set_source(cell, src)
        modified += 1
        has_sdl = "STATE_DISPLAY_LABELS" in src
        has_sd = "state_display" in src
        print(
            f"[SEGMENT MAP] patched. STATE_DISPLAY_LABELS={has_sdl}, state_display={has_sd}"
        )
        if not has_sdl or not has_sd:
            print("  WARNING: patch may be incomplete – check source manually")
            # Print a snippet for debugging
            idx = src.find("state_bin_sources")
            print("  SNIPPET:", repr(src[idx:idx+200]))

    # ---- Heatmap cell ----
    if (
        "_plot_heatmap" in src
        and "chr_map_heatfreq_figs" in src
        and "state_bin_sources" in src
    ):
        if "STATE_DISPLAY_LABELS" not in src:
            src = src.replace(
                "# ---- Run both plots for BOTH filter states ----",
                STATE_DISPLAY_LABELS_CODE
                + "# ---- Run both plots for BOTH filter states ----",
            )

        if "state_display = STATE_DISPLAY_LABELS" not in src:
            src = src.replace(
                'for state_label, bdf in state_bin_sources:\n    for sample_name, sdf in bdf.groupby("sample"):',
                'for state_label, bdf in state_bin_sources:\n    state_display = STATE_DISPLAY_LABELS.get(state_label, state_label)\n    for sample_name, sdf in bdf.groupby("sample"):',
            )

        src = src.replace(
            'f"regional hit-frequency heatmap | {state_label}"',
            'f"regional hit-frequency heatmap | {state_display}"',
        )
        src = src.replace(
            'f"TOP {TOP_N} binned hits heatmap (labeled) | {state_label}"',
            'f"TOP {TOP_N} binned hits heatmap (labeled) | {state_display}"',
        )
        set_source(cell, src)
        modified += 1
        has_sdl = "STATE_DISPLAY_LABELS" in src
        has_sd = "state_display" in src
        print(
            f"[HEATMAP] patched. STATE_DISPLAY_LABELS={has_sdl}, state_display={has_sd}"
        )
        if not has_sdl or not has_sd:
            print("  WARNING: patch may be incomplete")

print(f"\nTotal cells modified: {modified}")
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print("Notebook saved to disk.")
