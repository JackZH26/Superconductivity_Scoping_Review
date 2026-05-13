#!/usr/bin/env python3
"""Burst timeline: grouped bar chart (replaces line chart).

Fixes: text overlap, log-scale outlier (BS=357), cross-family comparability.
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "manuscript/figures"
OUT_DIR = ROOT / "analysis_outputs/2026.05.13"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Palette (warm neutrals)
BG       = '#FAFAF8'
CHARCOAL = '#2C2825'
RUST     = '#C96442'
WARM_GRAY= '#8C8278'
SAND     = '#EDE8DF'

# ── Burst event data ──────────────────────────────────────────────────────────
# Five identified burst events with key metrics
events = [
    {"family": "MgB₂",        "year": 2002, "BS": 5.83,  "papers": 42,  "peak_tc": 39,  "color": "#6B9E78"},
    {"family": "Iron-based",   "year": 2008, "BS": 357.0, "papers": 312, "peak_tc": 55,  "color": "#C96442"},
    {"family": "Hydride",      "year": 2015, "BS": 3.75,  "papers": 28,  "peak_tc": 203, "color": "#5B7FA6"},
    {"family": "Kagome",       "year": 2021, "BS": 15.5,  "papers": 89,  "peak_tc": 4,   "color": "#9B7EC8"},
    {"family": "Nickelate",    "year": 2023, "BS": 2.68,  "papers": 41,  "peak_tc": 80,  "color": "#C4A35A"},
]

fig, axes = plt.subplots(1, 3, figsize=(6.85, 4.0))
fig.patch.set_facecolor(BG)
for ax in axes:
    ax.set_facecolor(BG)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(WARM_GRAY)
    ax.spines['bottom'].set_color(WARM_GRAY)
    ax.tick_params(colors=CHARCOAL, labelsize=7.5)

labels = [f"{e['family']}\n({e['year']})" for e in events]
colors = [e['color'] for e in events]
x = np.arange(len(events))
bar_w = 0.6

# ── Panel A: Burst Index (log scale) ─────────────────────────────────────────
ax = axes[0]
bs_vals = [e['BS'] for e in events]
bars = ax.bar(x, bs_vals, width=bar_w, color=colors, edgecolor='white', linewidth=0.5)
ax.set_yscale('log')
ax.axhline(3.0, color=RUST, lw=0.8, ls='--', alpha=0.7, label='Threshold B=3')
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=6.8, color=CHARCOAL)
ax.set_ylabel('Burst Index B (log scale)', fontsize=8, color=CHARCOAL)
ax.set_title('(a) Burst Index', fontsize=8.5, color=CHARCOAL, weight='bold', pad=6)
ax.legend(fontsize=6.5, framealpha=0, labelcolor=RUST)
# Annotate values
for bar, val in zip(bars, bs_vals):
    label = f'{val:.1f}' if val < 100 else f'{val:.0f}'
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.3,
            label, ha='center', va='bottom', fontsize=6.5, color=CHARCOAL)
ax.set_ylim(1, max(bs_vals) * 8)
ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())

# ── Panel B: Source paper count ───────────────────────────────────────────────
ax = axes[1]
paper_vals = [e['papers'] for e in events]
bars = ax.bar(x, paper_vals, width=bar_w, color=colors, edgecolor='white', linewidth=0.5)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=6.8, color=CHARCOAL)
ax.set_ylabel('Source papers in burst year', fontsize=8, color=CHARCOAL)
ax.set_title('(b) Publication Volume', fontsize=8.5, color=CHARCOAL, weight='bold', pad=6)
for bar, val in zip(bars, paper_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 4,
            str(val), ha='center', va='bottom', fontsize=7, color=CHARCOAL)
ax.set_ylim(0, max(paper_vals) * 1.2)

# ── Panel C: Peak Tc ──────────────────────────────────────────────────────────
ax = axes[2]
tc_vals = [e['peak_tc'] for e in events]
bars = ax.bar(x, tc_vals, width=bar_w, color=colors, edgecolor='white', linewidth=0.5)
ax.axhline(77, color='#5B7FA6', lw=0.8, ls='--', alpha=0.7, label='LN₂ threshold (77 K)')
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=6.8, color=CHARCOAL)
ax.set_ylabel('Peak T_c (K)', fontsize=8, color=CHARCOAL)
ax.set_title('(c) Peak T_c at Burst', fontsize=8.5, color=CHARCOAL, weight='bold', pad=6)
ax.legend(fontsize=6.5, framealpha=0, labelcolor='#5B7FA6')
for bar, val in zip(bars, tc_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
            f'{val} K', ha='center', va='bottom', fontsize=7, color=CHARCOAL)
ax.set_ylim(0, max(tc_vals) * 1.25)

# ── Note on non-comparability ─────────────────────────────────────────────────
fig.text(0.5, 0.01,
    'Note: Burst Index values are not directly comparable across families (corpus size varies by family and year).\n'
    'B is a descriptive ratio indicator; no statistical significance is claimed.',
    ha='center', fontsize=6.5, color=WARM_GRAY, style='italic')

plt.tight_layout(rect=[0, 0.06, 1, 1])

out = OUT_DIR / "fig_burst_bars.png"
fig_out = FIG_DIR / "fig_burst_timeline.png"
plt.savefig(out, dpi=300, bbox_inches='tight', facecolor=BG)
plt.savefig(fig_out, dpi=300, bbox_inches='tight', facecolor=BG)
plt.close()
print(f"Saved: {out}")
print(f"Saved: {fig_out}")
