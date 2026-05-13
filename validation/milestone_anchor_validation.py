"""Milestone anchor validation for the SCLib superconductor scoping review.

For each of 50 well-known superconducting materials we hold a literature-anchored
expected Tc value and pressure regime. The script queries the SCLib API to
recover the corresponding extracted record, then computes coverage (was the
material found?) and Tc accuracy (within +/- 10 K of the literature anchor) and
pressure-regime agreement.

API endpoints used (canonical SCLib v1):
    GET https://api.jzis.org/v1/materials?q=<formula>&limit=20  (q is honored
        by the server only loosely; results are tc-sorted, so we use it to
        document what the public-search endpoint surfaces).
    GET https://api.jzis.org/v1/materials/<material_id>         (direct lookup
        by `mat:<lowercased-formula>` ID; this is the authoritative match).

Outputs (under analysis_outputs/2026.05.13/):
    milestone_anchor_validation.csv  - per-material comparison
    milestone_anchor_validation.json - summary metrics
"""
from __future__ import annotations

import csv
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests


API_BASE = "https://api.jzis.org/v1"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = PROJECT_ROOT / "data_freeze/snapshots/2026.05.13"
OUTPUT_DIR = PROJECT_ROOT / "analysis_outputs/2026.05.13"

TC_TOLERANCE_K = 10.0
REQUEST_TIMEOUT = 30
USER_AGENT = "SCLib-scoping-review-milestone-validation/0.1"


@dataclass
class Milestone:
    formula: str
    expected_tc: float
    pressure_class: str  # "ambient" or "high_pressure"
    expected_pressure_gpa: float | None = None
    note: str = ""


# Reference Tc values are taken from the standard superconductivity literature
# (Mott/Bednorz-Muller cuprate sequence, MgB2 Nagamatsu 2001, hydride
# discoveries by Drozdov/Snider/Eremets, Hosono iron-pnictide reports,
# fulleride work by Tanigaki/Iwasa, A15 compounds, and elemental SC).
MILESTONES: list[Milestone] = [
    # --- Cuprates (ambient) ---
    Milestone("YBa2Cu3O7", 93, "ambient", note="Wu/Chu 1987 Y-123"),
    Milestone("Bi2Sr2Ca2Cu3O10", 110, "ambient", note="BSCCO-2223"),
    Milestone("Bi2Sr2CaCu2O8", 85, "ambient", note="BSCCO-2212"),
    Milestone("Tl2Ba2Ca2Cu3O10", 125, "ambient", note="Tl-2223"),
    Milestone("HgBa2Ca2Cu3O8", 134, "ambient", note="Hg-1223, max Tc among cuprates at ambient"),
    Milestone("La2CuO4", 38, "ambient", note="Bednorz-Muller parent compound (doped variant)"),
    Milestone("La1.85Sr0.15CuO4", 38, "ambient", note="LSCO optimal doping"),
    Milestone("Nd2CuO4", 24, "ambient", note="Electron-doped n-type cuprate"),
    Milestone("YBa2Cu4O8", 80, "ambient", note="Y-124"),
    Milestone("Tl2Ba2CuO6", 90, "ambient", note="Tl-2201"),
    # --- Hydrides (high pressure) ---
    Milestone("LaH10", 250, "high_pressure", 170, note="Drozdov/Eremets 2019"),
    Milestone("H3S", 203, "high_pressure", 155, note="Drozdov 2015"),
    Milestone("YH6", 224, "high_pressure", 166, note="Kong 2021"),
    Milestone("YH9", 243, "high_pressure", 200, note="Snider 2021"),
    Milestone("CaH6", 215, "high_pressure", 172, note="Ma 2022"),
    Milestone("CeH9", 95, "high_pressure", 130, note="Chen 2021"),
    Milestone("ThH10", 161, "high_pressure", 175, note="Semenok 2020"),
    Milestone("SnH4", 80, "high_pressure", 200, note="Predicted hydride"),
    # --- Iron-based (mostly ambient) ---
    Milestone("FeSe", 8, "ambient", note="Hsu 2008 FeSe bulk"),
    Milestone("LaFeAsO0.9F0.1", 26, "ambient", note="Kamihara 2008 1111"),
    Milestone("SmFeAsO0.85", 55, "ambient", note="Ren 2008 Sm-1111"),
    Milestone("Ba0.6K0.4Fe2As2", 38, "ambient", note="Rotter 2008 122"),
    Milestone("BaFe2As2", 0, "ambient", note="122 parent, non-SC; used as baseline reference"),
    Milestone("LiFeAs", 18, "ambient", note="111 stoichiometric SC"),
    Milestone("FeTe0.5Se0.5", 14, "ambient", note="11 iron chalcogenide"),
    Milestone("KFe2Se2", 32, "ambient", note="K-122 selenide"),
    # --- A15 / conventional intermetallic (ambient) ---
    Milestone("MgB2", 39, "ambient", note="Nagamatsu 2001"),
    Milestone("Nb3Ge", 23, "ambient", note="Highest A15 Tc"),
    Milestone("Nb3Sn", 18, "ambient", note="Workhorse A15"),
    Milestone("V3Si", 17, "ambient", note="A15 prototype"),
    Milestone("NbN", 16, "ambient", note="Nitride"),
    Milestone("NbTi", 9, "ambient", note="Alloy workhorse"),
    # --- Elemental (ambient unless noted) ---
    Milestone("Nb", 9.25, "ambient", note="Highest-Tc elemental at ambient"),
    Milestone("Pb", 7.2, "ambient", note="BCS textbook example"),
    Milestone("Hg", 4.15, "ambient", note="Onnes 1911 original"),
    Milestone("Al", 1.2, "ambient", note="BCS textbook"),
    Milestone("Sn", 3.7, "ambient", note="Elemental tin"),
    # --- Heavy fermion / unconventional (mostly ambient) ---
    Milestone("CeCoIn5", 2.3, "ambient", note="115 heavy fermion"),
    Milestone("CeCu2Si2", 0.6, "ambient", note="First heavy-fermion SC, Steglich 1979"),
    Milestone("UPt3", 0.5, "ambient", note="Triplet heavy fermion"),
    Milestone("PuCoGa5", 18.5, "ambient", note="Actinide 115"),
    Milestone("Sr2RuO4", 1.5, "ambient", note="Ruthenate (Maeno 1994)"),
    # --- Fullerides ---
    Milestone("K3C60", 19, "ambient", note="Alkali fulleride"),
    Milestone("Rb2CsC60", 33, "ambient", note="Highest-Tc ambient fulleride"),
    # --- Other notable systems ---
    Milestone("MgCNi3", 8, "ambient", note="Antiperovskite SC"),
    Milestone("Ba0.6K0.4BiO3", 30, "ambient", note="Bismuthate"),
    Milestone("CaC6", 11.5, "ambient", note="Graphite intercalation"),
    Milestone("LaPt2Si2", 1.8, "ambient", note="Heavy-element silicide"),
    Milestone("Nd0.85Sr0.15NiO2", 15, "ambient", note="Infinite-layer nickelate, Li 2019"),
    Milestone("Pb1Mo6S8", 14, "ambient", note="Chevrel phase"),
]
assert len(MILESTONES) == 50, f"Expected 50 milestones, got {len(MILESTONES)}"


def normalize_formula_to_id(formula: str) -> str:
    """Produce the canonical SCLib material_id from a formula string."""
    return "mat:" + formula.lower()


def fetch_json(session: requests.Session, path: str, params: dict[str, Any] | None = None) -> dict | None:
    url = f"{API_BASE}{path}"
    for attempt in range(4):
        try:
            resp = session.get(url, params=params, timeout=REQUEST_TIMEOUT,
                               headers={"User-Agent": USER_AGENT})
        except requests.RequestException as exc:
            if attempt == 3:
                raise RuntimeError(f"network error on {url}: {exc}") from exc
            time.sleep(1.5 * (attempt + 1))
            continue
        if resp.status_code == 404:
            return None
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in (429,) or resp.status_code >= 500:
            time.sleep(2.0 * (attempt + 1))
            continue
        raise RuntimeError(f"HTTP {resp.status_code} for {url}: {resp.text[:200]}")
    return None


_PRESSURE_RE = re.compile(r"P\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*GPa", re.IGNORECASE)


def parse_pressure_class(conditions: str | None) -> tuple[str, float | None]:
    """Classify the SCLib `tc_max_conditions` string as ambient or high pressure."""
    if not conditions:
        return ("unknown", None)
    lowered = conditions.lower()
    if "ambient" in lowered:
        return ("ambient", 0.0)
    match = _PRESSURE_RE.search(conditions)
    if match:
        return ("high_pressure", float(match.group(1)))
    # No explicit pressure marker: assume ambient by SCLib convention (most
    # cuprate / iron-based / elemental records omit the pressure tag for
    # ambient measurements). We do not penalize this in the metrics.
    return ("ambient_implicit", None)


@dataclass
class MilestoneResult:
    formula: str
    expected_tc: float
    expected_pressure_class: str
    expected_pressure_gpa: float | None
    note: str
    candidate_id: str
    found_in_api: bool
    sclib_formula: str | None
    sclib_family: str | None
    sclib_tc_max: float | None
    sclib_tc_ambient: float | None
    sclib_tc_max_conditions: str | None
    sclib_pressure_class: str
    sclib_pressure_gpa: float | None
    discovery_year: int | None
    total_papers: int | None
    tc_delta: float | None
    tc_within_tolerance: bool
    pressure_class_match: bool
    q_endpoint_top_hit_formula: str | None
    q_endpoint_top_hit_tc: float | None
    q_endpoint_contains_target: bool
    notes: str = ""


def load_snapshot_index() -> dict[str, dict[str, Any]]:
    """Lowercased formula -> snapshot row from materials_all_summary.csv."""
    path = SNAPSHOT_DIR / "materials_all_summary.csv"
    index: dict[str, dict[str, Any]] = {}
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            formula = (row.get("formula") or "").strip()
            if not formula:
                continue
            key = formula.lower()
            # Prefer the row with the largest total_papers if there are duplicates.
            existing = index.get(key)
            new_papers = int(row.get("total_papers") or 0)
            if existing is None or int(existing.get("total_papers") or 0) < new_papers:
                index[key] = row
    return index


def lookup_milestone(session: requests.Session,
                     milestone: Milestone,
                     snapshot_index: dict[str, dict[str, Any]]) -> MilestoneResult:
    candidate_id = normalize_formula_to_id(milestone.formula)
    # 1. Document the q=<formula> endpoint behavior (top hit + does it contain target).
    q_payload = fetch_json(session, "/materials", params={"q": milestone.formula, "limit": 20})
    q_top_formula: str | None = None
    q_top_tc: float | None = None
    q_contains = False
    if q_payload and q_payload.get("results"):
        first = q_payload["results"][0]
        q_top_formula = first.get("formula")
        q_top_tc = first.get("tc_max")
        target_lower = milestone.formula.lower()
        for r in q_payload["results"]:
            if (r.get("formula") or "").lower() == target_lower:
                q_contains = True
                break

    # 2. Authoritative lookup: direct ID GET.
    encoded = quote(candidate_id, safe="")
    detail = fetch_json(session, f"/materials/{encoded}")
    snapshot_row = snapshot_index.get(milestone.formula.lower())

    if detail is None and snapshot_row is not None:
        snap_id = snapshot_row.get("id")
        if snap_id:
            detail = fetch_json(session, f"/materials/{quote(snap_id, safe='')}")

    found = detail is not None
    sclib_formula = (detail or {}).get("formula") or (snapshot_row or {}).get("formula")
    sclib_family = (detail or {}).get("family") or (snapshot_row or {}).get("family")
    sclib_tc_max_raw = (detail or {}).get("tc_max")
    if sclib_tc_max_raw is None and snapshot_row is not None:
        sclib_tc_max_raw = snapshot_row.get("tc_max") or None
    sclib_tc_max = float(sclib_tc_max_raw) if sclib_tc_max_raw not in (None, "", "None") else None
    sclib_tc_amb_raw = (detail or {}).get("tc_ambient")
    if sclib_tc_amb_raw is None and snapshot_row is not None:
        sclib_tc_amb_raw = snapshot_row.get("tc_ambient") or None
    sclib_tc_ambient = float(sclib_tc_amb_raw) if sclib_tc_amb_raw not in (None, "", "None") else None
    sclib_conditions = (detail or {}).get("tc_max_conditions") or (snapshot_row or {}).get("tc_max_conditions")
    sclib_year_raw = (detail or {}).get("discovery_year")
    if sclib_year_raw is None and snapshot_row is not None:
        sclib_year_raw = snapshot_row.get("discovery_year") or None
    discovery_year = int(sclib_year_raw) if sclib_year_raw not in (None, "", "None") else None
    total_papers_raw = (detail or {}).get("total_papers")
    if total_papers_raw is None and snapshot_row is not None:
        total_papers_raw = snapshot_row.get("total_papers") or None
    total_papers = int(total_papers_raw) if total_papers_raw not in (None, "", "None") else None

    sclib_p_class, sclib_p_gpa = parse_pressure_class(sclib_conditions)

    # Tc comparison: prefer ambient Tc for ambient milestones, tc_max otherwise.
    if milestone.pressure_class == "ambient":
        sclib_tc_for_compare = sclib_tc_ambient if sclib_tc_ambient is not None else sclib_tc_max
    else:
        sclib_tc_for_compare = sclib_tc_max
    tc_delta = (sclib_tc_for_compare - milestone.expected_tc) if sclib_tc_for_compare is not None else None
    tc_within = (tc_delta is not None) and (abs(tc_delta) <= TC_TOLERANCE_K)

    if milestone.pressure_class == "ambient":
        pressure_match = sclib_p_class in ("ambient", "ambient_implicit")
    else:
        pressure_match = sclib_p_class == "high_pressure"

    notes = []
    if milestone.expected_tc == 0:
        notes.append("baseline non-SC reference; tc_within recorded but not meaningful")
    if not found:
        notes.append("not found via direct ID or snapshot fallback")

    return MilestoneResult(
        formula=milestone.formula,
        expected_tc=milestone.expected_tc,
        expected_pressure_class=milestone.pressure_class,
        expected_pressure_gpa=milestone.expected_pressure_gpa,
        note=milestone.note,
        candidate_id=candidate_id,
        found_in_api=found,
        sclib_formula=sclib_formula,
        sclib_family=sclib_family,
        sclib_tc_max=sclib_tc_max,
        sclib_tc_ambient=sclib_tc_ambient,
        sclib_tc_max_conditions=sclib_conditions,
        sclib_pressure_class=sclib_p_class,
        sclib_pressure_gpa=sclib_p_gpa,
        discovery_year=discovery_year,
        total_papers=total_papers,
        tc_delta=tc_delta,
        tc_within_tolerance=tc_within,
        pressure_class_match=pressure_match,
        q_endpoint_top_hit_formula=q_top_formula,
        q_endpoint_top_hit_tc=q_top_tc,
        q_endpoint_contains_target=q_contains,
        notes="; ".join(notes),
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_index = load_snapshot_index()
    session = requests.Session()

    results: list[MilestoneResult] = []
    for i, ms in enumerate(MILESTONES, 1):
        print(f"[{i:02d}/{len(MILESTONES)}] {ms.formula}", flush=True)
        results.append(lookup_milestone(session, ms, snapshot_index))

    csv_path = OUTPUT_DIR / "milestone_anchor_validation.csv"
    fieldnames = list(asdict(results[0]).keys())
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))

    total = len(results)
    found = sum(1 for r in results if r.found_in_api)
    tc_ok = sum(1 for r in results if r.tc_within_tolerance and r.expected_tc > 0)
    tc_ok_denominator = sum(1 for r in results if r.found_in_api and r.expected_tc > 0)
    pressure_ok = sum(1 for r in results if r.pressure_class_match)
    pressure_ok_denominator = sum(1 for r in results if r.found_in_api)
    q_hit_target = sum(1 for r in results if r.q_endpoint_contains_target)

    summary = {
        "milestone_count": total,
        "coverage": {
            "found_in_api": found,
            "missing": total - found,
            "rate": round(found / total, 4),
        },
        "tc_accuracy_within_10K": {
            "matches": tc_ok,
            "denominator_found_and_sc": tc_ok_denominator,
            "rate": round(tc_ok / tc_ok_denominator, 4) if tc_ok_denominator else None,
            "tolerance_K": TC_TOLERANCE_K,
        },
        "pressure_class_agreement": {
            "matches": pressure_ok,
            "denominator_found": pressure_ok_denominator,
            "rate": round(pressure_ok / pressure_ok_denominator, 4) if pressure_ok_denominator else None,
        },
        "public_q_endpoint": {
            "note": "GET /v1/materials?q=<formula>&limit=20 sorts by tc_max and does not filter; the q parameter is currently a no-op.",
            "queries_with_target_in_top20": q_hit_target,
            "total_queries": total,
        },
        "missing_formulas": [r.formula for r in results if not r.found_in_api],
        "tc_misses": [
            {
                "formula": r.formula,
                "expected_tc": r.expected_tc,
                "sclib_tc_max": r.sclib_tc_max,
                "sclib_tc_ambient": r.sclib_tc_ambient,
                "delta": r.tc_delta,
            }
            for r in results
            if r.found_in_api and r.expected_tc > 0 and not r.tc_within_tolerance
        ],
        "pressure_misses": [
            {
                "formula": r.formula,
                "expected_class": r.expected_pressure_class,
                "sclib_class": r.sclib_pressure_class,
                "sclib_conditions": r.sclib_tc_max_conditions,
            }
            for r in results
            if r.found_in_api and not r.pressure_class_match
        ],
        "api_base": API_BASE,
        "tolerance_K": TC_TOLERANCE_K,
    }

    json_path = OUTPUT_DIR / "milestone_anchor_validation.json"
    json_path.write_text(json.dumps(summary, indent=2))

    print()
    print(f"Coverage:      {summary['coverage']['found_in_api']}/{total}"
          f"  ({summary['coverage']['rate']:.1%})")
    tc_rate = summary["tc_accuracy_within_10K"]["rate"]
    print(f"Tc accuracy:   {tc_ok}/{tc_ok_denominator}"
          f"  ({'%.1f%%' % (tc_rate * 100) if tc_rate is not None else 'n/a'}) within +/-{TC_TOLERANCE_K} K")
    pr_rate = summary["pressure_class_agreement"]["rate"]
    print(f"Pressure agr.: {pressure_ok}/{pressure_ok_denominator}"
          f"  ({'%.1f%%' % (pr_rate * 100) if pr_rate is not None else 'n/a'})")
    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")


if __name__ == "__main__":
    main()
