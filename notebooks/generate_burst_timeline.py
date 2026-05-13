#!/usr/bin/env python3
"""Burst score timeline: log(BS) per family per year, with burst-event arrows.

Reads family_year_bursts.csv from analysis_outputs and renders a line plot
showing each major family's burst-score trajectory. Annotates the canonical
events identified in the manuscript.

Sizing: 6.85 x 4.0 in, 300 DPI.
"""
import csv
from collections import defaultdict
from math import log10
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SRC  = ROOT / "analysis_outputs/2026.05.13/family_year_bursts.csv"
OUT  = ROOT / "manuscript/figures/fig_burst_timeline.png"

YEAR_MIN, YEAR_MAX = 1996, 2025
BS_FLOOR = 1.0  # only display families that exceed 1.0 in at least one year

# Families to plot (the dataset's labels, normalized for display)
DISPLAY = {
    "cuprate":       "Cuprate",
    "iron_based":    "Iron-based",
    "hydride":       "Hydride",
    "kagome":        "Kagome",
    "nickelate":     "Nickelate",
    "mgb2":          "MgB$_2$",
    "chalcogenide":  "Chalcogenide",
    "conventional":  "Conventional",
    "elemental":     "Elemental",
    "heavy_fermion": "Heavy-fermion",
    "fulleride":     "Fulleride",
}

# Warm palette consistent with the rest of the figure set
PALETTE = {
    "cuprate":       "#C9885F",
    "iron_based":    "#A87155",
    "hydride":       "#D4A574",
    "kagome":        "#9C7F8E",
    "nickelate":     "#C2807E",
    "mgb2":          "#8E7B5E",
    "chalcogenide":  "#7C9885",
    "conventional":  "#6B5D48",
    "elemental":     "#B8A988",
    "heavy_fermion": "#6E7F8A",
    "fulleride":     "#A89F76",
}

# Read all rows
rows = []
with open(SRC, newline="") as f:
    for r in csv.DictReader(f):
        try:
            y = int(r["year"])
            bs = float(r["burst_score"])
        except (KeyError, ValueError, TypeError):
            continue
        rows.append((r["family"], y, bs))

# Aggregate
series: dict[str, dict[int, float]] = defaultdict(dict)
for fam, y, bs in rows:
    if YEAR_MIN <= y <= YEAR_MAX and fam in DISPLAY:
        series[fam][y] = bs

# ── Plot ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(6.85, 4.0), dpi=300)
fig.patch.set_facecolor("#FAFAF8")
ax.set_facecolor("#FAFAF8")

xs_all = list(range(YEAR_MIN, YEAR_MAX + 1))
for fam, ymap in series.items():
    if max(ymap.values(), default=0) < BS_FLOOR:
        continue
    xs = [y for y in xs_all if y in ymap]
    ys = [log10(max(ymap[y], 0.05)) for y in xs]
    ax.plot(
        xs, ys,
        label=DISPLAY[fam],
        color=PALETTE[fam],
        linewidth=1.3,
        marker="o",
        markersize=2.5,
        alpha=0.92,
    )

ax.axhline(log10(3.0), color="#5A4A3A", linestyle="--", linewidth=0.7, alpha=0.6)
ax.text(YEAR_MAX, log10(3.0) + 0.04, "burst threshold $B=3$",
        ha="right", fontsize=7, color="#5A4A3A")

# Event arrows for the five named bursts
EVENTS = [
    (2002, log10(5.83), "MgB$_2$\n2001--2002"),
    (2008, log10(357.0), "Iron-based\n2008"),
    (2015, log10(3.75), "Hydride\n2015"),
    (2021, log10(15.5), "Kagome\n2021"),
    (2023, log10(2.68), "Nickelate\n2023+"),
]
for yr, ybs, label in EVENTS:
    ax.annotate(
        label,
        xy=(yr, ybs),
        xytext=(yr, ybs + 0.55),
        ha="center", va="bottom", fontsize=7, color="#3A2E22",
        arrowprops=dict(arrowstyle="-|>", color="#5A4A3A", lw=0.7,
                        shrinkA=0, shrinkB=2),
    )

ax.set_xlim(YEAR_MIN, YEAR_MAX)
ax.set_ylim(-1.2, 3.0)
ax.set_xlabel("Year", fontsize=10, color="#3A2E22")
ax.set_ylabel("log$_{10}$ burst score $B_{f,y}$",
              fontsize=10, color="#3A2E22")
ax.set_title("Family burst-score trajectories, 1996–2025",
             fontsize=11, color="#3A2E22", pad=8)

for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color("#8E7B5E")
ax.tick_params(colors="#3A2E22", labelsize=8.5)
ax.grid(True, axis="y", linestyle=":", color="#C9C2B2", alpha=0.5, linewidth=0.6)

ax.legend(loc="upper left", fontsize=7.5, ncol=2, frameon=False,
          labelcolor="#3A2E22", handlelength=1.5, handletextpad=0.4,
          columnspacing=0.8, borderaxespad=0.4)

plt.tight_layout()
plt.savefig(OUT, dpi=300, facecolor="#FAFAF8", bbox_inches="tight")
print(f"wrote {OUT}")
