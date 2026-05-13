"""Fair dual-LLM consistency check: Gemini (SCLib V2 pipeline) vs Claude
(Anthropic), holding the prompt and parsing logic identical.

The original P1-3 script used a hand-written 5-field prompt for Claude and
compared it against SCLib's full V2 output -- prompt drift contaminated the
comparison. This V2 script eliminates that confound:

  * Same V2 prompt body (copied verbatim from
    /opt/SCLib_JZIS/ingestion/ingestion/extract/material_ner.py)
  * Same numeric coercion / field whitelist as SCLib's _coerce_float
  * Same family classifier (copied from SCLib's nims.classify_family)
  * Same pressure-class derivation on both sides
  * Same paired-record matching (best formula similarity)

Input difference (declared in Methods as a Limitation):
  SCLib's Gemini sees the full extracted body (title + abstract + first
  ~8 sections, capped at 16k chars). Claude only sees title + abstract
  because the scoping review workspace cannot reach the on-VPS body
  store. The comparison therefore charts Claude-on-abstract vs
  Gemini-on-full-text -- which is still informative for any record
  whose superconducting properties are reported in the abstract.

Outputs (under analysis_outputs/2026.05.13/):
    dual_llm_consistency_v2_records.csv  - per-record comparison
    dual_llm_consistency_v2_summary.json - aggregate metrics

Run with:
    ANTHROPIC_API_KEY=... python3 validation/dual_llm_consistency_v2.py
"""
from __future__ import annotations

import csv
import json
import os
import random
import re
import time
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import requests


API_BASE = "https://api.jzis.org/v1"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = PROJECT_ROOT / "data_freeze/snapshots/2026.05.13"
OUTPUT_DIR = PROJECT_ROOT / "analysis_outputs/2026.05.13"
USER_AGENT = "SCLib-scoping-review-dual-llm-v2/0.1"
SAMPLE_SIZE = 100
RANDOM_SEED = 20260513
TC_TOLERANCE_K = 10.0
FORMULA_SIM_THRESHOLD = 0.8
CLAUDE_MODEL = "claude-haiku-4-5"
ANTHROPIC_KEY_ENV = "ANTHROPIC_API_KEY"


# ---------------------------------------------------------------------------
# V2 prompt, copied verbatim from SCLib material_ner.py
# (commit ref: /opt/SCLib_JZIS/ingestion/ingestion/extract/material_ner.py)
# ---------------------------------------------------------------------------

_V2_PROMPT_CORE = """\
Extract superconducting material data from the text below. Return a
JSON array only. One object per (material, measurement) pair. If no
superconducting material is measured, return [].

REQUIRED per record:
- formula: chemical formula as written in the text (e.g. "La3Ni2O7")
- tc_kelvin: critical temperature in Kelvin, null if not stated
- tc_type: "onset" | "zero_resistance" | "midpoint" | "unknown"
- pressure_gpa: pressure in GPa (0.0 if ambient, null if not stated)
- measurement: "resistivity" | "susceptibility" | "specific_heat" |
               "muSR" | "ARPES" | "STM" | "neutron" | "unknown"
- confidence: 0.0-1.0 -- your confidence the text actually reports this

EXTRACT IF PRESENT (omit or set null otherwise):
- pairing_symmetry: "d-wave" | "s-wave" | "s_pm" | "p-wave" | "unknown"
- gap_structure: "full_gap" | "nodal" | "multi_gap" | "unknown"
- crystal_structure: space group or structure type (e.g. "I4/mmm")
- space_group: space group symbol or number (e.g. "I4/mmm (#139)")
- structure_phase: RP or cuprate phase label ("1212", "2222", "1313",
                   "infinite_layer", "cuprate_214", "cuprate_123", ...)
- lattice_a, lattice_c: lattice parameters in angstrom (numbers)
- t_cdw_k, t_sdw_k, t_afm_k: competing-order transition temps in K
- rho_exponent: normal-state resistivity exponent n (rho ~ T^n)
- competing_order: "CDW" | "AFM" | "SDW" | "Mott_insulator" | "PDW"
- hc2_tesla: upper critical field in Tesla
- hc2_conditions: conditions string for Hc2 (e.g. "0 K, H parallel c")
- lambda_eph: electron-phonon coupling constant lambda
- omega_log_k: logarithmic average phonon frequency in Kelvin
- rho_s_mev: superfluid stiffness rho_s in meV
- ambient_sc: true iff superconducting at 0 GPa
- sample_form: "single_crystal" | "polycrystal" | "thin_film" |
               "powder" | "wire"
- substrate: substrate material for thin films
- pressure_type: "hydrostatic" | "uniaxial" | "chemical" | "none"
- doping_type: "hole" | "electron" | "isovalent" | "none"
- doping_level: numeric doping x (0..1 range)
- is_topological: true iff the paper claims topological SC features
- is_unconventional: true iff explicitly described as unconventional
                     / non-BCS
- is_2d_or_interface: true iff 2D material or interface superconductor
- disputed: true iff the paper mentions contested / retracted results

RULES:
- Only extract materials explicitly measured for superconductivity.
- Do not invent data. Fields not in the text must be null / omitted.
- If Tc > 300 K or Tc < 0.01 K, set confidence <= 0.3.
- Distinguish experimental measurements from theoretical predictions.
  If the paper only predicts Tc from DFT, mark measurement="unknown"
  and confidence <= 0.5.
- For structure_phase, look for patterns like "1212 phase", "n=2 RP",
  "infinite layer", "YBCO", "La2CuO4" etc.
- For rho_exponent, look for "T-linear" (n=1.0), "T^2" (n=2.0),
  "rho proportional to T^n with n=..."
- lambda_eph / omega_log_k ONLY from DFT or Eliashberg papers.

Text:
---
{{BODY}}
---
"""


_V2_FIELDS = (
    "tc_kelvin", "tc_type", "pressure_gpa", "measurement", "confidence",
    "pairing_symmetry", "gap_structure",
    "crystal_structure", "space_group", "structure_phase",
    "lattice_a", "lattice_c",
    "t_cdw_k", "t_sdw_k", "t_afm_k", "rho_exponent", "competing_order",
    "hc2_tesla", "hc2_conditions",
    "lambda_eph", "omega_log_k", "rho_s_mev",
    "ambient_sc", "sample_form", "substrate",
    "pressure_type", "doping_type", "doping_level",
    "is_topological", "is_unconventional", "is_2d_or_interface",
    "disputed",
)
_NUMERIC_FIELDS = {
    "tc_kelvin", "pressure_gpa", "confidence",
    "lattice_a", "lattice_c",
    "t_cdw_k", "t_sdw_k", "t_afm_k", "rho_exponent",
    "hc2_tesla", "lambda_eph", "omega_log_k", "rho_s_mev",
    "doping_level",
}
_BOOL_FIELDS = {
    "ambient_sc", "is_topological", "is_unconventional",
    "is_2d_or_interface", "disputed",
}


# ---------------------------------------------------------------------------
# Numeric coercion, copied from SCLib material_ner._coerce_float
# ---------------------------------------------------------------------------

_RANGE_RE = re.compile(r"^\s*([-+]?\d*\.?\d+)\s*[-–—]\s*([-+]?\d*\.?\d+)")
_NUM_RE = re.compile(r"[-+]?\d*\.?\d+")
_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _coerce_float(v: Any) -> float | None:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s:
        return None
    m = _RANGE_RE.match(s)
    if m:
        try:
            return (float(m.group(1)) + float(m.group(2))) / 2
        except (TypeError, ValueError):
            return None
    nm = _NUM_RE.search(s)
    if not nm:
        return None
    try:
        return float(nm.group(0))
    except (TypeError, ValueError):
        return None


def _coerce_bool(v: Any) -> bool | None:
    if isinstance(v, bool):
        return v
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return bool(v)
    s = str(v).strip().lower()
    if s in {"true", "yes", "y", "1"}:
        return True
    if s in {"false", "no", "n", "0"}:
        return False
    return None


def _parse_json(text: str) -> list[Any] | None:
    text = _JSON_FENCE_RE.sub("", text).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "materials" in data:
        inner = data["materials"]
        return inner if isinstance(inner, list) else None
    if isinstance(data, dict) and "records" in data:
        inner = data["records"]
        return inner if isinstance(inner, list) else None
    return None


def clean_record(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Apply SCLib's V2 cleaning rules to a single raw record."""
    if not isinstance(raw, dict) or "formula" not in raw:
        return None
    record: dict[str, Any] = {"formula": str(raw["formula"]).strip()}
    if not record["formula"]:
        return None
    for field_name in _V2_FIELDS:
        if field_name not in raw:
            continue
        value = raw[field_name]
        if value is None or value == "":
            continue
        if field_name in _NUMERIC_FIELDS:
            coerced = _coerce_float(value)
            if coerced is None:
                continue
            record[field_name] = coerced
        elif field_name in _BOOL_FIELDS:
            record[field_name] = _coerce_bool(value)
        else:
            record[field_name] = str(value).strip() or None
    tc = record.get("tc_kelvin")
    conf = record.get("confidence") or 0.0
    if tc is not None and (tc > 300 or tc < 0.01) and conf >= 0.3:
        record["confidence"] = 0.3
    if "ambient_sc" not in record and record.get("pressure_gpa") == 0:
        if record.get("tc_kelvin") is not None:
            record["ambient_sc"] = True
    return record


# ---------------------------------------------------------------------------
# Family classifier, copied from SCLib ingestion/nims.py
# ---------------------------------------------------------------------------

def classify_family(formula: str) -> str | None:
    f = formula.strip()
    fl = f.lower()
    if re.fullmatch(r"mgb2", fl):
        return "mgb2"
    elements = re.findall(r"[A-Z][a-z]?", f)
    high_h = bool(re.search(r"H(?:[2-9]|1[0-9])\b", f))
    if high_h and "O" not in elements and "C" not in elements:
        partners = {"S", "Se", "La", "Y", "Ca", "Mg", "Sr", "Ba",
                    "Th", "Sc", "Yb", "Ce", "Pr", "Nd"}
        if any(e in partners for e in elements):
            return "hydride"
    if "fe" in fl and re.search(r"(as|se|te|p)", fl):
        return "iron_based"
    if "cu" in fl and "o" in fl and re.search(
        r"(la|y|ba|sr|ca|bi|hg|tl|nd|sm|gd)", fl
    ):
        return "cuprate"
    if re.search(r"(ube|cein|ceco|cecu|ypb|yrh|uru)", fl):
        return "heavy_fermion"
    if re.search(r"(nb3sn|nb3ge|v3si|nbti|pb\b|hg\b|\bsn\b)", fl):
        return "conventional"
    return None


def classify_pressure(pressure_gpa: float | None) -> str:
    """V2 convention: 0.0 = ambient, null = unknown, >0 = high_pressure."""
    if pressure_gpa is None:
        return "unknown"
    if pressure_gpa <= 0.05:
        return "ambient"
    return "high_pressure"


# ---------------------------------------------------------------------------
# Comparison row
# ---------------------------------------------------------------------------

@dataclass
class ComparisonRow:
    paper_id: str
    paper_year: int | None
    paper_title: str
    claude_formula: str
    claude_tc: float | None
    claude_pressure_class: str
    claude_pressure_gpa: float | None
    claude_family: str | None
    sclib_formula: str | None
    sclib_tc: float | None
    sclib_pressure_class: str
    sclib_pressure_gpa: float | None
    sclib_family: str | None
    formula_similarity: float
    formula_match: bool
    tc_delta: float | None
    tc_match: bool
    pressure_class_match: bool
    family_match: bool
    notes: str = ""


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def fetch_json(session: requests.Session, path: str,
               params: dict[str, Any] | None = None) -> dict | None:
    url = f"{API_BASE}{path}"
    for attempt in range(4):
        try:
            resp = session.get(url, params=params, timeout=30,
                               headers={"User-Agent": USER_AGENT})
        except requests.RequestException:
            time.sleep(1.5 * (attempt + 1))
            continue
        if resp.status_code == 404:
            return None
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429 or resp.status_code >= 500:
            time.sleep(2.0 * (attempt + 1))
            continue
        return None
    return None


def sample_paper_ids() -> list[str]:
    seen: set[str] = set()
    path = SNAPSHOT_DIR / "timeline_points.csv"
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = (row.get("paper_id") or "").strip()
            if pid:
                seen.add(pid)
    rng = random.Random(RANDOM_SEED)
    ids = sorted(seen)
    rng.shuffle(ids)
    return ids


def formula_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def best_sclib_match(claude_formula: str,
                     sclib_records: list[dict]) -> tuple[dict | None, float]:
    best, best_sim = None, 0.0
    for rec in sclib_records:
        sim = formula_similarity(claude_formula, rec.get("formula") or "")
        if sim > best_sim:
            best_sim = sim
            best = rec
    return best, best_sim


def call_claude(client: Any, title: str, abstract: str) -> list[dict]:
    """Call Claude with the SCLib V2 prompt. Returns cleaned records."""
    body = f"Title: {title}\nAbstract: {abstract}"
    prompt = _V2_PROMPT_CORE.replace("{{BODY}}", body)
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in msg.content if hasattr(b, "text"))
    raw_records = _parse_json(text)
    if raw_records is None:
        return []
    cleaned: list[dict[str, Any]] = []
    for r in raw_records:
        c = clean_record(r) if isinstance(r, dict) else None
        if c is not None:
            cleaned.append(c)
    return cleaned


def write_skip_summary(reason: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "skipped",
        "reason": reason,
        "sample_size_target": SAMPLE_SIZE,
        "claude_model": CLAUDE_MODEL,
        "note": "Re-run validation/dual_llm_consistency_v2.py with a valid "
                f"{ANTHROPIC_KEY_ENV}.",
    }
    out = OUTPUT_DIR / "dual_llm_consistency_v2_summary.json"
    out.write_text(json.dumps(payload, indent=2))
    print(f"Skip recorded: {reason}\nWrote {out}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    key = os.environ.get(ANTHROPIC_KEY_ENV, "")
    if not key:
        write_skip_summary(f"{ANTHROPIC_KEY_ENV} not set in environment.")
        return
    try:
        from anthropic import Anthropic, AuthenticationError
    except ImportError as exc:
        write_skip_summary(f"anthropic SDK not importable: {exc}")
        return

    client = Anthropic(api_key=key)
    try:
        client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=8,
            messages=[{"role": "user", "content": "ping"}],
        )
    except AuthenticationError as exc:
        write_skip_summary(f"AuthenticationError on probe: {exc}")
        return
    except Exception as exc:
        write_skip_summary(f"Probe call failed: {exc}")
        return

    session = requests.Session()
    candidate_ids = sample_paper_ids()
    rows: list[ComparisonRow] = []
    accepted_papers = 0
    skipped_papers: list[dict] = []
    sclib_extracted_total = 0
    claude_extracted_total = 0

    cursor = 0
    while accepted_papers < SAMPLE_SIZE and cursor < len(candidate_ids):
        paper_id = candidate_ids[cursor]
        cursor += 1
        paper = fetch_json(session, f"/paper/{paper_id}")
        if not paper or not paper.get("abstract"):
            skipped_papers.append({"paper_id": paper_id, "reason": "no abstract"})
            continue
        sclib_raw = paper.get("materials_extracted") or []
        if not sclib_raw:
            skipped_papers.append({"paper_id": paper_id, "reason": "no SCLib records"})
            continue
        title = paper.get("title") or ""
        abstract = paper.get("abstract") or ""

        try:
            claude_records = call_claude(client, title, abstract)
        except AuthenticationError as exc:
            write_skip_summary(f"AuthenticationError during run: {exc}")
            return
        except Exception as exc:
            skipped_papers.append({"paper_id": paper_id,
                                   "reason": f"claude call failed: {exc}"})
            continue
        if not claude_records:
            skipped_papers.append({"paper_id": paper_id,
                                   "reason": "claude returned no records"})
            continue

        # SCLib's stored materials_extracted is already the cleaned V2 output
        # from the Gemini pipeline. We do NOT re-clean -- it's already gone
        # through the same _coerce_float / field whitelist on the SCLib side.
        sclib_records = [r for r in sclib_raw if isinstance(r, dict) and r.get("formula")]
        if not sclib_records:
            skipped_papers.append({"paper_id": paper_id,
                                   "reason": "SCLib records lack formula"})
            continue

        accepted_papers += 1
        sclib_extracted_total += len(sclib_records)
        claude_extracted_total += len(claude_records)

        year_raw = paper.get("date_submitted") or ""
        paper_year = int(year_raw[:4]) if year_raw[:4].isdigit() else None

        for cr in claude_records:
            claude_formula = cr.get("formula") or ""
            claude_tc = cr.get("tc_kelvin")
            claude_p_gpa = cr.get("pressure_gpa")
            claude_p_class = classify_pressure(claude_p_gpa)
            claude_family = classify_family(claude_formula)

            match, sim = best_sclib_match(claude_formula, sclib_records)
            sclib_formula = match.get("formula") if match else None
            sclib_tc = match.get("tc_kelvin") if match else None
            sclib_p_gpa = match.get("pressure_gpa") if match else None
            sclib_p_class = classify_pressure(sclib_p_gpa) if match else "unknown"
            sclib_family = classify_family(sclib_formula or "") if match else None

            tc_delta = None
            tc_match = False
            if claude_tc is not None and sclib_tc is not None:
                tc_delta = sclib_tc - claude_tc
                tc_match = abs(tc_delta) <= TC_TOLERANCE_K
            elif claude_tc is None and sclib_tc is None:
                tc_match = True  # both silent counts as agreement

            formula_match = sim >= FORMULA_SIM_THRESHOLD
            pressure_class_match = claude_p_class == sclib_p_class
            family_match = claude_family == sclib_family

            notes = []
            if match is None:
                notes.append("no SCLib match")
            elif not formula_match:
                notes.append(f"formula similarity {sim:.2f} below threshold")
            if not tc_match and not (claude_tc is None and sclib_tc is None):
                notes.append("tc disagreement")
            if not pressure_class_match:
                notes.append("pressure class disagreement")
            if not family_match:
                notes.append("family disagreement")

            rows.append(ComparisonRow(
                paper_id=paper_id,
                paper_year=paper_year,
                paper_title=title,
                claude_formula=claude_formula,
                claude_tc=claude_tc,
                claude_pressure_class=claude_p_class,
                claude_pressure_gpa=claude_p_gpa,
                claude_family=claude_family,
                sclib_formula=sclib_formula,
                sclib_tc=sclib_tc,
                sclib_pressure_class=sclib_p_class,
                sclib_pressure_gpa=sclib_p_gpa,
                sclib_family=sclib_family,
                formula_similarity=round(sim, 4),
                formula_match=formula_match,
                tc_delta=round(tc_delta, 3) if tc_delta is not None else None,
                tc_match=tc_match,
                pressure_class_match=pressure_class_match,
                family_match=family_match,
                notes="; ".join(notes),
            ))

        if accepted_papers % 10 == 0:
            print(f"  processed {accepted_papers}/{SAMPLE_SIZE} papers", flush=True)

    csv_path = OUTPUT_DIR / "dual_llm_consistency_v2_records.csv"
    if rows:
        fieldnames = list(asdict(rows[0]).keys())
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(asdict(r))

    total = len(rows)

    def rate(predicate) -> float | None:
        if not total:
            return None
        return round(sum(1 for r in rows if predicate(r)) / total, 4)

    formula_rate = rate(lambda r: r.formula_match)
    tc_rate = rate(lambda r: r.tc_match)
    pressure_rate = rate(lambda r: r.pressure_class_match)
    family_rate = rate(lambda r: r.family_match)
    all_axes_rate = rate(
        lambda r: r.formula_match and r.tc_match and r.pressure_class_match
                  and r.family_match
    )

    low_conf = [
        asdict(r) for r in rows
        if not (r.formula_match and r.tc_match
                and r.pressure_class_match and r.family_match)
    ][:50]

    summary = {
        "status": "ok",
        "design": "fair-comparison-v2",
        "claude_model": CLAUDE_MODEL,
        "sclib_extractor": "gemini-2.5-flash via SCLib V2 NER pipeline",
        "prompt_source": "SCLib material_ner._V2_PROMPT_CORE (copied verbatim)",
        "input_to_claude": "title + abstract only (no full text)",
        "input_to_sclib": "title + abstract + first ~8 body sections (cap 16k chars)",
        "limitation": (
            "Claude receives less context than Gemini because the scoping "
            "review workspace cannot reach the on-VPS body store. "
            "Disagreements caused by body-only signals (Hc2, sample form, "
            "lambda_eph etc.) are expected. Comparable fields restricted "
            "to those reliably reported in abstracts: formula, tc_kelvin, "
            "pressure_class, family."
        ),
        "papers_target": SAMPLE_SIZE,
        "papers_with_pairings": accepted_papers,
        "papers_skipped": len(skipped_papers),
        "papers_skipped_reasons_head": skipped_papers[:20],
        "claude_records_total": claude_extracted_total,
        "sclib_records_total": sclib_extracted_total,
        "row_count": total,
        "tc_tolerance_K": TC_TOLERANCE_K,
        "formula_similarity_threshold": FORMULA_SIM_THRESHOLD,
        "match_rates": {
            "formula_match": formula_rate,
            "tc_within_tolerance": tc_rate,
            "pressure_class": pressure_rate,
            "family": family_rate,
            "all_four_axes": all_axes_rate,
        },
        "low_confidence_records_head": low_conf,
    }

    out = OUTPUT_DIR / "dual_llm_consistency_v2_summary.json"
    out.write_text(json.dumps(summary, indent=2))
    print()
    print(f"Papers paired: {accepted_papers}")
    print(f"Records compared: {total}")
    print(f"  formula match    : {formula_rate}")
    print(f"  tc match (+-10K) : {tc_rate}")
    print(f"  pressure class   : {pressure_rate}")
    print(f"  family           : {family_rate}")
    print(f"  all four axes    : {all_axes_rate}")
    print(f"Wrote {csv_path}")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
