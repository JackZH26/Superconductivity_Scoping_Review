"""Dual-LLM consistency check between SCLib's extraction and Claude sonnet-4-6.

For 100 papers sampled from the SCLib timeline:
  1. Fetch the SCLib paper detail (abstract + materials_extracted) from
     GET /v1/paper/{paper_id}.
  2. Ask Claude sonnet-4-6 to re-extract (formula, Tc, pressure) records from
     the same abstract using a strict JSON schema.
  3. For each Claude-extracted record, find the closest SCLib record by
     fuzzy formula match and compute:
       - Tc agreement (within 10 K)
       - Formula similarity (SequenceMatcher ratio > 0.8)
       - Pressure-class match (ambient / high-pressure / unknown)

Outputs (under analysis_outputs/2026.05.13/):
    dual_llm_consistency_records.csv  - per-record comparison
    dual_llm_consistency_summary.json - aggregate metrics + low-confidence rows

The script is defensive: if the ANTHROPIC_API_KEY is missing or returns 401,
it writes a status JSON documenting the skip and exits with code 0.
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
USER_AGENT = "SCLib-scoping-review-dual-llm/0.1"
SAMPLE_SIZE = 100
RANDOM_SEED = 20260513
TC_TOLERANCE_K = 10.0
FORMULA_SIM_THRESHOLD = 0.8
CLAUDE_MODEL = "claude-sonnet-4-6"
ANTHROPIC_KEY_ENV = "ANTHROPIC_API_KEY"

CLAUDE_SYSTEM_PROMPT = (
    "You are a careful superconductivity NER extractor. From the supplied "
    "paper title and abstract, return ONLY a strict JSON object with key "
    "'records', whose value is a list of objects. Each object MUST have:\n"
    "  - formula: the chemical formula as written, no LaTeX, ASCII only\n"
    "  - tc_kelvin: numeric critical temperature in Kelvin, or null\n"
    "  - pressure_class: 'ambient' | 'high_pressure' | 'unknown'\n"
    "  - pressure_gpa: numeric pressure in GPa, or null\n"
    "  - evidence_type: 'primary' | 'cited' | 'theoretical' | 'unknown'\n"
    "Only include materials whose superconducting properties are discussed "
    "in this abstract. If no superconductor is reported, return an empty "
    "records list. Do not include any prose -- JSON only."
)


@dataclass
class ComparisonRow:
    paper_id: str
    paper_year: int | None
    paper_title: str
    claude_formula: str
    claude_tc: float | None
    claude_pressure_class: str
    claude_pressure_gpa: float | None
    claude_evidence_type: str
    sclib_formula: str | None
    sclib_tc: float | None
    sclib_pressure_class: str
    sclib_pressure_gpa: float | None
    sclib_evidence_type: str | None
    formula_similarity: float
    formula_match: bool
    tc_delta: float | None
    tc_match: bool
    pressure_class_match: bool
    notes: str = ""


def fetch_json(session: requests.Session, path: str, params: dict[str, Any] | None = None) -> dict | None:
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
    """Sample paper IDs from the timeline snapshot (papers with abstracts)."""
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


def classify_pressure(value: float | None, conditions: str | None = None) -> str:
    """Crude SCLib pressure-class derivation, matching milestone validator."""
    if value is not None:
        try:
            v = float(value)
        except (TypeError, ValueError):
            v = None
        else:
            if v <= 0.05:
                return "ambient"
            return "high_pressure"
    if conditions:
        lowered = conditions.lower()
        if "ambient" in lowered:
            return "ambient"
        if re.search(r"P\s*=\s*[0-9]", conditions, re.IGNORECASE):
            return "high_pressure"
    return "unknown"


def formula_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def best_sclib_match(claude_formula: str, sclib_records: list[dict]) -> tuple[dict | None, float]:
    best = None
    best_sim = 0.0
    for rec in sclib_records:
        sim = formula_similarity(claude_formula, rec.get("formula") or "")
        if sim > best_sim:
            best_sim = sim
            best = rec
    return best, best_sim


def call_claude(client: Any, title: str, abstract: str) -> tuple[list[dict], str]:
    """Return (records, raw_text). On parse failure, records is empty."""
    user_content = f"Title: {title}\n\nAbstract: {abstract}\n\nReturn JSON."
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=CLAUDE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    text = "".join(b.text for b in msg.content if hasattr(b, "text"))
    # Strip optional ```json fences then parse.
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?", "", candidate).strip()
        if candidate.endswith("```"):
            candidate = candidate[:-3].strip()
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", candidate, re.DOTALL)
        if not match:
            return [], text
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return [], text
    records = parsed.get("records") if isinstance(parsed, dict) else None
    if not isinstance(records, list):
        return [], text
    return records, text


def write_skip_summary(reason: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "skipped",
        "reason": reason,
        "sample_size_target": SAMPLE_SIZE,
        "model": CLAUDE_MODEL,
        "tc_tolerance_K": TC_TOLERANCE_K,
        "formula_similarity_threshold": FORMULA_SIM_THRESHOLD,
        "note": "Re-run validation/dual_llm_consistency.py with a valid ANTHROPIC_API_KEY to populate the consistency tables.",
    }
    out = OUTPUT_DIR / "dual_llm_consistency_summary.json"
    out.write_text(json.dumps(payload, indent=2))
    print(f"Skip recorded: {reason}\nWrote {out}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    key = os.environ.get(ANTHROPIC_KEY_ENV, "")
    if not key:
        write_skip_summary("ANTHROPIC_API_KEY not set in environment.")
        return
    try:
        from anthropic import Anthropic, AuthenticationError
    except ImportError as exc:
        write_skip_summary(f"anthropic SDK not importable: {exc}")
        return

    client = Anthropic(api_key=key)
    # Probe credentials with a tiny call so we fail fast.
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
        sclib_records = paper.get("materials_extracted") or []
        if not sclib_records:
            skipped_papers.append({"paper_id": paper_id, "reason": "no SCLib records"})
            continue
        title = paper.get("title") or ""
        abstract = paper.get("abstract") or ""

        try:
            claude_records, _raw = call_claude(client, title, abstract)
        except AuthenticationError as exc:
            write_skip_summary(f"AuthenticationError during run: {exc}")
            return
        except Exception as exc:
            skipped_papers.append({"paper_id": paper_id, "reason": f"claude call failed: {exc}"})
            continue
        if not claude_records:
            skipped_papers.append({"paper_id": paper_id, "reason": "claude returned no records"})
            continue

        accepted_papers += 1
        sclib_extracted_total += len(sclib_records)
        claude_extracted_total += len(claude_records)

        for cr in claude_records:
            if not isinstance(cr, dict):
                continue
            claude_formula = (cr.get("formula") or "").strip()
            claude_tc = cr.get("tc_kelvin")
            claude_p_class = (cr.get("pressure_class") or "unknown").strip().lower()
            claude_p_gpa = cr.get("pressure_gpa")
            claude_ev = (cr.get("evidence_type") or "unknown").strip().lower()

            match, sim = best_sclib_match(claude_formula, sclib_records)
            sclib_formula = match.get("formula") if match else None
            sclib_tc = match.get("tc_kelvin") if match else None
            sclib_p_gpa = match.get("pressure_gpa") if match else None
            sclib_p_class = classify_pressure(sclib_p_gpa) if match else "unknown"
            sclib_ev = match.get("evidence_type") if match else None

            try:
                claude_tc_num = float(claude_tc) if claude_tc is not None else None
            except (TypeError, ValueError):
                claude_tc_num = None
            try:
                sclib_tc_num = float(sclib_tc) if sclib_tc is not None else None
            except (TypeError, ValueError):
                sclib_tc_num = None
            try:
                claude_p_num = float(claude_p_gpa) if claude_p_gpa is not None else None
            except (TypeError, ValueError):
                claude_p_num = None
            try:
                sclib_p_num = float(sclib_p_gpa) if sclib_p_gpa is not None else None
            except (TypeError, ValueError):
                sclib_p_num = None

            tc_delta = None
            tc_match = False
            if claude_tc_num is not None and sclib_tc_num is not None:
                tc_delta = sclib_tc_num - claude_tc_num
                tc_match = abs(tc_delta) <= TC_TOLERANCE_K
            elif claude_tc_num is None and sclib_tc_num is None:
                tc_match = True  # both silent

            formula_match = sim >= FORMULA_SIM_THRESHOLD
            if claude_p_class not in ("ambient", "high_pressure", "unknown"):
                claude_p_class = "unknown"
            pressure_class_match = claude_p_class == sclib_p_class

            notes = []
            if match is None:
                notes.append("no SCLib match available")
            elif not formula_match:
                notes.append(f"formula similarity {sim:.2f} below threshold")
            if not tc_match and not (claude_tc_num is None and sclib_tc_num is None):
                notes.append("tc disagreement")
            if not pressure_class_match:
                notes.append("pressure class disagreement")

            rows.append(ComparisonRow(
                paper_id=paper_id,
                paper_year=paper.get("date_submitted", "")[:4].isdigit() and int(paper["date_submitted"][:4]) or None,
                paper_title=title,
                claude_formula=claude_formula,
                claude_tc=claude_tc_num,
                claude_pressure_class=claude_p_class,
                claude_pressure_gpa=claude_p_num,
                claude_evidence_type=claude_ev,
                sclib_formula=sclib_formula,
                sclib_tc=sclib_tc_num,
                sclib_pressure_class=sclib_p_class,
                sclib_pressure_gpa=sclib_p_num,
                sclib_evidence_type=sclib_ev,
                formula_similarity=round(sim, 4),
                formula_match=formula_match,
                tc_delta=round(tc_delta, 3) if tc_delta is not None else None,
                tc_match=tc_match,
                pressure_class_match=pressure_class_match,
                notes="; ".join(notes),
            ))

        if accepted_papers % 10 == 0:
            print(f"  processed {accepted_papers}/{SAMPLE_SIZE} papers", flush=True)

    csv_path = OUTPUT_DIR / "dual_llm_consistency_records.csv"
    if rows:
        fieldnames = list(asdict(rows[0]).keys())
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(asdict(r))

    total_rows = len(rows)
    fully_consistent = [
        r for r in rows
        if r.formula_match and r.tc_match and r.pressure_class_match
    ]
    low_conf = [
        asdict(r) for r in rows
        if not (r.formula_match and r.tc_match and r.pressure_class_match)
    ][:50]

    formula_match_rate = (sum(1 for r in rows if r.formula_match) / total_rows) if total_rows else None
    tc_match_rate = (sum(1 for r in rows if r.tc_match) / total_rows) if total_rows else None
    pressure_match_rate = (sum(1 for r in rows if r.pressure_class_match) / total_rows) if total_rows else None
    overall_rate = (len(fully_consistent) / total_rows) if total_rows else None

    summary = {
        "status": "ok",
        "model": CLAUDE_MODEL,
        "papers_target": SAMPLE_SIZE,
        "papers_with_pairings": accepted_papers,
        "papers_skipped": len(skipped_papers),
        "papers_skipped_reasons_head": skipped_papers[:20],
        "claude_records_total": claude_extracted_total,
        "sclib_records_total": sclib_extracted_total,
        "row_count": total_rows,
        "tc_tolerance_K": TC_TOLERANCE_K,
        "formula_similarity_threshold": FORMULA_SIM_THRESHOLD,
        "match_rates": {
            "formula_match": round(formula_match_rate, 4) if formula_match_rate is not None else None,
            "tc_within_tolerance": round(tc_match_rate, 4) if tc_match_rate is not None else None,
            "pressure_class": round(pressure_match_rate, 4) if pressure_match_rate is not None else None,
            "all_three_axes": round(overall_rate, 4) if overall_rate is not None else None,
        },
        "low_confidence_records_head": low_conf,
    }

    out = OUTPUT_DIR / "dual_llm_consistency_summary.json"
    out.write_text(json.dumps(summary, indent=2))
    print()
    print(f"Papers paired: {accepted_papers}")
    print(f"Records compared: {total_rows}")
    print(f"  formula match    : {formula_match_rate}")
    print(f"  tc match (+-10K) : {tc_match_rate}")
    print(f"  pressure class   : {pressure_match_rate}")
    print(f"  all three axes   : {overall_rate}")
    print(f"Wrote {csv_path}")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
