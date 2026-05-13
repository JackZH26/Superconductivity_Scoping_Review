"""Build the SCLib data-quality funnel for the scoping review.

The funnel traces how a corpus-level paper count narrows to the slimmer counts
that drive the analytical figures, so reviewers can see the attrition path.

Funnel steps:
    1. total_papers                       -- /v1/stats
    2. total_materials_records            -- /v1/stats
    3. all_materials_incl_pending         -- /v1/materials?include_pending=true&include_skeletons=true&limit=1
    4. public_materials_default           -- /v1/materials?limit=1  (curator-approved, non-skeleton)
    5. public_timeline_points_all         -- /v1/timeline (coverage.total_points)
    6. public_timeline_materials_all      -- /v1/timeline (coverage.total_materials)
    7. experimental_only_timeline_points  -- /v1/timeline?experimental_only=true
    8. experimental_only_timeline_materials
    9. complete_year_window_points        -- experimental-only points restricted to 1996-2025

Outputs:
    analysis_outputs/2026.05.13/data_funnel.json
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests


API_BASE = "https://api.jzis.org/v1"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "analysis_outputs/2026.05.13"
USER_AGENT = "SCLib-scoping-review-data-funnel/0.1"
COMPLETE_YEAR_MIN = 1996
COMPLETE_YEAR_MAX = 2025


def fetch_json(session: requests.Session, path: str, params: dict[str, Any] | None = None) -> dict:
    url = f"{API_BASE}{path}"
    for attempt in range(4):
        resp = session.get(url, params=params, timeout=30,
                           headers={"User-Agent": USER_AGENT})
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in (429,) or resp.status_code >= 500:
            time.sleep(2.0 * (attempt + 1))
            continue
        resp.raise_for_status()
    raise RuntimeError(f"failed to fetch {url}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    stats = fetch_json(session, "/stats")
    materials_default = fetch_json(session, "/materials", params={"limit": 1})
    materials_all = fetch_json(
        session, "/materials",
        params={"limit": 1, "include_pending": "true", "include_skeletons": "true"},
    )
    timeline = fetch_json(session, "/timeline")
    timeline_exp = fetch_json(session, "/timeline", params={"experimental_only": "true"})

    timeline_exp_points = timeline_exp.get("points", []) or []
    complete_year_points = [
        p for p in timeline_exp_points
        if isinstance(p.get("year"), int) and COMPLETE_YEAR_MIN <= p["year"] <= COMPLETE_YEAR_MAX
    ]
    complete_year_materials = {
        p.get("material") for p in complete_year_points if p.get("material")
    }

    papers_by_year = stats.get("papers_by_year") or {}
    complete_year_papers = sum(
        int(c) for y, c in papers_by_year.items()
        if y.isdigit() and COMPLETE_YEAR_MIN <= int(y) <= COMPLETE_YEAR_MAX
    )

    total_papers = int(stats.get("total_papers") or 0)
    materials_records = int(stats.get("total_materials") or 0)
    public_default = int(materials_default.get("total") or 0)
    public_all = int(materials_all.get("total") or 0)
    timeline_points_all = int((timeline.get("coverage") or {}).get("total_points") or 0)
    timeline_materials_all = int((timeline.get("coverage") or {}).get("total_materials") or 0)
    timeline_exp_points_total = int((timeline_exp.get("coverage") or {}).get("total_points") or 0)
    timeline_exp_materials = int((timeline_exp.get("coverage") or {}).get("total_materials") or 0)

    steps = [
        {
            "step": 1,
            "name": "total_papers_ingested",
            "value": total_papers,
            "source": "/v1/stats total_papers",
            "description": "All arXiv superconductivity papers ingested by SCLib (1993-2026).",
        },
        {
            "step": 2,
            "name": "complete_year_window_papers_1996_2025",
            "value": complete_year_papers,
            "source": "/v1/stats papers_by_year filtered to 1996-2025",
            "description": "Papers in the complete-year analysis window used by the manuscript.",
        },
        {
            "step": 3,
            "name": "raw_material_records",
            "value": materials_records,
            "source": "/v1/stats total_materials",
            "description": "Distinct materials.records rows from NER (one per paper x material x condition).",
        },
        {
            "step": 4,
            "name": "materials_incl_pending_and_skeletons",
            "value": public_all,
            "source": "/v1/materials?include_pending=true&include_skeletons=true total",
            "description": "All distinct material entities in SCLib, including unreviewed.",
        },
        {
            "step": 5,
            "name": "materials_default_curated_public",
            "value": public_default,
            "source": "/v1/materials?limit=1 total",
            "description": "Curator-approved, non-skeleton materials (default public list).",
        },
        {
            "step": 6,
            "name": "timeline_points_public_all",
            "value": timeline_points_all,
            "source": "/v1/timeline coverage.total_points",
            "description": "Public timeline points (theoretical + experimental, dedup by SCLib rules).",
        },
        {
            "step": 7,
            "name": "timeline_materials_public_all",
            "value": timeline_materials_all,
            "source": "/v1/timeline coverage.total_materials",
            "description": "Distinct materials represented on the public timeline.",
        },
        {
            "step": 8,
            "name": "timeline_points_experimental_only",
            "value": timeline_exp_points_total,
            "source": "/v1/timeline?experimental_only=true coverage.total_points",
            "description": "Timeline points filtered to experimental evidence.",
        },
        {
            "step": 9,
            "name": "timeline_materials_experimental_only",
            "value": timeline_exp_materials,
            "source": "/v1/timeline?experimental_only=true coverage.total_materials",
            "description": "Distinct materials surviving the experimental-only filter.",
        },
        {
            "step": 10,
            "name": "experimental_points_complete_year_window_1996_2025",
            "value": len(complete_year_points),
            "source": "/v1/timeline?experimental_only=true points filtered to 1996-2025",
            "description": "Final point set entering the manuscript analyses.",
        },
        {
            "step": 11,
            "name": "experimental_materials_complete_year_window_1996_2025",
            "value": len(complete_year_materials),
            "source": "derived: distinct materials in step 10",
            "description": "Distinct materials behind the final point set.",
        },
    ]

    retention_pairs = [
        (1, 3, "raw_material_records vs total_papers"),
        (3, 4, "all_materials vs raw_records"),
        (4, 5, "curated_public vs all_materials"),
        (6, 8, "experimental_points vs all_timeline_points"),
        (8, 10, "complete_year_window vs experimental_points"),
        (1, 10, "final_points vs total_papers"),
    ]
    retention = []
    for src_step, dst_step, label in retention_pairs:
        src = steps[src_step - 1]["value"]
        dst = steps[dst_step - 1]["value"]
        retention.append({
            "label": label,
            "from_step": src_step,
            "to_step": dst_step,
            "from_value": src,
            "to_value": dst,
            "ratio_to_from": round(dst / src, 4) if src else None,
        })

    payload = {
        "snapshot_id": "2026.05.13",
        "api_base": API_BASE,
        "dataset_version_reported": stats.get("dataset_version"),
        "last_ingest_at": stats.get("last_ingest_at"),
        "complete_year_window": [COMPLETE_YEAR_MIN, COMPLETE_YEAR_MAX],
        "steps": steps,
        "retention_ratios": retention,
        "raw": {
            "stats_total_papers": total_papers,
            "stats_total_materials": materials_records,
            "stats_total_chunks": int(stats.get("total_chunks") or 0),
            "papers_by_year": {y: int(c) for y, c in papers_by_year.items()},
            "timeline_coverage": timeline.get("coverage"),
            "timeline_experimental_coverage": timeline_exp.get("coverage"),
            "materials_default_total": public_default,
            "materials_all_total": public_all,
        },
    }

    out_path = OUTPUT_DIR / "data_funnel.json"
    out_path.write_text(json.dumps(payload, indent=2))

    print("Data funnel:")
    for s in steps:
        print(f"  {s['step']:>2}. {s['name']:55s} = {s['value']:>10,}")
    print()
    print("Key retention ratios:")
    for r in retention:
        ratio = "n/a" if r["ratio_to_from"] is None else f"{r['ratio_to_from']:.4f}"
        print(f"  step {r['from_step']:>2} -> {r['to_step']:>2}  {r['label']:50s}  {r['from_value']:>10,} -> {r['to_value']:>10,}  ({ratio})")
    print()
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
