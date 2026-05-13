#!/usr/bin/env python3
"""Generate PRISMA-ScR flow diagram using matplotlib.

Outputs: analysis_outputs/2026.05.13/fig_prisma_flow.png
         manuscript/figures/fig_prisma_flow.png
"""
import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis_outputs/2026.05.13/prisma_flow.json"
OUT_DIR = ROOT / "analysis_outputs/2026.05.13"
FIG_DIR = ROOT / "manuscript/figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Load numbers
with open(DATA) as f:
    raw = json.load(f)

# Flatten stages into dict by key
d = {s['key']: s['count'] for s in raw['stages']}
d['unique_materials'] = 3734

fig, ax = plt.subplots(figsize=(10, 14))
ax.set_xlim(0, 10)
ax.set_ylim(0, 14)
ax.axis('off')
ax.set_facecolor('white')
fig.patch.set_facecolor('white')

def box(ax, x, y, w, h, text, color='#E8F4FD', edge='#2980B9', fontsize=10, bold=False):
    """Draw a rounded rectangle with text."""
    rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                          boxstyle="round,pad=0.1",
                          facecolor=color, edgecolor=edge, linewidth=1.5, zorder=2)
    ax.add_patch(rect)
    weight = 'bold' if bold else 'normal'
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            weight=weight, wrap=True, zorder=3,
            multialignment='center')

def arrow(ax, x, y1, y2):
    ax.annotate('', xy=(x, y2 + 0.02), xytext=(x, y1 - 0.02),
                arrowprops=dict(arrowstyle='->', color='#555555', lw=1.5), zorder=1)

def excluded_box(ax, x, y, text):
    rect = FancyBboxPatch((x, y - 0.35), 3.5, 0.7,
                          boxstyle="round,pad=0.08",
                          facecolor='#FEF9E7', edgecolor='#E67E22', linewidth=1.2, zorder=2)
    ax.add_patch(rect)
    ax.text(x + 1.75, y, text, ha='center', va='center', fontsize=8.5,
            color='#7D6608', zorder=3, multialignment='center')

# ── Section headers ──────────────────────────────────────────────────────────
ax.text(1.0, 13.7, 'IDENTIFICATION', ha='center', va='center', fontsize=9,
        color='white', weight='bold',
        bbox=dict(boxstyle='round', facecolor='#2980B9', edgecolor='none', pad=0.4))
ax.text(1.0, 10.9, 'SCREENING', ha='center', va='center', fontsize=9,
        color='white', weight='bold',
        bbox=dict(boxstyle='round', facecolor='#27AE60', edgecolor='none', pad=0.4))
ax.text(1.0, 7.9, 'ELIGIBILITY', ha='center', va='center', fontsize=9,
        color='white', weight='bold',
        bbox=dict(boxstyle='round', facecolor='#8E44AD', edgecolor='none', pad=0.4))
ax.text(1.0, 4.7, 'INCLUDED', ha='center', va='center', fontsize=9,
        color='white', weight='bold',
        bbox=dict(boxstyle='round', facecolor='#C0392B', edgecolor='none', pad=0.4))

# ── Identification ────────────────────────────────────────────────────────────
box(ax, 5.0, 13.3, 6.5, 0.7,
    f"Records identified from arXiv cond-mat.supr-con\n(n = {d['records_identified']:,})",
    color='#D6EAF8', edge='#2980B9', fontsize=9.5)

arrow(ax, 5.0, 12.95, 12.2)

box(ax, 5.0, 11.9, 6.5, 0.6,
    f"Records after year filter (1996–2025)\n(n = {d['records_after_year_filter']:,})",
    color='#D6EAF8', edge='#2980B9', fontsize=9.5)

# ── Screening ─────────────────────────────────────────────────────────────────
arrow(ax, 5.0, 11.6, 11.0)

box(ax, 5.0, 10.65, 6.5, 0.7,
    f"Material records extracted by NER pipeline\n(n = {d['materials_extracted']:,})",
    color='#D5F5E3', edge='#27AE60', fontsize=9.5)

ax.annotate('', xy=(7.9, 10.65), xytext=(8.2, 10.65),
            arrowprops=dict(arrowstyle='->', color='#E67E22', lw=1.2))
excluded_box(ax, 6.3, 10.65,
             f"Records not meeting quality\n& provenance thresholds\n(n = {d['materials_extracted'] - d['materials_public']:,})")

arrow(ax, 5.0, 10.3, 9.6)

box(ax, 5.0, 9.25, 6.5, 0.7,
    f"Records in public SCLib materials database\n(n = {d['materials_public']:,})",
    color='#D5F5E3', edge='#27AE60', fontsize=9.5)

# ── Eligibility ───────────────────────────────────────────────────────────────
arrow(ax, 5.0, 8.9, 8.2)

box(ax, 5.0, 7.85, 6.5, 0.7,
    f"SCLib timeline points (all evidence types)\n(n = {d['timeline_points']:,})",
    color='#E8DAEF', edge='#8E44AD', fontsize=9.5)

ax.annotate('', xy=(7.9, 7.85), xytext=(8.2, 7.85),
            arrowprops=dict(arrowstyle='->', color='#E67E22', lw=1.2))
excluded_box(ax, 6.3, 7.85,
             f"Theoretical predictions\nexcluded from primary analysis\n(n = {d['timeline_points'] - d['experimental_only']:,})")

arrow(ax, 5.0, 7.5, 6.8)

box(ax, 5.0, 6.45, 6.5, 0.7,
    f"Experimental timeline points\n(n = {d['experimental_only']:,})",
    color='#E8DAEF', edge='#8E44AD', fontsize=9.5)

ax.annotate('', xy=(7.9, 6.45), xytext=(8.2, 6.45),
            arrowprops=dict(arrowstyle='->', color='#E67E22', lw=1.2))
excluded_box(ax, 6.3, 6.45,
             f"Outside analysis window\n(pre-1996 or 2026)\n(n = {d['experimental_only'] - d['experimental_1996_2025']:,})")

# ── Included ──────────────────────────────────────────────────────────────────
arrow(ax, 5.0, 6.1, 5.4)

box(ax, 5.0, 5.0, 6.5, 0.8,
    f"Records included in final analysis\nExperimental, 1996–2025\n(n = {d['experimental_1996_2025']:,})",
    color='#FADBD8', edge='#C0392B', fontsize=9.5, bold=True)

arrow(ax, 5.0, 4.6, 3.9)

box(ax, 5.0, 3.6, 6.5, 0.6,
    f"Unique canonical materials identified\n(n = {d.get('unique_materials', 3734):,})",
    color='#FADBD8', edge='#C0392B', fontsize=9.5)

# ── Title ─────────────────────────────────────────────────────────────────────
ax.text(5.0, 0.6, "PRISMA-ScR Flow Diagram\nSCLib Superconductivity Scoping Review (1996–2025)",
        ha='center', va='center', fontsize=10, style='italic', color='#555555')

plt.tight_layout(pad=0.5)
out_path = OUT_DIR / "fig_prisma_flow.png"
fig_path = FIG_DIR / "fig_prisma_flow.png"
plt.savefig(out_path, dpi=200, bbox_inches='tight', facecolor='white')
plt.savefig(fig_path, dpi=200, bbox_inches='tight', facecolor='white')
plt.close()
print(f"Saved: {out_path}")
print(f"Saved: {fig_path}")
