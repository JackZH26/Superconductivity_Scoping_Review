from __future__ import annotations

from pathlib import Path
import json
import re

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_ID = "2026.05.13"
SNAPSHOT_DIR = PROJECT_ROOT / f"data_freeze/snapshots/{SNAPSHOT_ID}"
OUT_DIR = PROJECT_ROOT / f"validation/samples/{SNAPSHOT_ID}"
RANDOM_SEED = 20260513


UNUSUAL_FORMULA_RE = re.compile(
    r"(?:interface|graphene|diamond|organic|doped|system|compound|material|"
    r"superconductor|[a-z]{10,}|/|\\\\|\\$|_|\\{)",
    re.IGNORECASE,
)


def sample(frame: pd.DataFrame, n: int, seed_offset: int = 0) -> pd.DataFrame:
    if len(frame) <= n:
        return frame.copy()
    return frame.sample(n=n, random_state=RANDOM_SEED + seed_offset)


def ambient_from_pressure(value) -> str:
    if pd.isna(value):
        return "unknown"
    try:
        p = float(value)
    except (TypeError, ValueError):
        return "unknown"
    if abs(p) < 1e-9:
        return "true"
    if p > 1:
        return "false"
    return "unknown"


def add_stratum(pool: dict[int, set[str]], rows: pd.DataFrame, stratum: str) -> None:
    for idx in rows["source_row_index"].tolist():
        pool.setdefault(int(idx), set()).add(stratum)


def validation_rows(selected: pd.DataFrame, metadata: dict) -> pd.DataFrame:
    out_rows = []
    selected = selected.sort_values(["primary_stratum", "year", "paper_id", "material"])
    for n, (_, row) in enumerate(selected.iterrows(), start=1):
        out_rows.append(
            {
                "validation_id": f"VAL-{n:06d}",
                "reviewer": "",
                "review_date": "",
                "snapshot_version": metadata.get("stats", {}).get("dataset_version")
                or metadata.get("snapshot_id", SNAPSHOT_ID),
                "sample_strata": row["sample_strata"],
                "primary_stratum": row["primary_stratum"],
                "source_row_index": int(row["source_row_index"]),
                "paper_id": row.get("paper_id", ""),
                "paper_title": "",
                "paper_year": int(row["year"]),
                "material_id": "",
                "formula_extracted": row["material"],
                "formula_corrected": "",
                "formula_valid": "",
                "family_extracted": row.get("family", "Other"),
                "family_corrected": "",
                "family_valid": "",
                "tc_extracted_k": row["tc_kelvin"],
                "tc_corrected_k": "",
                "tc_valid": "",
                "tc_type_extracted": "",
                "tc_type_corrected": "",
                "pressure_extracted_gpa": ""
                if pd.isna(row.get("pressure_gpa"))
                else row.get("pressure_gpa"),
                "pressure_corrected_gpa": "",
                "pressure_valid": "",
                "pressure_role_extracted": "unknown"
                if pd.isna(row.get("pressure_gpa"))
                else ("none" if abs(float(row.get("pressure_gpa"))) < 1e-9 else "measurement"),
                "pressure_role_corrected": "",
                "pressure_role_valid": "",
                "ambient_extracted": ambient_from_pressure(row.get("pressure_gpa")),
                "ambient_corrected": "",
                "ambient_valid": "",
                "evidence_type_extracted": "unknown",
                "evidence_type_corrected": "",
                "evidence_type_valid": "",
                "is_theoretical_extracted": str(bool(row["is_theoretical"])).lower(),
                "is_theoretical_corrected": "",
                "is_theoretical_valid": "",
                "measurement_extracted": "",
                "measurement_corrected": "",
                "needs_review_extracted": "",
                "should_exclude_from_main": "",
                "exclusion_reason": "",
                "source_quote_or_location": "",
                "notes": "",
            }
        )
    return pd.DataFrame(out_rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    metadata = json.loads((SNAPSHOT_DIR / "metadata.json").read_text())
    df = pd.read_csv(SNAPSHOT_DIR / "timeline_points.csv")
    df["family"] = df["family"].fillna("Other").replace("", "Other")
    df["source_row_index"] = np.arange(len(df))

    complete = df[df["year"].between(1996, 2025)].copy()

    strata_frames: list[tuple[str, pd.DataFrame]] = [
        ("random_timeline", sample(complete, 300, 1)),
        (
            "tc_50_80_gap",
            sample(complete[(complete["tc_kelvin"] >= 50) & (complete["tc_kelvin"] < 80)], 150, 2),
        ),
        (
            "tc_80_100_plateau",
            sample(complete[(complete["tc_kelvin"] >= 80) & (complete["tc_kelvin"] < 100)], 150, 3),
        ),
        (
            "tc_ge_150_experimental_all",
            complete[(complete["tc_kelvin"] >= 150) & (~complete["is_theoretical"])],
        ),
        (
            "tc_ge_150_theoretical",
            sample(complete[(complete["tc_kelvin"] >= 150) & (complete["is_theoretical"])], 100, 4),
        ),
        (
            "iron_based_2008",
            sample(complete[(complete["family"] == "iron_based") & (complete["year"] == 2008)], 100, 5),
        ),
        ("hydride", sample(complete[complete["family"] == "hydride"], 100, 6)),
        ("nickelate", sample(complete[complete["family"] == "nickelate"], 100, 7)),
        ("kagome", sample(complete[complete["family"] == "kagome"], 50, 8)),
        (
            "missing_family_or_unusual_formula",
            sample(
                complete[
                    (complete["family"] == "Other")
                    | complete["material"].astype(str).str.contains(UNUSUAL_FORMULA_RE, na=False)
                ],
                100,
                9,
            ),
        ),
    ]

    row_strata: dict[int, set[str]] = {}
    primary: dict[int, str] = {}
    stratum_summary = []
    for name, frame in strata_frames:
        frame = frame.drop_duplicates("source_row_index")
        add_stratum(row_strata, frame, name)
        for idx in frame["source_row_index"].tolist():
            primary.setdefault(int(idx), name)
        stratum_summary.append({"stratum": name, "requested_or_all": len(frame), "unique_rows": len(frame)})

    selected_indices = sorted(row_strata)
    selected = df[df["source_row_index"].isin(selected_indices)].copy()
    selected["sample_strata"] = selected["source_row_index"].map(
        lambda i: ";".join(sorted(row_strata[int(i)]))
    )
    selected["primary_stratum"] = selected["source_row_index"].map(lambda i: primary[int(i)])

    validation = validation_rows(selected, metadata)
    validation.to_csv(OUT_DIR / "validation_sample.csv", index=False)

    summary = pd.DataFrame(stratum_summary)
    summary["deduplicated_total_sample"] = len(validation)
    summary.to_csv(OUT_DIR / "validation_sample_summary.csv", index=False)

    with open(OUT_DIR / "README.md", "w") as f:
        f.write(
            f"""# Validation Sample {SNAPSHOT_ID}

Generated from `{SNAPSHOT_DIR}` with random seed `{RANDOM_SEED}`.

Rows in `validation_sample.csv`: {len(validation)}

The sample is intentionally stratified and overlapping. If a timeline record
belongs to multiple strata, `sample_strata` lists all matching strata while
`primary_stratum` records the first stratum that selected it.

Fields that are unavailable from the public timeline API, such as paper title,
material id, Tc type, measurement type, and primary/cited evidence, are left
blank or `unknown` for manual validation.
"""
        )

    print(f"Wrote {len(validation)} validation rows to {OUT_DIR}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
