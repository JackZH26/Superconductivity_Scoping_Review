from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE = PROJECT_ROOT / "validation/samples/2026.05.13/validation_sample.csv"
REVIEWER = "Codex preliminary"
REVIEW_DATE = "2026-05-13"
DEFAULT_NOTE = (
    "Preliminary validation from SCLib paper endpoint and arXiv abstract; "
    "final human full-text check still required."
)
PRESSURE_ROLE_COLUMNS = [
    "pressure_role_extracted",
    "pressure_role_corrected",
    "pressure_role_valid",
]


# Only rows in the high-risk Tc >= 150 K experimental stratum.
# The correction choices are intentionally conservative:
# - records that are secondary analyses/citations are excluded from main analysis;
# - missing pressure is marked invalid even when the source states high pressure;
# - formula strings with phase prefixes are corrected.
UPDATES = {
    "VAL-001000": {
        "paper_title": "Conventional superconductivity at 190 K at high pressures",
        "formula_valid": "true",
        "family_valid": "true",
        "tc_valid": "true",
        "pressure_corrected_gpa": 200,
        "pressure_valid": "false",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "primary",
        "evidence_type_valid": "true",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "resistivity",
        "measurement_corrected": "resistivity",
        "should_exclude_from_main": "false",
        "source_quote_or_location": "SCLib paper endpoint abstract/material record; exact pressure needs full-text figure check.",
    },
    "VAL-001001": {
        "paper_title": "Conventional superconductivity at 190 K at high pressures",
        "formula_valid": "true",
        "family_valid": "true",
        "tc_valid": "true",
        "pressure_valid": "true",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "primary",
        "evidence_type_valid": "true",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "resistivity",
        "measurement_corrected": "resistivity",
        "should_exclude_from_main": "false",
        "source_quote_or_location": "SCLib material record reports H2S Tc 150 K at 200 GPa.",
    },
    "VAL-001002": {
        "paper_title": "Conventional superconductivity at 203 K at high pressures",
        "formula_valid": "true",
        "family_valid": "true",
        "tc_valid": "true",
        "pressure_corrected_gpa": 155,
        "pressure_valid": "false",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "primary",
        "evidence_type_valid": "true",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "resistivity",
        "measurement_corrected": "resistivity/susceptibility",
        "should_exclude_from_main": "false",
        "source_quote_or_location": "SCLib/arXiv abstract confirms 203 K high-pressure sulfur hydride; extracted 90 GPa likely lower-bound pressure.",
    },
    "VAL-001003": {
        "paper_title": "Direct Meissner Effect Observation of Superconductivity in Compressed H2S",
        "formula_valid": "true",
        "family_valid": "true",
        "tc_valid": "true",
        "pressure_valid": "true",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "primary",
        "evidence_type_valid": "true",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "susceptibility",
        "measurement_corrected": "Meissner/susceptibility",
        "should_exclude_from_main": "false",
        "source_quote_or_location": "Title and SCLib material record support primary magnetic evidence for compressed sulfur hydride.",
    },
    "VAL-001004": {
        "paper_title": "Spectroscopy of H3S: evidence of a new energy scale for superconductivity",
        "formula_valid": "true",
        "family_valid": "true",
        "tc_valid": "true",
        "pressure_valid": "true",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "primary",
        "evidence_type_valid": "true",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "resistivity",
        "measurement_corrected": "spectroscopy/resistivity context",
        "should_exclude_from_main": "false",
        "source_quote_or_location": "SCLib record reports primary H3S Tc 200 K at 150 GPa; abstract describes experimental spectroscopy.",
    },
    "VAL-001005": {
        "paper_title": "Superconductivity at 250 K in lanthanum hydride under high pressures",
        "formula_valid": "true",
        "family_valid": "true",
        "tc_valid": "true",
        "pressure_valid": "true",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "primary",
        "evidence_type_valid": "true",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "resistivity",
        "measurement_corrected": "resistivity",
        "should_exclude_from_main": "false",
        "source_quote_or_location": "Title and SCLib material record support LaH10 Tc 250 K at 170 GPa.",
    },
    "VAL-001006": {
        "paper_title": "Superconductivity at 161 K in Thorium Hydride ThH10: Synthesis and Properties",
        "formula_valid": "true",
        "family_valid": "true",
        "tc_corrected_k": 161,
        "tc_valid": "true",
        "pressure_valid": "true",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "primary",
        "evidence_type_valid": "true",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "resistivity",
        "measurement_corrected": "resistivity",
        "should_exclude_from_main": "false",
        "source_quote_or_location": "Abstract reports ThH10 Tc 159-161 K at 170-175 GPa.",
    },
    "VAL-001007": {
        "paper_title": "Superconductivity of Pure H3S Synthesis from Elemental Sulfur and Hydrogen",
        "formula_valid": "true",
        "family_valid": "true",
        "tc_valid": "true",
        "pressure_valid": "true",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "primary",
        "evidence_type_valid": "true",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "resistivity",
        "measurement_corrected": "resistivity",
        "should_exclude_from_main": "false",
        "source_quote_or_location": "SCLib material record reports H3S onset Tc 200 K at 146 GPa.",
    },
    "VAL-001008": {
        "paper_title": "Superconductivity of Pure H3S Synthesis from Elemental Sulfur and Hydrogen",
        "formula_valid": "true",
        "family_valid": "true",
        "tc_valid": "true",
        "pressure_valid": "true",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "primary",
        "evidence_type_valid": "true",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "resistivity",
        "measurement_corrected": "resistivity",
        "should_exclude_from_main": "false",
        "source_quote_or_location": "SCLib material record reports H3S offset Tc 186 K at 146 GPa.",
    },
    "VAL-001009": {
        "paper_title": "Superconductivity up to 243 K in yttrium hydrides under high pressure",
        "formula_valid": "true",
        "family_valid": "true",
        "tc_valid": "true",
        "pressure_valid": "true",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "primary",
        "evidence_type_valid": "true",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "resistivity",
        "measurement_corrected": "resistivity",
        "should_exclude_from_main": "false",
        "source_quote_or_location": "SCLib record reports YH6 Tc 227 K at 237 GPa.",
    },
    "VAL-001010": {
        "paper_title": "Superconductivity up to 243 K in yttrium hydrides under high pressure",
        "formula_valid": "true",
        "family_valid": "true",
        "tc_valid": "true",
        "pressure_valid": "true",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "primary",
        "evidence_type_valid": "true",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "resistivity",
        "measurement_corrected": "resistivity",
        "should_exclude_from_main": "false",
        "source_quote_or_location": "Title and SCLib record support YH9 Tc 243 K at 201 GPa.",
    },
    "VAL-001011": {
        "paper_title": "The electron-phonon coupling constant, the Fermi temperature and unconventional superconductivity in the carbonaceous sulfur hydride 190 K superconductor",
        "formula_valid": "true",
        "family_corrected": "hydride",
        "family_valid": "false",
        "tc_valid": "true",
        "pressure_valid": "true",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "unknown",
        "evidence_type_corrected": "cited/secondary analysis",
        "evidence_type_valid": "false",
        "is_theoretical_corrected": "true",
        "is_theoretical_valid": "false",
        "measurement_corrected": "analysis of reported magnetoresistance",
        "should_exclude_from_main": "true",
        "exclusion_reason": "cited_only",
        "source_quote_or_location": "arXiv abstract says the paper analyzes data reported by Snider et al.; not primary synthesis/measurement.",
    },
    "VAL-001012": {
        "paper_title": "Superconductivity above 200 K Observed in Superhydrides of Calcium",
        "formula_valid": "true",
        "family_valid": "true",
        "tc_valid": "true",
        "pressure_valid": "true",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "primary",
        "evidence_type_valid": "true",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "resistivity",
        "measurement_corrected": "resistivity",
        "should_exclude_from_main": "false",
        "source_quote_or_location": "Abstract reports experimental calcium superhydride superconductivity above 210 K at 160-190 GPa.",
    },
    "VAL-001013": {
        "paper_title": "Efficient route to achieve superconductivity improvement via substitutional La-Ce alloy superhydride at high pressure",
        "formula_valid": "true",
        "family_valid": "true",
        "tc_valid": "true",
        "pressure_valid": "false",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "primary",
        "evidence_type_valid": "true",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "resistivity",
        "measurement_corrected": "resistivity",
        "should_exclude_from_main": "false",
        "source_quote_or_location": "Title/abstract support high-pressure La-Ce hydride; extracted pressure is missing and needs full-text figure check.",
    },
    "VAL-001014": {
        "paper_title": "Synthesis of Superconducting Phase of La0.5Ce0.5H10 at High Pressures",
        "formula_corrected": "La0.5Ce0.5H10",
        "formula_valid": "false",
        "family_valid": "true",
        "tc_valid": "true",
        "pressure_valid": "true",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "primary",
        "evidence_type_valid": "true",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "resistivity",
        "measurement_corrected": "resistivity",
        "should_exclude_from_main": "false",
        "source_quote_or_location": "arXiv title and SCLib record support Tc 175 K at 155 GPa; formula includes phase prefix.",
    },
    "VAL-001015": {
        "paper_title": "Observation of the Josephson effect in superhydrides: DC SQUID based on (La,Ce)H10+x with operating temperature of 179 K",
        "formula_valid": "true",
        "family_valid": "true",
        "tc_valid": "true",
        "pressure_valid": "true",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "primary",
        "evidence_type_valid": "true",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "resistivity",
        "measurement_corrected": "Josephson/SQUID operation",
        "should_exclude_from_main": "false",
        "source_quote_or_location": "Abstract reports DC SQUID using (La,Ce)H10+x at 148 GPa and 179 K.",
    },
    "VAL-001016": {
        "paper_title": "Diffusion Driven Transient Hydrogenation in Metal Superhydrides at Extreme Conditions",
        "formula_valid": "true",
        "family_valid": "true",
        "tc_valid": "false",
        "pressure_valid": "true",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "cited/contextual",
        "evidence_type_valid": "false",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "resistivity",
        "measurement_corrected": "NMR / hydrogen diffusion",
        "should_exclude_from_main": "true",
        "exclusion_reason": "not_superconductivity",
        "source_quote_or_location": "arXiv abstract describes NMR on LaHx diffusion, not a primary superconducting Tc measurement.",
    },
    "VAL-001017": {
        "paper_title": "X-ray Diffraction and Electrical Transport Imaging of Superconducting Superhydride (La,Y)H10",
        "formula_valid": "true",
        "family_valid": "true",
        "tc_valid": "true",
        "pressure_valid": "false",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "primary",
        "evidence_type_valid": "true",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "resistivity",
        "measurement_corrected": "four-probe DC resistance",
        "should_exclude_from_main": "false",
        "source_quote_or_location": "arXiv abstract reports onset 244 K; pressure range 168 to 136 GPa, but record pressure missing.",
    },
    "VAL-001018": {
        "paper_title": "X-ray Diffraction and Electrical Transport Imaging of Superconducting Superhydride (La,Y)H10",
        "formula_valid": "true",
        "family_valid": "true",
        "tc_valid": "true",
        "pressure_valid": "false",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "primary",
        "evidence_type_valid": "true",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "resistivity",
        "measurement_corrected": "four-probe DC resistance",
        "should_exclude_from_main": "false",
        "source_quote_or_location": "arXiv abstract reports second transition near 220 K; pressure range present but record pressure missing.",
    },
    "VAL-001019": {
        "paper_title": "Imaging magnetic flux trapping in lanthanum hydride using diamond quantum sensors",
        "formula_valid": "true",
        "family_valid": "true",
        "tc_valid": "true",
        "pressure_valid": "true",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "primary",
        "evidence_type_valid": "true",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "susceptibility",
        "measurement_corrected": "magnetic flux trapping / susceptibility",
        "should_exclude_from_main": "false",
        "source_quote_or_location": "SCLib record reports LaH9.6 Tc 220 K at 150 GPa; abstract describes magnetic flux trapping.",
    },
    "VAL-001020": {
        "paper_title": "Imaging magnetic flux trapping in lanthanum hydride using diamond quantum sensors",
        "formula_valid": "true",
        "family_valid": "true",
        "tc_valid": "true",
        "pressure_valid": "true",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "primary",
        "evidence_type_valid": "true",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "resistivity",
        "measurement_corrected": "resistivity",
        "should_exclude_from_main": "false",
        "source_quote_or_location": "SCLib record reports LaH9.6 zero-resistance Tc 216 K at 153 GPa.",
    },
    "VAL-001021": {
        "paper_title": "Raman fingerprint of high-temperature superconductivity in compressed hydrides",
        "formula_valid": "true",
        "family_valid": "true",
        "tc_valid": "true",
        "pressure_valid": "true",
        "ambient_corrected": "false",
        "ambient_valid": "true",
        "evidence_type_extracted": "primary",
        "evidence_type_corrected": "primary",
        "evidence_type_valid": "true",
        "is_theoretical_corrected": "false",
        "is_theoretical_valid": "true",
        "measurement_extracted": "Raman",
        "measurement_corrected": "Raman/resistivity context",
        "should_exclude_from_main": "false",
        "source_quote_or_location": "SCLib record reports LaH10 Tc 165 K at 145 GPa; arXiv abstract describes Raman study.",
    },
}


def parse_float(value):
    try:
        s = str(value).strip()
        return float(s) if s else None
    except (TypeError, ValueError):
        return None


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def pressure_role_from_value(value) -> str:
    pressure = parse_float(value)
    if pressure is None:
        return "unknown"
    if abs(pressure) < 1e-9:
        return "none"
    return "measurement"


def main() -> None:
    df = pd.read_csv(SAMPLE, dtype=str, keep_default_na=False)
    for column in PRESSURE_ROLE_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    for validation_id, updates in UPDATES.items():
        mask = df["validation_id"] == validation_id
        if mask.sum() != 1:
            raise RuntimeError(f"Expected one row for {validation_id}, found {mask.sum()}")
        updates = dict(updates)
        updates["reviewer"] = REVIEWER
        updates["review_date"] = REVIEW_DATE
        updates.setdefault("notes", DEFAULT_NOTE)

        extracted_role = pressure_role_from_value(df.loc[mask, "pressure_extracted_gpa"].iloc[0])
        corrected_role = (
            "cited/contextual"
            if updates.get("should_exclude_from_main") == "true"
            else "measurement"
        )
        updates.setdefault("pressure_role_extracted", extracted_role)
        updates.setdefault("pressure_role_corrected", corrected_role)
        updates.setdefault(
            "pressure_role_valid",
            bool_text(extracted_role == corrected_role),
        )

        for key, value in updates.items():
            df.loc[mask, key] = value

    df.to_csv(SAMPLE, index=False)
    print(f"Applied {len(UPDATES)} high-Tc experimental precheck updates to {SAMPLE}")


if __name__ == "__main__":
    main()
