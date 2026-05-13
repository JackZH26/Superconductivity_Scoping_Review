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
CACHE = PROJECT_ROOT / "validation/cache/sclib_papers_tc_bands.json"
SUMMARY = OUT_DIR / "tc_band_precheck_summary.md"
REVIEW_QUEUE = OUT_DIR / "tc_band_review_queue.csv"

API_BASE = "https://api.jzis.org/sclib/v1"
REVIEWER = "Codex preliminary"
REVIEW_DATE = "2026-05-13"
TARGET_STRATA = ["tc_50_80_gap", "tc_80_100_plateau"]
DEFAULT_NOTE = (
    "Preliminary Tc-band validation from SCLib paper endpoint and arXiv "
    "abstract metadata; final human full-text check still required."
)

VALIDATION_FIELDS = [
    "formula_valid",
    "family_valid",
    "tc_valid",
    "pressure_valid",
    "pressure_role_valid",
    "ambient_valid",
    "evidence_type_valid",
    "is_theoretical_valid",
]

CANONICAL_COLUMNS = [
    "validation_id",
    "reviewer",
    "review_date",
    "snapshot_version",
    "sample_strata",
    "primary_stratum",
    "source_row_index",
    "paper_id",
    "paper_title",
    "paper_year",
    "material_id",
    "formula_extracted",
    "formula_corrected",
    "formula_valid",
    "family_extracted",
    "family_corrected",
    "family_valid",
    "tc_extracted_k",
    "tc_corrected_k",
    "tc_valid",
    "tc_type_extracted",
    "tc_type_corrected",
    "pressure_extracted_gpa",
    "pressure_corrected_gpa",
    "pressure_valid",
    "pressure_role_extracted",
    "pressure_role_corrected",
    "pressure_role_valid",
    "ambient_extracted",
    "ambient_corrected",
    "ambient_valid",
    "evidence_type_extracted",
    "evidence_type_corrected",
    "evidence_type_valid",
    "is_theoretical_extracted",
    "is_theoretical_corrected",
    "is_theoretical_valid",
    "measurement_extracted",
    "measurement_corrected",
    "needs_review_extracted",
    "should_exclude_from_main",
    "exclusion_reason",
    "source_quote_or_location",
    "notes",
]

COMPUTATIONAL_TERMS = [
    "first-principles",
    "density functional",
    "dft",
    "ab initio",
    "calculated",
    "calculate",
    "prediction",
    "eliashberg",
    "electron-phonon coupling",
]

EXPERIMENTAL_TERMS = [
    "we measured",
    "we have measured",
    "we synthesized",
    "we have synthesized",
    "we report",
    "we observe",
    "resistivity",
    "susceptibility",
    "specific heat",
    "photoemission",
    "arpes",
    "nmr",
    "neutron",
    "muon",
    "andreev",
    "magnetization",
    "transport",
]


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
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    missing = [paper_id for paper_id in paper_ids if paper_id not in cache]
    for i, paper_id in enumerate(missing, start=1):
        encoded = urllib.parse.quote(paper_id, safe="")
        cache[paper_id] = fetch_json(f"/paper/{encoded}")
        if i % 25 == 0 or i == len(missing):
            print(f"cached Tc-band paper metadata {i}/{len(missing)}")
    CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False))
    return cache


def parse_float(value: object) -> float | None:
    s = str(value or "").strip()
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


def normalized_formula(value: object, drop_variables: bool = False) -> str:
    s = str(value or "").lower()
    s = (
        s.replace("δ", "delta")
        .replace("Δ", "delta")
        .replace("−", "-")
        .replace("–", "-")
    )
    if drop_variables:
        s = re.sub(r"(delta|epsilon|[wxyz])", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def elements(value: object) -> set[str]:
    return set(re.findall(r"[A-Z][a-z]?", str(value or "")))


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
            score += 115
        elif material_loose == target_loose:
            score += 95
        elif target_norm and (target_norm in material_norm or material_norm in target_norm):
            score += 60
        elif target_elements and material_elements and target_elements == material_elements:
            score += 35
        elif target_elements and material_elements:
            score += 8 * len(target_elements & material_elements) / len(target_elements)

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


def formula_looks_valid(formula: str) -> bool:
    if len(formula.strip()) < 2:
        return False
    if re.search(
        r"(?:interface|graphene|sample|system|compound|material|superconductor|film)",
        formula,
        re.IGNORECASE,
    ):
        return False
    return bool(re.search(r"[A-Za-z]", formula)) and bool(re.search(r"\d|[A-Z][a-z]?", formula))


def family_looks_valid(family: str, formula: str, title: str) -> bool:
    els = elements(formula)
    text = f"{formula} {title}".lower()
    if family == "cuprate":
        return ("Cu" in els and "O" in els) or "cuprate" in text
    if family == "iron_based":
        return "Fe" in els and bool(els & {"As", "P", "Se", "Te"})
    if family == "hydride":
        return "H" in els or "hydride" in text
    if family == "mgb2":
        return "Mg" in els and "B" in els
    if family == "elemental":
        return len(els) == 1
    if family == "nickelate":
        return "Ni" in els or "nickelate" in text
    if family == "kagome":
        return "kagome" in text or ("V" in els and "Sb" in els)
    return True


def infer_theory_flag(row: pd.Series, paper: dict, material: dict | None) -> bool:
    text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
    measurement = str((material or {}).get("measurement") or "").lower()
    paper_type = str((material or {}).get("paper_type") or "").lower()
    extracted = parse_bool(row["is_theoretical_extracted"])

    if paper_type == "computational" or measurement == "calculation":
        return True
    if paper_type == "experimental":
        return False
    if measurement and measurement != "unknown":
        return False
    if any(term in text for term in EXPERIMENTAL_TERMS):
        return False
    if any(term in text for term in COMPUTATIONAL_TERMS):
        return True
    return bool(extracted)


def pressure_role(
    row: pd.Series, paper: dict, material: dict | None
) -> tuple[object, str, str, str, bool, bool | None]:
    extracted_pressure = parse_float(row["pressure_extracted_gpa"])
    material_pressure = parse_float((material or {}).get("pressure_gpa"))
    extracted_ambient = parse_bool(row["ambient_extracted"])
    text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()

    if extracted_pressure is None:
        extracted_role = "none"
    elif abs(extracted_pressure) < 1e-9:
        extracted_role = "none"
    else:
        extracted_role = "measurement"

    if extracted_pressure is not None and re.search(r"(high pressure synthesis|grown at high pressure|prepared .*gpa|synthesis .*gpa)", text):
        corrected_role = "synthesis"
    elif (material or {}).get("evidence_type") == "cited":
        corrected_role = "cited/contextual"
    else:
        corrected_role = extracted_role

    if material_pressure is not None:
        pressure_valid = (
            extracted_pressure is not None and abs(extracted_pressure - material_pressure) <= 0.05
        )
        corrected_pressure: object = material_pressure
    else:
        pressure_valid = extracted_pressure in {None, 0.0}
        corrected_pressure = ""

    if corrected_role == "synthesis":
        pressure_valid = extracted_pressure is not None
        corrected_pressure = extracted_pressure if extracted_pressure is not None else ""
        ambient_corrected = True
    else:
        applied_pressure = material_pressure if material_pressure is not None else extracted_pressure
        ambient_corrected = not (applied_pressure is not None and applied_pressure > 0)

    ambient_valid = (
        extracted_ambient == ambient_corrected if extracted_ambient is not None else None
    )
    return (
        corrected_pressure,
        bool_text(pressure_valid),
        corrected_role,
        bool_text(extracted_role == corrected_role),
        ambient_corrected,
        ambient_valid,
    )


def validate_row(row: pd.Series, paper: dict) -> dict[str, object]:
    material = match_material(row, paper)
    title = paper.get("title", "")
    formula = row["formula_extracted"]
    target_tc = parse_float(row["tc_extracted_k"])

    if material is None:
        formula_valid = formula_looks_valid(formula)
        tc_valid = False
        evidence = "unknown"
        measurement = ""
        tc_type = ""
    else:
        formula_valid = material["_match_score"] >= 25 or formula_looks_valid(formula)
        material_tc = parse_float(material.get("tc_kelvin"))
        tc_valid = material_tc is not None and target_tc is not None and abs(material_tc - target_tc) <= 0.6
        evidence = material.get("evidence_type") or "unknown"
        measurement = material.get("measurement") or ""
        tc_type = material.get("tc_type") or ""

    family_valid = family_looks_valid(row["family_extracted"], formula, title)
    corrected_theory = infer_theory_flag(row, paper, material)
    extracted_theory = parse_bool(row["is_theoretical_extracted"])
    (
        corrected_pressure,
        pressure_valid,
        corrected_role,
        pressure_role_valid,
        ambient_corrected,
        ambient_valid,
    ) = pressure_role(row, paper, material)
    pressure_role_extracted = (
        "none"
        if parse_float(row["pressure_extracted_gpa"]) in {None, 0.0}
        else "measurement"
    )

    evidence_valid = evidence == "primary"
    evidence_unknown = evidence == "unknown"
    exclude = (not formula_valid) or (not tc_valid) or evidence == "cited"
    exclusion_reason = ""
    if exclude:
        if evidence != "primary":
            exclusion_reason = "not_primary_evidence"
        elif not tc_valid:
            exclusion_reason = "tc_extraction_error"
        elif not formula_valid:
            exclusion_reason = "formula_extraction_error"

    updates: dict[str, object] = {
        "reviewer": REVIEWER,
        "review_date": REVIEW_DATE,
        "paper_title": title,
        "formula_valid": bool_text(formula_valid),
        "family_valid": bool_text(family_valid),
        "tc_valid": bool_text(tc_valid),
        "tc_type_extracted": tc_type,
        "pressure_corrected_gpa": corrected_pressure,
        "pressure_valid": pressure_valid,
        "pressure_role_extracted": pressure_role_extracted,
        "pressure_role_corrected": corrected_role,
        "pressure_role_valid": pressure_role_valid,
        "ambient_corrected": bool_text(ambient_corrected),
        "ambient_valid": bool_text(ambient_valid),
        "evidence_type_extracted": evidence,
        "evidence_type_corrected": evidence,
        "evidence_type_valid": bool_text(evidence_valid),
        "is_theoretical_corrected": bool_text(corrected_theory),
        "is_theoretical_valid": bool_text(extracted_theory == corrected_theory),
        "measurement_extracted": measurement,
        "measurement_corrected": measurement,
        "should_exclude_from_main": "" if evidence_unknown and not exclude else bool_text(exclude),
        "exclusion_reason": exclusion_reason,
        "source_quote_or_location": (
            f"SCLib paper endpoint: {title}; matched record "
            f"{(material or {}).get('formula', '')}, Tc={(material or {}).get('tc_kelvin', '')}, "
            f"evidence={evidence}."
        ),
        "notes": (
            DEFAULT_NOTE + " Evidence type is unresolved and needs full-text verification."
            if evidence_unknown
            else DEFAULT_NOTE
        ),
    }

    if material is not None and normalized_formula(material.get("formula")) != normalized_formula(formula):
        if normalized_formula(material.get("formula"), drop_variables=True) != normalized_formula(
            formula, drop_variables=True
        ):
            updates["formula_corrected"] = material.get("formula", "")

    return updates


def score_field(frame: pd.DataFrame, field: str) -> tuple[int, int, float | None]:
    values = frame[field].map(parse_bool).dropna()
    n = len(values)
    if not n:
        return 0, 0, None
    k = int(values.sum())
    return n, k, k / n


def target_mask(frame: pd.DataFrame) -> pd.Series:
    mask = pd.Series(False, index=frame.index)
    for stratum in TARGET_STRATA:
        mask |= frame["sample_strata"].str.contains(stratum, regex=False)
    return mask


def write_review_queue(frame: pd.DataFrame) -> None:
    rows = []
    for _, row in frame.iterrows():
        false_fields = [field for field in VALIDATION_FIELDS if parse_bool(row.get(field)) is False]
        if parse_bool(row.get("should_exclude_from_main")) is True or false_fields:
            rows.append(
                {
                    "validation_id": row["validation_id"],
                    "sample_strata": row["sample_strata"],
                    "paper_id": row["paper_id"],
                    "paper_title": row["paper_title"],
                    "formula_extracted": row["formula_extracted"],
                    "family_extracted": row["family_extracted"],
                    "tc_extracted_k": row["tc_extracted_k"],
                    "false_fields": ";".join(false_fields),
                    "should_exclude_from_main": row["should_exclude_from_main"],
                    "exclusion_reason": row["exclusion_reason"],
                    "source_quote_or_location": row["source_quote_or_location"],
                    "notes": row["notes"],
                }
            )

    with REVIEW_QUEUE.open("w", newline="") as handle:
        fieldnames = [
            "validation_id",
            "sample_strata",
            "paper_id",
            "paper_title",
            "formula_extracted",
            "family_extracted",
            "tc_extracted_k",
            "false_fields",
            "should_exclude_from_main",
            "exclusion_reason",
            "source_quote_or_location",
            "notes",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(frame: pd.DataFrame, newly_updated: int) -> None:
    lines = [
        "# Tc-Band Validation Precheck",
        "",
        f"- Review date: {REVIEW_DATE}",
        f"- Target strata: {', '.join(TARGET_STRATA)}",
        f"- Target rows: {len(frame)}",
        f"- Newly updated rows: {newly_updated}",
        f"- Reviewed target rows after this pass: {int(frame['formula_valid'].astype(str).str.len().gt(0).sum())}",
        "",
        "## Field-Level Metrics by Stratum",
        "",
        "| Stratum | Field | Reviewed n | Valid n | Accuracy |",
        "|---|---|---:|---:|---:|",
    ]

    for stratum in TARGET_STRATA:
        group = frame[frame["sample_strata"].str.contains(stratum, regex=False)]
        for field in VALIDATION_FIELDS:
            n, k, acc = score_field(group, field)
            acc_text = "" if acc is None else f"{acc:.1%}"
            lines.append(f"| {stratum} | {field} | {n} | {k} | {acc_text} |")

    exclude_vals = frame["should_exclude_from_main"].map(parse_bool).dropna()
    pending_exclude = int(frame["should_exclude_from_main"].astype(str).str.len().eq(0).sum())
    false_theory = int((frame["is_theoretical_valid"].map(parse_bool) == False).sum())
    false_evidence = int((frame["evidence_type_valid"].map(parse_bool) == False).sum())
    false_tc = int((frame["tc_valid"].map(parse_bool) == False).sum())

    lines.extend(
        [
            "",
            "## Initial Findings",
            "",
            f"- Rows currently marked for exclusion among reviewed target rows: {int(exclude_vals.sum()) if len(exclude_vals) else 0}.",
            f"- Rows left pending rather than excluded because evidence is unresolved at API/abstract level: {pending_exclude}.",
            f"- Theory/experiment mismatches among target rows: {false_theory}.",
            f"- Non-primary or unresolved evidence rows among target rows: {false_evidence}.",
            f"- Tc mismatches among target rows: {false_tc}.",
            "- These are preliminary API/abstract-level checks; review-queue rows should be full-text checked before manuscript-level claims.",
            "",
            f"Detailed review queue: `{REVIEW_QUEUE.name}`.",
            "",
        ]
    )
    SUMMARY.write_text("\n".join(lines))


def main() -> None:
    df = pd.read_csv(SAMPLE, dtype=str, keep_default_na=False)
    for column in CANONICAL_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    mask = target_mask(df)
    target = df.loc[mask].copy()
    todo = target[
        (target["reviewer"].astype(str).str.len() == 0)
        | (target["notes"].astype(str).str.startswith(DEFAULT_NOTE))
    ].copy()
    paper_ids = list(dict.fromkeys(todo["paper_id"].tolist()))
    cache = load_paper_cache(paper_ids)

    newly_updated = 0
    for idx, row in todo.iterrows():
        updates = validate_row(row, cache[row["paper_id"]])
        for key, value in updates.items():
            df.loc[idx, key] = "" if value is None else value
        newly_updated += 1

    extras = [column for column in df.columns if column not in CANONICAL_COLUMNS]
    df = df[CANONICAL_COLUMNS + extras]
    df.to_csv(SAMPLE, index=False)

    updated_target = df.loc[mask].copy()
    write_review_queue(updated_target)
    write_summary(updated_target, newly_updated)
    print(f"Applied Tc-band precheck updates to {newly_updated} rows")
    print(f"Wrote {SUMMARY}")
    print(f"Wrote {REVIEW_QUEUE}")


if __name__ == "__main__":
    main()
