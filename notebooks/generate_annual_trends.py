#!/usr/bin/env python3
"""Annual stacked-area timeline-point trends, 1996-2025, by family.

Reads the frozen snapshot CSV and produces a stacked area chart with
burst-year vertical annotations.

Sizing: 6.85 x 4.5 in, 300 DPI. Palette matches the PRISMA v2 figure.
"""
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SRC  = ROOT / "data_freeze/snapshots/2026.05.13/timeline_points.csv"
OUT  = ROOT / "manuscript/figures/fig_annual_trends.png"

YEAR_MIN, YEAR_MAX = 1996, 2025

# Family group: collapse SCLib labels into the eight families used in the
# manuscript figures so the stacked area mirrors the family tables.
FAMILY_ORDER = [
    "cuprate",
    "iron-based",
    "hydride",
    "conventional",
    "elemental",
    "chalcogenide",
    "heavy-fermion",
    "kagome",
    "nickelate",
    "fulleride",
    "Other",
]

ALIASES = {
    "iron_based": "iron-based",
    "iron-pnictide": "iron-based",
    "iron pnictide": "iron-based",
    "heavy_fermion": "heavy-fermion",
    "heavy fermion": "heavy-fermion",
    "borocarbide": "conventional",
    "boride": "conventional",
    "intermetallic": "conventional",
    "alloy": "conventional",
    "carbide": "conventional",
    "nitride": "conventional",
    "organic": "Other",
    "ruthenate": "Other",
    "topological": "Other",
    "skyrmion": "Other",
    "kagome_metal": "kagome",
    "kagome metal": "kagome",
}

def normalize(fam: str) -> str:
    f = (fam or "").strip().lower()
    if not f or f in {"none", "null", "unknown", "n/a"}:
        return "Other"
    if f in ALIASES:
        return ALIASES[f]
    for key in FAMILY_ORDER:
        if f == key.lower():
            return key
    if "cuprate" in f or "yba" in f or "bisr" in f or "hgba" in f:
        return "cuprate"
    if "iron" in f:
        return "iron-based"
    if "hydride" in f or "h3s" in f:
        return "hydride"
    if "fullerene" in f or "fulleride" in f:
        return "fulleride"
    if "chalcog" in f:
        return "chalcogenide"
    if "nickel" in f:
        return "nickelate"
    if "kagome" in f:
        return "kagome"
    if "heavy" in f:
        return "heavy-fermion"
    if "convent" in f or "bcs" in f or "borocarbide" in f:
        return "conventional"
    if "element" in f:
        return "elemental"
    return "Other"

# ── Load and aggregate ────────────────────────────────────────────────────
counts: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
with open(SRC, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            y = int(float(row["year"]))
        except (KeyError, ValueError, TypeError):
            continue
        if y < YEAR_MIN or y > YEAR_MAX:
            continue
        fam = normalize(row.get("family") or "")
        counts[y][fam] += 1

years = list(range(YEAR_MIN, YEAR_MAX + 1))
stacks = {fam: [counts[y].get(fam, 0) for y in years] for fam in FAMILY_ORDER}

# ── Plot ──────────────────────────────────────────────────────────────────
# Warm palette consistent with the PRISMA v2 figure
PALETTE = {
    "cuprate":        "#C9885F",   # warm terracotta
    "iron-based":     "#A87155",
    "hydride":        "#D4A574",
    "conventional":   "#8E7B5E",
    "elemental":      "#B8A988",
    "chalcogenide":   "#7C9885",
    "heavy-fermion":  "#6E7F8A",
    "kagome":         "#9C7F8E",
    "nickelate":      "#C2807E",
    "fulleride":      "#A89F76",
    "Other":          "#BFB7A6",
}

fig, ax = plt.subplots(figsize=(6.85, 4.5), dpi=300)
fig.patch.set_facecolor("#FAFAF8")
ax.set_facecolor("#FAFAF8")

ax.stackplot(
    years,
    [stacks[f] for f in FAMILY_ORDER],
    labels=FAMILY_ORDER,
    colors=[PALETTE[f] for f in FAMILY_ORDER],
    alpha=0.92,
    edgecolor="#FAFAF8",
    linewidth=0.4,
)

# Burst-year vertical annotations
BURSTS = [
    (2001, "MgB$_2$"),
    (2008, "Iron-based"),
    (2015, "Hydride"),
    (2021, "Kagome"),
    (2023, "Nickelate"),
]
total_per_year = [sum(stacks[f][i] for f in FAMILY_ORDER) for i in range(len(years))]
y_top = max(total_per_year) * 1.08
ax.set_ylim(0, y_top)

for yr, label in BURSTS:
    if YEAR_MIN <= yr <= YEAR_MAX:
        ax.axvline(yr, color="#5A4A3A", linestyle=":", linewidth=0.8, alpha=0.7)
        ax.text(
            yr, y_top * 0.97, label,
            rotation=90, va="top", ha="right",
            fontsize=7, color="#3A2E22",
        )

ax.set_xlim(YEAR_MIN, YEAR_MAX)
ax.set_xlabel("Year", fontsize=10, color="#3A2E22")
ax.set_ylabel("Timeline points (per year)", fontsize=10, color="#3A2E22")
ax.set_title(
    "Annual SCLib timeline points by family, 1996–2025",
    fontsize=11, color="#3A2E22", pad=8,
)

for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color("#8E7B5E")
ax.tick_params(colors="#3A2E22", labelsize=8.5)
ax.grid(True, axis="y", linestyle=":", color="#C9C2B2", alpha=0.5, linewidth=0.6)

leg = ax.legend(
    loc="upper left", fontsize=7.5, ncol=2, frameon=False,
    labelcolor="#3A2E22", handlelength=1.2, handletextpad=0.4,
    columnspacing=0.8, borderaxespad=0.4,
)

plt.tight_layout()
plt.savefig(OUT, dpi=300, facecolor="#FAFAF8", bbox_inches="tight")
print(f"wrote {OUT}")

# Sanity print: total points captured
total = sum(total_per_year)
print(f"total timeline points 1996-2025: {total}")
print(f"family totals: {[(f, sum(stacks[f])) for f in FAMILY_ORDER]}")
