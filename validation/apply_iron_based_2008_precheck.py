from __future__ import annotations

import csv
import json
import math
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE = PROJECT_ROOT / "validation/samples/2026.05.13/validation_sample.csv"
OUT_DIR = SAMPLE.parent
CACHE = PROJECT_ROOT / "validation/cache/sclib_papers_iron_based_2008.json"
SUMMARY = OUT_DIR / "iron_based_2008_precheck_summary.md"
REVIEW_QUEUE = OUT_DIR / "iron_based_2008_review_queue.csv"

API_BASE = "https://api.jzis.org/sclib/v1"
REVIEWER = "Codex preliminary"
REVIEW_DATE = "2026-05-13"
TARGET_STRATUM = "iron_based_2008"
DEFAULT_NOTE = (
    "Preliminary iron-based-2008 validation from SCLib paper endpoint "
    "and arXiv abstract metadata; final human full-text check still required."
)

# The 2008 iron-based sample is overwhelmingly experimental. This set is
# restricted to records whose source abstract clearly describes computation.
COMPUTATIONAL_PAPERS = {
    "arxiv:0803.2703",
}

# These papers report high-pressure synthesis, not Tc measured under pressure.
# The current validation schema has no pressure-role field, so these are
# marked invalid for pressure-as-Tc-condition and discussed in the notes.
SYNTHESIS_PRESSURE_ROWS = {
    "VAL-000095",
    "VAL-000096",
}

MANUAL_OVERRIDES = {
    "VAL-000074": {
        "formula_valid": "false",
        "tc_valid": "false",
        "evidence_type_corrected": "cited/contextual",
        "evidence_type_valid": "false",
        "should_exclude_from_main": "true",
        "exclusion_reason": "contextual_or_cited_material",
        "source_quote_or_location": (
            "Paper title/abstract are for LaO0.9F0.1-deltaFeAs point-contact "
            "spectroscopy; the Pr[O1-xFx]FeAs 42 K row is not supported as a "
            "primary material record by the abstract-level evidence."
        ),
    },
    "VAL-000107": {
        "formula_corrected": "Ba0.5K0.5Fe2As2",
        "formula_valid": "false",
        "source_quote_or_location": (
            "Paper title/abstract use Ba_{1-x}M_xFe2As2; extracted "
            "Ba0.5K0.5OFe2As2 carries an extra O."
        ),
    },
    "VAL-000122": {
        "tc_corrected_k": "27.0",
        "tc_valid": "false",
        "should_exclude_from_main": "true",
        "exclusion_reason": "tc_extraction_error",
        "source_quote_or_location": (
            "SCLib paper endpoint contains 27 K and 23 K superconducting "
            "LaFeAsO0.89F0.11 records; the sampled 0.5 K value is a low "
            "measurement temperature, not Tc."
        ),
    },
}


def fetch_json(pathname: str) -> dict:
    url = f"{API_BASE}{pathname}"
    for attempt in range(6):
        request = urllib.request.Request(
            url, headers={"User-Agent": "SCLib-scope-review-validation/0.1"}
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except Exception:
            if attempt == 5:
                raise
            time.sleep(min(20, 1.5 * 2**attempt))
    raise RuntimeError(f"unreachable fetch retry loop for {url}")


def load_paper_cache(paper_ids: list[str]) -> dict[str, dict]:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    if CACHE.exists():
        cache = json.loads(CACHE.read_text())
    else:
        cache = {}

    missing = [paper_id for paper_id in paper_ids if paper_id not in cache]
    for i, paper_id in enumerate(missing, start=1):
        encoded = urllib.parse.quote(paper_id, safe="")
        cache[paper_id] = fetch_json(f"/paper/{encoded}")
        if i % 10 == 0 or i == len(missing):
            print(f"cached paper metadata {i}/{len(missing)}")

    CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False))
    return cache


def normalized_formula(value: object, drop_variables: bool = False) -> str:
    s = str(value or "").lower()
    s = (
        s.replace("δ", "delta")
        .replace("Δ", "delta")
        .replace("−", "-")
        .replace("–", "-")
    )
    if drop_variables:
        s = re.sub(r"(delta|epsilon|[xyz])", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def elements(value: object) -> set[str]:
    return set(re.findall(r"[A-Z][a-z]?", str(value or "")))


def parse_float(value: object) -> float | None:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        out = float(s)
    except ValueError:
        return None
    if math.isnan(out):
        return None
    return out


def parse_bool(value: object) -> bool | None:
    s = str(value or "").strip().lower()
    if s in {"true", "t", "yes", "y", "1"}:
        return True
    if s in {"false", "f", "no", "n", "0"}:
        return False
    return None


def bool_text(value: bool | None) -> str:
    if value is None:
        return ""
    return "true" if value else "false"


def match_material(row: pd.Series, paper: dict) -> dict | None:
    target_formula = row["formula_extracted"]
    target_tc = parse_float(row["tc_extracted_k"])
    target_norm = normalized_formula(target_formula)
    target_loose = normalized_formula(target_formula, drop_variables=True)
    target_elements = elements(target_formula)

    best_score = -10_000.0
    best_material = None
    for material in paper.get("materials_extracted", []) or []:
        material_tc = parse_float(material.get("tc_kelvin"))
        if target_tc is None or material_tc is None:
            continue

        material_formula = material.get("formula", "")
        material_norm = normalized_formula(material_formula)
        material_loose = normalized_formula(material_formula, drop_variables=True)
        material_elements = elements(material_formula)
        tc_diff = abs(material_tc - target_tc)

        score = -8.0 * tc_diff
        if material_norm == target_norm:
            score += 110
        elif material_loose == target_loose:
            score += 90
        elif target_norm and (
            target_norm in material_norm or material_norm in target_norm
        ):
            score += 60
        elif target_elements and material_elements and target_elements == material_elements:
            score += 35
        elif target_elements and material_elements:
            score += 10 * len(target_elements & material_elements) / len(target_elements)

        if material.get("evidence_type") == "primary":
            score += 12
        if material.get("measurement") not in {None, "", "unknown"}:
            score += 3
        if tc_diff <= 0.2:
            score += 10

        if score > best_score:
            best_score = score
            best_material = material

    if best_material is None:
        return None
    best_material = dict(best_material)
    best_material["_match_score"] = best_score
    return best_material


def corrected_theory_flag(paper_id: str) -> bool:
    return paper_id in COMPUTATIONAL_PAPERS


def is_iron_based_formula(formula: str, paper_title: str) -> bool:
    els = elements(formula)
    if "Fe" in els and els & {"As", "P", "Se", "Te"}:
        return True
    return "iron" in paper_title.lower() or "feas" in formula.lower()


def validate_row(row: pd.Series, paper: dict) -> dict[str, object]:
    material = match_material(row, paper)
    paper_id = row["paper_id"]
    extracted_theory = parse_bool(row["is_theoretical_extracted"])
    corrected_theory = corrected_theory_flag(paper_id)
    extracted_pressure = parse_float(row["pressure_extracted_gpa"])
    material_pressure = parse_float((material or {}).get("pressure_gpa"))
    extracted_ambient = parse_bool(row["ambient_extracted"])

    formula = row["formula_extracted"]
    title = paper.get("title", "")
    family_valid = row["family_extracted"] == "iron_based" and is_iron_based_formula(
        formula, title
    )

    if material is None:
        formula_valid = False
        tc_valid = False
        evidence = "unknown"
        measurement = ""
        tc_type = ""
    else:
        formula_valid = material["_match_score"] >= 30
        tc_valid = (
            parse_float(material.get("tc_kelvin")) is not None
            and parse_float(row["tc_extracted_k"]) is not None
            and abs(parse_float(material.get("tc_kelvin")) - parse_float(row["tc_extracted_k"]))
            <= 0.6
        )
        evidence = material.get("evidence_type") or "unknown"
        measurement = material.get("measurement") or ""
        tc_type = material.get("tc_type") or ""

    if material_pressure is not None:
        pressure_valid = (
            extracted_pressure is not None and abs(extracted_pressure - material_pressure) <= 0.05
        )
        pressure_corrected = material_pressure
    else:
        pressure_valid = extracted_pressure in {None, 0.0}
        pressure_corrected = ""

    if extracted_pressure is None:
        pressure_role_extracted = "none"
    elif extracted_pressure <= 1e-9:
        pressure_role_extracted = "none"
    else:
        pressure_role_extracted = "measurement"
    pressure_role_corrected = pressure_role_extracted
    pressure_role_valid: bool | None = True

    applied_pressure = material_pressure if material_pressure is not None else extracted_pressure
    ambient_corrected = not (applied_pressure is not None and applied_pressure > 0)
    ambient_valid = (
        extracted_ambient == ambient_corrected if extracted_ambient is not None else None
    )

    if row["validation_id"] in SYNTHESIS_PRESSURE_ROWS:
        pressure_valid = extracted_pressure is not None
        pressure_corrected = extracted_pressure if extracted_pressure is not None else ""
        pressure_role_extracted = "measurement"
        pressure_role_corrected = "synthesis"
        pressure_role_valid = False
        ambient_corrected = True
        ambient_valid = extracted_ambient is True

    evidence_corrected = evidence
    evidence_valid = evidence == "primary"
    exclude = not (formula_valid and tc_valid and evidence_valid)
    exclusion_reason = ""
    if exclude:
        if evidence != "primary":
            exclusion_reason = "not_primary_evidence"
        elif not tc_valid:
            exclusion_reason = "tc_extraction_error"
        elif not formula_valid:
            exclusion_reason = "formula_extraction_error"

    source = (
        f"SCLib paper endpoint: {title}; matched record "
        f"{(material or {}).get('formula', '')}, Tc={(material or {}).get('tc_kelvin', '')}, "
        f"evidence={evidence}."
    )

    updates: dict[str, object] = {
        "reviewer": REVIEWER,
        "review_date": REVIEW_DATE,
        "paper_title": title,
        "formula_valid": bool_text(formula_valid),
        "family_valid": bool_text(family_valid),
        "tc_valid": bool_text(tc_valid),
        "tc_type_extracted": tc_type,
        "pressure_corrected_gpa": pressure_corrected,
        "pressure_valid": bool_text(pressure_valid),
        "pressure_role_extracted": pressure_role_extracted,
        "pressure_role_corrected": pressure_role_corrected,
        "pressure_role_valid": bool_text(pressure_role_valid),
        "ambient_corrected": bool_text(ambient_corrected),
        "ambient_valid": bool_text(ambient_valid),
        "evidence_type_extracted": evidence,
        "evidence_type_corrected": evidence_corrected,
        "evidence_type_valid": bool_text(evidence_valid),
        "is_theoretical_corrected": bool_text(corrected_theory),
        "is_theoretical_valid": bool_text(extracted_theory == corrected_theory),
        "measurement_extracted": measurement,
        "measurement_corrected": measurement,
        "should_exclude_from_main": bool_text(exclude),
        "exclusion_reason": exclusion_reason,
        "source_quote_or_location": source,
        "notes": DEFAULT_NOTE,
    }

    if material is not None and normalized_formula(material.get("formula")) != normalized_formula(
        formula
    ):
        if normalized_formula(material.get("formula"), drop_variables=True) != normalized_formula(
            formula, drop_variables=True
        ):
            updates["formula_corrected"] = material.get("formula", "")

    if row["validation_id"] in SYNTHESIS_PRESSURE_ROWS:
        updates["notes"] = (
            DEFAULT_NOTE
            + " Pressure value is a high-pressure synthesis condition, not a Tc measurement pressure."
        )
        updates["source_quote_or_location"] = (
            "Abstract reports preparation at 10-12 GPa; superconducting Tc is for "
            "the prepared Tb/Dy FeAs(O,F) materials rather than an in situ pressure-Tc point."
        )
        updates["should_exclude_from_main"] = "false"
        updates["exclusion_reason"] = ""

    for key, value in MANUAL_OVERRIDES.get(row["validation_id"], {}).items():
        updates[key] = value

    # Keep non-excluded rows explicit after field-level manual corrections.
    if row["validation_id"] == "VAL-000107":
        updates["should_exclude_from_main"] = "false"
        updates["exclusion_reason"] = ""
    return updates


def score_field(frame: pd.DataFrame, field: str) -> tuple[int, int, float | None]:
    values = frame[field].map(parse_bool).dropna()
    n = len(values)
    if n == 0:
        return 0, 0, None
    k = int(values.sum())
    return n, k, k / n


def write_review_queue(frame: pd.DataFrame) -> None:
    fields = [
        "formula_valid",
        "family_valid",
        "tc_valid",
        "pressure_valid",
        "pressure_role_valid",
        "ambient_valid",
        "evidence_type_valid",
        "is_theoretical_valid",
    ]
    rows = []
    for _, row in frame.iterrows():
        false_fields = [field for field in fields if parse_bool(row[field]) is False]
        if parse_bool(row["should_exclude_from_main"]) is True or false_fields:
            rows.append(
                {
                    "validation_id": row["validation_id"],
                    "paper_id": row["paper_id"],
                    "paper_title": row["paper_title"],
                    "formula_extracted": row["formula_extracted"],
                    "tc_extracted_k": row["tc_extracted_k"],
                    "false_fields": ";".join(false_fields),
                    "should_exclude_from_main": row["should_exclude_from_main"],
                    "exclusion_reason": row["exclusion_reason"],
                    "notes": row["notes"],
                    "source_quote_or_location": row["source_quote_or_location"],
                }
            )

    with REVIEW_QUEUE.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "validation_id",
                "paper_id",
                "paper_title",
                "formula_extracted",
                "tc_extracted_k",
                "false_fields",
                "should_exclude_from_main",
                "exclusion_reason",
                "notes",
                "source_quote_or_location",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_summary(frame: pd.DataFrame) -> None:
    fields = [
        ("Formula", "formula_valid"),
        ("Family", "family_valid"),
        ("Tc", "tc_valid"),
        ("Pressure", "pressure_valid"),
        ("Pressure role", "pressure_role_valid"),
        ("Ambient flag", "ambient_valid"),
        ("Evidence type", "evidence_type_valid"),
        ("Theory flag", "is_theoretical_valid"),
    ]
    excluded = frame["should_exclude_from_main"].map(parse_bool)
    excluded_n = int(excluded.dropna().sum())
    unique_papers = frame["paper_id"].nunique()
    computational = int((frame["is_theoretical_corrected"].map(parse_bool) == True).sum())
    theory_mismatches = int((frame["is_theoretical_valid"].map(parse_bool) == False).sum())

    lines = [
        "# Iron-Based 2008 Validation Precheck",
        "",
        f"- Review date: {REVIEW_DATE}",
        f"- Rows updated: {len(frame)}",
        f"- Unique papers: {unique_papers}",
        f"- Computational/theoretical source rows after correction: {computational}",
        f"- Theory/experiment flag mismatches: {theory_mismatches}",
        f"- Rows recommended for exclusion from main quantitative analysis: {excluded_n}",
        "",
        "## Field-Level Metrics",
        "",
        "| Field | Reviewed n | Valid n | Accuracy |",
        "|---|---:|---:|---:|",
    ]
    for label, field in fields:
        n, k, acc = score_field(frame, field)
        acc_text = "" if acc is None else f"{acc:.1%}"
        lines.append(f"| {label} | {n} | {k} | {acc_text} |")

    lines.extend(
        [
            "",
            "## Main Findings",
            "",
            "- The 2008 iron-based burst sample is largely valid at the formula, family, Tc, and primary-evidence levels.",
            "- Several rows labelled theoretical are experimental spectroscopy, transport, synthesis, or thermodynamic papers; this is an important caveat for theory/experiment comparisons.",
            "- High-pressure synthesis rows should not be treated as high-pressure Tc measurements; pressure role is now tracked separately from pressure value.",
            "- Two rows are recommended for exclusion from the main quantitative analysis at this stage: one contextual PrFeAsO row from a LaFeAsO spectroscopy paper and one 0.5 K value extracted as Tc.",
            "",
            f"Detailed review queue: `{REVIEW_QUEUE.name}`.",
            "",
        ]
    )
    SUMMARY.write_text("\n".join(lines))


def main() -> None:
    df = pd.read_csv(SAMPLE, dtype=str, keep_default_na=False)
    target_mask = df["sample_strata"].str.contains(TARGET_STRATUM, regex=False)
    target = df.loc[target_mask].copy()
    paper_ids = list(dict.fromkeys(target["paper_id"].tolist()))
    cache = load_paper_cache(paper_ids)

    for idx, row in target.iterrows():
        updates = validate_row(row, cache[row["paper_id"]])
        for key, value in updates.items():
            df.loc[idx, key] = "" if value is None else value

    df.to_csv(SAMPLE, index=False)
    updated = df.loc[target_mask].copy()
    write_review_queue(updated)
    write_summary(updated)
    print(f"Applied iron-based 2008 precheck updates to {len(updated)} rows")
    print(f"Wrote {SUMMARY}")
    print(f"Wrote {REVIEW_QUEUE}")


if __name__ == "__main__":
    main()
