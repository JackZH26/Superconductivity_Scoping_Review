# Validation Sample 2026.05.13

Generated from `/Users/jackzhou/Documents/SuperCononductivity/SCLib/data_freeze/snapshots/2026.05.13` with random seed `20260513`.

Rows in `validation_sample.csv`: 1117

The sample is intentionally stratified and overlapping. If a timeline record
belongs to multiple strata, `sample_strata` lists all matching strata while
`primary_stratum` records the first stratum that selected it.

Fields that are unavailable from the public timeline API, such as paper title,
material id, Tc type, measurement type, and primary/cited evidence, are left
blank or `unknown` for manual validation.

## Preliminary Review Passes

- `tc_ge_150_experimental_all`: 22 rows reviewed in
  `high_tc_experimental_precheck_summary.md`.
- `iron_based_2008`: 100 rows reviewed in
  `iron_based_2008_precheck_summary.md`, with follow-up issues isolated in
  `iron_based_2008_review_queue.csv`.
- `tc_50_80_gap` and `tc_80_100_plateau`: 300 rows reviewed in
  `tc_band_precheck_summary.md`, with unresolved evidence and other issues
  isolated in `tc_band_review_queue.csv`.

Run `python3 validation/score_validation.py
validation/samples/2026.05.13/validation_sample.csv` from the project root to
refresh `validation_metrics.csv` and `validation_stratum_metrics.csv`.
