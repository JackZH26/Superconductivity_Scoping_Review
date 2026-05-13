from pathlib import Path
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = PROJECT_ROOT / "data_freeze/snapshots/2026.05.13"
OUT_DIR = PROJECT_ROOT / "analysis_outputs/2026.05.13"


def band_count(frame: pd.DataFrame, lo: float, hi: float) -> int:
    return frame[(frame["tc_kelvin"] >= lo) & (frame["tc_kelvin"] < hi)].shape[0]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(SNAPSHOT_DIR / "metadata.json") as f:
        metadata = json.load(f)

    timeline = pd.read_csv(SNAPSHOT_DIR / "timeline_points.csv")
    materials = pd.read_csv(SNAPSHOT_DIR / "materials_default_summary.csv")

    df = timeline.copy()
    df["family"] = df["family"].fillna("Other").replace("", "Other")
    df["pressure_class"] = np.select(
        [
            df["pressure_gpa"].isna(),
            df["pressure_gpa"].fillna(0) <= 1,
            df["pressure_gpa"].fillna(0) > 1,
        ],
        ["unknown_pressure", "ambient_or_low_pressure", "high_pressure"],
        default="unknown_pressure",
    )
    df["evidence"] = np.where(
        df["is_theoretical"].astype(bool), "theoretical", "experimental"
    )
    df["evidence_regime"] = df["evidence"] + "_" + df["pressure_class"]
    main_df = df[df["year"].between(1996, 2025)].copy()

    bands = [
        ("0-10", 0, 10),
        ("10-20", 10, 20),
        ("20-30", 20, 30),
        ("30-40", 30, 40),
        ("40-50", 40, 50),
        ("50-60", 50, 60),
        ("60-70", 60, 70),
        ("70-80", 70, 80),
        ("80-90", 80, 90),
        ("90-100", 90, 100),
        ("100-120", 100, 120),
        ("120-150", 120, 150),
        ("150-200", 150, 200),
        ("200-251", 200, 251),
    ]

    band_rows = []
    for band, lo, hi in bands:
        sub = main_df[(main_df["tc_kelvin"] >= lo) & (main_df["tc_kelvin"] < hi)]
        band_rows.append(
            {
                "band": band,
                "lower_k": lo,
                "upper_k": hi,
                "width_k": hi - lo,
                "points": len(sub),
                "point_density_per_k": len(sub) / (hi - lo),
                "experimental_points": int((sub["evidence"] == "experimental").sum()),
                "theoretical_points": int((sub["evidence"] == "theoretical").sum()),
                "unique_materials": sub[["material", "family"]]
                .drop_duplicates()
                .shape[0],
                "unique_papers": sub["paper_id"].dropna().nunique(),
            }
        )

    tc_band_summary = pd.DataFrame(band_rows)
    tc_band_summary.to_csv(OUT_DIR / "tc_band_summary.csv", index=False)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(tc_band_summary["band"], tc_band_summary["points"], color="#5B7DBB")
    ax.set_ylabel("Timeline points")
    ax.set_xlabel("Tc band (K)")
    ax.set_title("SCLib timeline point density by Tc band, 1996-2025")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_tc_band_counts.png", dpi=200)
    plt.close(fig)

    density_30_50 = band_count(main_df, 30, 50) / 20
    density_50_80 = band_count(main_df, 50, 80) / 30
    density_80_100 = band_count(main_df, 80, 100) / 20
    gap_ratio = density_50_80 / np.mean([density_30_50, density_80_100])

    mat_density_30_50 = (
        main_df[main_df["tc_kelvin"].between(30, 50, inclusive="left")][
            ["material", "family"]
        ]
        .drop_duplicates()
        .shape[0]
        / 20
    )
    mat_density_50_80 = (
        main_df[main_df["tc_kelvin"].between(50, 80, inclusive="left")][
            ["material", "family"]
        ]
        .drop_duplicates()
        .shape[0]
        / 30
    )
    mat_density_80_100 = (
        main_df[main_df["tc_kelvin"].between(80, 100, inclusive="left")][
            ["material", "family"]
        ]
        .drop_duplicates()
        .shape[0]
        / 20
    )
    material_gap_ratio = mat_density_50_80 / np.mean(
        [mat_density_30_50, mat_density_80_100]
    )
    pd.DataFrame(
        [
            {"metric": "record_gap_ratio", "value": gap_ratio},
            {"metric": "material_gap_ratio", "value": material_gap_ratio},
        ]
    ).to_csv(OUT_DIR / "gap_metrics.csv", index=False)

    regime_bins = [0, 10, 30, 50, 80, 100, 150, 251]
    regime_labels = ["0-10", "10-30", "30-50", "50-80", "80-100", "100-150", "150-251"]
    main_df["tc_regime"] = pd.cut(
        main_df["tc_kelvin"], regime_bins, right=False, labels=regime_labels
    )
    family_regime = (
        main_df.dropna(subset=["tc_regime"])
        .groupby(["tc_regime", "family"], observed=True)
        .size()
        .reset_index(name="points")
    )
    family_regime.to_csv(OUT_DIR / "family_tc_regime_counts.csv", index=False)

    pivot = family_regime.pivot(
        index="tc_regime", columns="family", values="points"
    ).fillna(0)
    top_cols = pivot.sum().sort_values(ascending=False).head(10).index
    ax = pivot[top_cols].plot(kind="bar", stacked=True, figsize=(11, 5), colormap="tab20")
    ax.set_ylabel("Timeline points")
    ax.set_xlabel("Tc regime (K)")
    ax.set_title("Family composition by Tc regime")
    ax.figure.tight_layout()
    ax.figure.savefig(OUT_DIR / "fig_family_tc_regime_counts.png", dpi=200)
    plt.close(ax.figure)

    burst_source = df[df["year"].between(1993, 2025)].copy()
    family_year = (
        burst_source.groupby(["family", "year"])
        .agg(
            points=("tc_kelvin", "size"),
            unique_materials=("material", "nunique"),
            unique_papers=("paper_id", "nunique"),
            experimental_points=("evidence", lambda s: int((s == "experimental").sum())),
            theoretical_points=("evidence", lambda s: int((s == "theoretical").sum())),
            max_tc_k=("tc_kelvin", "max"),
        )
        .reset_index()
        .sort_values(["family", "year"])
    )

    burst_rows = []
    for family, group in family_year.groupby("family"):
        lookup = dict(zip(group["year"], group["points"]))
        for _, row in group.iterrows():
            prev3 = np.mean([lookup.get(row["year"] - i, 0) for i in (1, 2, 3)])
            burst_score = (row["points"] + 1) / (prev3 + 1)
            out = row.to_dict()
            out["prev3_avg_points"] = prev3
            out["burst_score"] = burst_score
            out["burst_candidate"] = bool(
                row["points"] >= 20
                and row["unique_materials"] >= 3
                and burst_score >= 3
            )
            burst_rows.append(out)
    family_year_bursts = pd.DataFrame(burst_rows)
    family_year_bursts = family_year_bursts[
        family_year_bursts["year"].between(1996, 2025)
    ].copy()
    family_year_bursts.to_csv(OUT_DIR / "family_year_bursts.csv", index=False)

    evidence_summary = (
        main_df.groupby("evidence_regime")
        .agg(
            points=("tc_kelvin", "size"),
            unique_materials=("material", "nunique"),
            unique_papers=("paper_id", "nunique"),
            max_tc_k=("tc_kelvin", "max"),
        )
        .reset_index()
        .sort_values("points", ascending=False)
    )
    evidence_summary.to_csv(OUT_DIR / "evidence_regime_summary.csv", index=False)

    yearly_envelope = (
        main_df.groupby(["year", "evidence_regime"])
        .agg(max_tc_k=("tc_kelvin", "max"))
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(11, 5))
    for regime, group in yearly_envelope.groupby("evidence_regime"):
        ax.plot(group["year"], group["max_tc_k"], marker="o", linewidth=1.5, label=regime)
    ax.set_ylabel("Yearly maximum Tc (K)")
    ax.set_xlabel("Year")
    ax.set_title("Theory/experiment Tc envelope by pressure regime")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_evidence_regime_tc_envelope.png", dpi=200)
    plt.close(fig)

    iron_2008 = main_df[(main_df["family"] == "iron_based") & (main_df["year"] == 2008)].copy()
    iron_2008["arxiv_month"] = iron_2008["paper_id"].str.extract(r"arxiv:(\d{4})\.")[0]
    iron_2008["calendar_month"] = (
        "20" + iron_2008["arxiv_month"].str[:2] + "-" + iron_2008["arxiv_month"].str[2:]
    )
    iron_monthly = (
        iron_2008.groupby("calendar_month")
        .agg(
            points=("tc_kelvin", "size"),
            unique_materials=("material", "nunique"),
            unique_papers=("paper_id", "nunique"),
            max_tc_k=("tc_kelvin", "max"),
        )
        .reset_index()
    )
    iron_monthly.to_csv(OUT_DIR / "iron_based_2008_monthly.csv", index=False)

    run_summary = {
        "snapshot_id": metadata["snapshot_id"],
        "frozen_at": metadata["frozen_at"],
        "timeline_points_complete_years": int(len(main_df)),
        "materials_default_rows": int(len(materials)),
        "output_dir": str(OUT_DIR),
    }
    with open(OUT_DIR / "run_summary.json", "w") as f:
        json.dump(run_summary, f, indent=2)
    print(json.dumps(run_summary, indent=2))


if __name__ == "__main__":
    main()
