#!/usr/bin/env python3
"""PRISMA-ScR flow diagram v3 — fixed borders, cleaner layout, for main text.

300 DPI, double-column width (6.85 in). All boxes have visible borders.
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis_outputs/2026.05.13/prisma_flow.json"
OUT_DIR = ROOT / "analysis_outputs/2026.05.13"
FIG_DIR = ROOT / "manuscript/figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

with open(DATA) as f:
    raw = json.load(f)
d = {s['key']: s['count'] for s in raw['stages']}
d['unique_materials'] = 3734

# ── Palette ───────────────────────────────────────────────────────────────────
BG        = '#FFFFFF'
MAIN_FILL = '#F7F3EE'
MAIN_EDGE = '#7A6A60'
INCL_FILL = '#EDE8DF'
INCL_EDGE = '#C96442'
EXCL_FILL = '#FAF8F5'
EXCL_EDGE = '#B5AFA8'
PILL_ID   = '#C96442'
PILL_SC   = '#8C8278'
PILL_EL   = '#8C8278'
PILL_IN   = '#C96442'
CHARCOAL  = '#2C2825'
ARROW_CLR = '#8C8278'

FIG_W, FIG_H = 7.0, 12.5
DPI = 300

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 10)
ax.set_ylim(0, 14)
ax.axis('off')

def main_box(ax, x, y, w, h, line1, line2='', lw=1.0,
             fill=MAIN_FILL, edge=MAIN_EDGE):
    rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                          boxstyle="round,pad=0.1",
                          facecolor=fill, edgecolor=edge,
                          linewidth=lw, zorder=3)
    ax.add_patch(rect)
    if line2:
        ax.text(x, y + 0.18, line1, ha='center', va='center',
                fontsize=8.5, color=CHARCOAL, weight='bold', zorder=4)
        ax.text(x, y - 0.22, line2, ha='center', va='center',
                fontsize=7.8, color='#6B6058', zorder=4, style='italic')
    else:
        ax.text(x, y, line1, ha='center', va='center',
                fontsize=8.5, color=CHARCOAL, zorder=4,
                multialignment='center')

def excl_box(ax, xl, y, w, h, text):
    rect = FancyBboxPatch((xl, y - h/2), w, h,
                          boxstyle="round,pad=0.08",
                          facecolor=EXCL_FILL, edgecolor=EXCL_EDGE,
                          linewidth=0.9, linestyle='--', zorder=3)
    ax.add_patch(rect)
    ax.text(xl + w/2, y, text, ha='center', va='center',
            fontsize=7.2, color='#7A6A60', zorder=4,
            multialignment='center')

def pill(ax, x, y, label, color):
    ax.text(x, y, label, ha='center', va='center',
            fontsize=7, weight='bold', color='white', rotation=90,
            bbox=dict(boxstyle='round,pad=0.4', facecolor=color, edgecolor='none'),
            zorder=5)

def down_arrow(ax, x, y1, y2):
    ax.annotate('', xy=(x, y2 + 0.04), xytext=(x, y1 - 0.04),
                arrowprops=dict(arrowstyle='->', color=ARROW_CLR,
                                lw=1.1, mutation_scale=13), zorder=2)

def side_arrow(ax, x1, x2, y):
    ax.annotate('', xy=(x2 - 0.05, y), xytext=(x1 + 0.05, y),
                arrowprops=dict(arrowstyle='->', color=EXCL_EDGE,
                                lw=0.9, mutation_scale=11), zorder=2)

# ── Layout ────────────────────────────────────────────────────────────────────
CX   = 4.7    # center x of main boxes
BW   = 5.8    # main box width
BH   = 0.80   # main box height
EXL  = 7.70   # left edge of excluded boxes
EW   = 2.20   # excluded box width
EH   = 0.70   # excluded box height
PX   = 0.55   # pill x

Y = dict(
    id1  = 13.1,
    id2  = 11.8,
    sc1  = 10.5,
    sc2  =  9.2,
    el1  =  7.9,
    el2  =  6.6,
    inc1 =  5.1,
    inc2 =  3.8,
)

# Pills
pill(ax, PX, (Y['id1']+Y['id2'])/2, 'IDENTIFICATION', PILL_ID)
pill(ax, PX, (Y['sc1']+Y['sc2'])/2, 'SCREENING',      PILL_SC)
pill(ax, PX, (Y['el1']+Y['el2'])/2, 'ELIGIBILITY',    PILL_EL)
pill(ax, PX, (Y['inc1']+Y['inc2'])/2,'INCLUDED',       PILL_IN)

# ── Identification ────────────────────────────────────────────────────────────
main_box(ax, CX, Y['id1'], BW, BH,
         f"Records identified via SCLib ingest",
         f"arXiv cond-mat.supr-con  ·  n = {d['records_identified']:,}")
down_arrow(ax, CX, Y['id1']-BH/2, Y['id2']+BH/2)
main_box(ax, CX, Y['id2'], BW, BH,
         f"Records after complete-year window filter (1996–2025)",
         f"n = {d['records_after_year_filter']:,}")

# ── Screening ────────────────────────────────────────────────────────────────
down_arrow(ax, CX, Y['id2']-BH/2, Y['sc1']+BH/2)
main_box(ax, CX, Y['sc1'], BW, BH,
         f"Material–paper records extracted by LLM NER pipeline",
         f"n = {d['materials_extracted']:,}")
side_arrow(ax, CX+BW/2, EXL, Y['sc1'])
excl_box(ax, EXL, Y['sc1'], EW, EH,
         f"Excluded: duplicate, low-confidence,\nneeds-review records\n"
         f"(n = {d['materials_extracted']-d['materials_public']:,})")

down_arrow(ax, CX, Y['sc1']-BH/2, Y['sc2']+BH/2)
main_box(ax, CX, Y['sc2'], BW, BH,
         f"Canonical materials in public SCLib database",
         f"n = {d['materials_public']:,}")

# ── Eligibility ───────────────────────────────────────────────────────────────
down_arrow(ax, CX, Y['sc2']-BH/2, Y['el1']+BH/2)
main_box(ax, CX, Y['el1'], BW, BH,
         f"SCLib timeline points — all evidence types (1996–2025)",
         f"n = {d['timeline_points']:,}")
side_arrow(ax, CX+BW/2, EXL, Y['el1'])
excl_box(ax, EXL, Y['el1'], EW, EH,
         f"Excluded: theoretical predictions\n"
         f"(n = {d['timeline_points']-d['experimental_only']:,})")

down_arrow(ax, CX, Y['el1']-BH/2, Y['el2']+BH/2)
main_box(ax, CX, Y['el2'], BW, BH,
         f"Experimental timeline points (full corpus)",
         f"n = {d['experimental_only']:,}")
side_arrow(ax, CX+BW/2, EXL, Y['el2'])
excl_box(ax, EXL, Y['el2'], EW, EH,
         f"Excluded: outside 1996–2025 window\n"
         f"(n = {d['experimental_only']-d['experimental_1996_2025']:,})")

# ── Included ──────────────────────────────────────────────────────────────────
down_arrow(ax, CX, Y['el2']-BH/2, Y['inc1']+BH/2)
# Highlighted included box
main_box(ax, CX, Y['inc1'], BW, BH+0.05,
         f"Records included in final analysis  ·  n = {d['experimental_1996_2025']:,}",
         "Experimental, 1996–2025",
         lw=1.8, fill=INCL_FILL, edge=INCL_EDGE)

down_arrow(ax, CX, Y['inc1']-BH/2-0.025, Y['inc2']+BH/2)
main_box(ax, CX, Y['inc2'], BW, BH,
         f"Unique canonical materials identified",
         f"n = {d['unique_materials']:,}")

# ── Caption ───────────────────────────────────────────────────────────────────
ax.text(CX, 2.75,
    "Fig. 1.  PRISMA-ScR flow diagram for the SCLib superconductivity scoping review (1996–2025).\n"
    "Dashed boxes indicate records excluded at each stage with reasons.",
    ha='center', va='top', fontsize=7.5, color='#7A6A60', style='italic',
    multialignment='center')

# ── Outer border ──────────────────────────────────────────────────────────────
outer = FancyBboxPatch((0.1, 2.55), 9.8, 11.2,
                       boxstyle="square,pad=0",
                       facecolor='none', edgecolor='#D0C8C0',
                       linewidth=0.8, zorder=1)
ax.add_patch(outer)

plt.tight_layout(pad=0.2)

out = OUT_DIR / "fig_prisma_flow_v3.png"
fig_out = FIG_DIR / "fig_prisma_flow.png"
plt.savefig(out, dpi=DPI, bbox_inches='tight', facecolor=BG)
plt.savefig(fig_out, dpi=DPI, bbox_inches='tight', facecolor=BG)
plt.close()
print(f"Saved: {out}")
print(f"Saved: {fig_out}")
