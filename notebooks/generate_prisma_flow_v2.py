#!/usr/bin/env python3
"""Generate PRISMA-ScR flow diagram — publication-ready version.

Color palette: warm neutrals inspired by claude.ai
Sizing: double-column journal width (174mm = 6.85 in), 300 DPI
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as pe

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis_outputs/2026.05.13/prisma_flow.json"
OUT_DIR = ROOT / "analysis_outputs/2026.05.13"
FIG_DIR = ROOT / "manuscript/figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

with open(DATA) as f:
    raw = json.load(f)
d = {s['key']: s['count'] for s in raw['stages']}
d['unique_materials'] = 3734

# ── Claude-inspired warm neutral palette ────────────────────────────────────
BG        = '#FAFAF8'   # off-white background
CREAM     = '#F5F0E8'   # warm cream for main boxes
SAND      = '#EDE8DF'   # slightly darker for section pills
RUST      = '#C96442'   # terracotta accent (section labels)
RUST_DARK = '#A04E33'   # darker rust for arrows/borders
WARM_GRAY = '#8C8278'   # warm gray for excluded boxes & borders
CHARCOAL  = '#2C2825'   # near-black text
MED_GRAY  = '#B5AFA8'   # light border for excluded
EXCL_BG   = '#F5F2EE'   # very light warm for excluded boxes

# Journal double-column width = 6.85 in, height proportional
FIG_W = 6.85
FIG_H = 11.0
DPI   = 300

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 10)
ax.set_ylim(0, 14)
ax.axis('off')

# ── Helper functions ─────────────────────────────────────────────────────────

def main_box(ax, x, y, w, h, title, subtitle='', n=None):
    """Main funnel box: warm cream fill, charcoal text."""
    rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                          boxstyle="round,pad=0.12",
                          facecolor=CREAM, edgecolor=WARM_GRAY,
                          linewidth=0.8, zorder=2)
    ax.add_patch(rect)
    if n is not None:
        # Bold count
        ax.text(x, y + 0.15, f"n = {n:,}", ha='center', va='center',
                fontsize=9.5, weight='bold', color=RUST_DARK, zorder=3,
                fontfamily='serif')
        ax.text(x, y - 0.18, title, ha='center', va='center',
                fontsize=8, color=CHARCOAL, zorder=3, style='italic')
    else:
        ax.text(x, y, title, ha='center', va='center',
                fontsize=8.5, color=CHARCOAL, zorder=3)

def section_pill(ax, x, y, label, color=RUST):
    """Rotated vertical section label on the left margin."""
    ax.text(x, y, label, ha='center', va='center',
            fontsize=7, weight='bold', color='white',
            rotation=90, zorder=4,
            bbox=dict(boxstyle='round,pad=0.35', facecolor=color,
                      edgecolor='none'))

def down_arrow(ax, x, y_top, y_bot):
    ax.annotate('', xy=(x, y_bot + 0.05), xytext=(x, y_top - 0.05),
                arrowprops=dict(arrowstyle='->', color=WARM_GRAY,
                                lw=1.0, mutation_scale=12), zorder=1)

def side_arrow(ax, x_start, y):
    ax.annotate('', xy=(x_start + 0.12, y), xytext=(x_start - 0.12, y),
                arrowprops=dict(arrowstyle='->', color=MED_GRAY,
                                lw=0.8, mutation_scale=10), zorder=1)

def excl_box(ax, x_left, y, text):
    """Excluded box: dashed border, lighter fill."""
    w, h = 3.2, 0.65
    rect = FancyBboxPatch((x_left, y - h/2), w, h,
                          boxstyle="round,pad=0.09",
                          facecolor=EXCL_BG, edgecolor=MED_GRAY,
                          linewidth=0.7, linestyle='--', zorder=2)
    ax.add_patch(rect)
    ax.text(x_left + w/2, y, text, ha='center', va='center',
            fontsize=7.2, color=WARM_GRAY, zorder=3,
            multialignment='center')

# ── Layout constants ─────────────────────────────────────────────────────────
LEFT_PILL = 0.55   # x of section pills
CX = 5.0           # center x of main boxes
BW = 5.8           # box width
EXCL_X = 7.95      # left edge of excluded boxes

# Y positions (top to bottom)
Y = {
    'id1':    13.1,
    'id2':    11.8,
    'sc1':    10.5,
    'sc2':     9.2,
    'el1':     7.9,
    'el2':     6.6,
    'inc1':    5.1,
    'inc2':    3.8,
}

BH = 0.75  # box height

# ── Section pills ────────────────────────────────────────────────────────────
section_pill(ax, LEFT_PILL, (Y['id1'] + Y['id2']) / 2, 'IDENTIFICATION', RUST)
section_pill(ax, LEFT_PILL, (Y['sc1'] + Y['sc2']) / 2, 'SCREENING', '#7A6A60')
section_pill(ax, LEFT_PILL, (Y['el1'] + Y['el2']) / 2, 'ELIGIBILITY', '#7A6A60')
section_pill(ax, LEFT_PILL, (Y['inc1'] + Y['inc2']) / 2, 'INCLUDED', RUST)

# ── Main boxes ───────────────────────────────────────────────────────────────
main_box(ax, CX, Y['id1'], BW, BH,
         'Records identified via SCLib ingest\n(arXiv cond-mat.supr-con)',
         n=d['records_identified'])

down_arrow(ax, CX, Y['id1'] - BH/2, Y['id2'] + BH/2)

main_box(ax, CX, Y['id2'], BW, BH,
         'Records retained: 1996–2025 complete-year window',
         n=d['records_after_year_filter'])

down_arrow(ax, CX, Y['id2'] - BH/2, Y['sc1'] + BH/2)

main_box(ax, CX, Y['sc1'], BW, BH,
         'Material–paper records extracted by LLM-assisted NER',
         n=d['materials_extracted'])

# excluded: curation
side_arrow(ax, CX + BW/2, Y['sc1'])
excl_box(ax, EXCL_X, Y['sc1'],
         f"Excluded: duplicate, low-confidence,\nor needs-review records  (n = {d['materials_extracted'] - d['materials_public']:,})")

down_arrow(ax, CX, Y['sc1'] - BH/2, Y['sc2'] + BH/2)

main_box(ax, CX, Y['sc2'], BW, BH,
         'Canonical materials in public SCLib database',
         n=d['materials_public'])

down_arrow(ax, CX, Y['sc2'] - BH/2, Y['el1'] + BH/2)

main_box(ax, CX, Y['el1'], BW, BH,
         'SCLib timeline points (all evidence types, 1996–2025)',
         n=d['timeline_points'])

# excluded: theoretical
side_arrow(ax, CX + BW/2, Y['el1'])
excl_box(ax, EXCL_X, Y['el1'],
         f"Excluded: theoretical predictions\n(n = {d['timeline_points'] - d['experimental_only']:,})")

down_arrow(ax, CX, Y['el1'] - BH/2, Y['el2'] + BH/2)

main_box(ax, CX, Y['el2'], BW, BH,
         'Experimental timeline points (full corpus)',
         n=d['experimental_only'])

# excluded: outside window
side_arrow(ax, CX + BW/2, Y['el2'])
excl_box(ax, EXCL_X, Y['el2'],
         f"Excluded: outside 1996–2025 window\n(n = {d['experimental_only'] - d['experimental_1996_2025']:,})")

down_arrow(ax, CX, Y['el2'] - BH/2, Y['inc1'] + BH/2)

# Included — slightly more prominent box
rect_inc = FancyBboxPatch((CX - BW/2, Y['inc1'] - BH/2), BW, BH,
                          boxstyle="round,pad=0.12",
                          facecolor=SAND, edgecolor=RUST_DARK,
                          linewidth=1.2, zorder=2)
ax.add_patch(rect_inc)
ax.text(CX, Y['inc1'] + 0.15, f"n = {d['experimental_1996_2025']:,}",
        ha='center', va='center', fontsize=10.5, weight='bold',
        color=RUST_DARK, zorder=3, fontfamily='serif')
ax.text(CX, Y['inc1'] - 0.20, 'Records included in final analysis  ·  Experimental, 1996–2025',
        ha='center', va='center', fontsize=8, color=CHARCOAL,
        zorder=3, style='italic')

down_arrow(ax, CX, Y['inc1'] - BH/2, Y['inc2'] + BH/2)

main_box(ax, CX, Y['inc2'], BW, BH,
         'Unique canonical materials identified',
         n=d['unique_materials'])

# ── Caption / footnote ───────────────────────────────────────────────────────
ax.text(CX, 2.8,
        'Fig. 1.  PRISMA-ScR flow diagram for the SCLib superconductivity scoping review (1996–2025).',
        ha='center', va='top', fontsize=7.5, color=WARM_GRAY,
        style='italic', wrap=True)

# ── Thin outer border ────────────────────────────────────────────────────────
for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout(pad=0.3)

out_path = OUT_DIR / "fig_prisma_flow_v2.png"
fig_path = FIG_DIR / "fig_prisma_flow.png"   # overwrite in figures/
plt.savefig(out_path, dpi=DPI, bbox_inches='tight', facecolor=BG)
plt.savefig(fig_path, dpi=DPI, bbox_inches='tight', facecolor=BG)
plt.close()
print(f"Saved: {out_path}  ({DPI} dpi, {FIG_W:.2f}×{FIG_H:.2f} in)")
print(f"Saved: {fig_path}")
