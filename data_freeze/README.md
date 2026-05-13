# Data Freeze Workflow

This directory contains reproducible SCLib snapshot exports for the 1996-2026 superconductivity scoping review.

## Fast API Snapshot

Run:

```bash
node data_freeze/freeze_sclib_snapshot.mjs
```

By default this writes:

```text
data_freeze/snapshots/YYYY.MM.DD/
```

The fast snapshot includes:

- SCLib stats.
- Full public timeline.
- Experimental-only timeline.
- Default public materials summary.
- Materials summary with `include_pending=true&include_skeletons=true`.
- Flattened CSV files for notebooks.

## Optional Material Details

Run:

```bash
node data_freeze/freeze_sclib_snapshot.mjs --details
```

This additionally fetches every material detail page and therefore captures `materials.records`.
It makes many API requests and should be used for the final validation-grade snapshot or replaced by a direct production database export.

## Recommended Final Manuscript Freeze

For the submitted paper, prefer a direct production database export containing:

- `papers_snapshot`
- `materials_snapshot`
- `tc_records_snapshot`
- raw per-paper `materials_extracted`
- audit reports and admin decisions
- code commit hash
- SCLib dataset version

The API snapshot is still useful for early analysis because it exactly matches the public website's conservative data surface.
