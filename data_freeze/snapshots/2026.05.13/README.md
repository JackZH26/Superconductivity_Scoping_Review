# SCLib Snapshot 2026.05.13

Frozen at: 2026-05-13T10:45:58.690Z

API base: https://api.jzis.org/sclib/v1

Dataset version reported by SCLib: v2026.05.12

## Contents

- `metadata.json`: freeze metadata, counts, and file hashes.
- `stats.json`: SCLib stats endpoint payload.
- `timeline.json`: full public timeline endpoint payload.
- `timeline_experimental_only.json`: timeline endpoint with `experimental_only=true`.
- `timeline_points.csv`: flattened timeline points for notebook analysis.
- `timeline_experimental_only_points.csv`: flattened experimental-only points.
- `materials_default_summary.json/csv`: default public materials list.
- `materials_all_summary.json/csv`: materials list with `include_pending=true&include_skeletons=true`.
- `material_family_counts.csv`: family counts from all material summaries.

This API-level snapshot is sufficient for the first timeline-landscape analysis.
For the final manuscript, export a database-level snapshot of papers, material
details, and raw `materials.records` to support full validation and provenance.
