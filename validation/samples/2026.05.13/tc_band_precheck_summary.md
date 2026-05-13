# Tc-Band Validation Precheck

- Review date: 2026-05-13
- Target strata: tc_50_80_gap, tc_80_100_plateau
- Target rows: 300
- Newly updated rows: 298
- Reviewed target rows after this pass: 300

## Field-Level Metrics by Stratum

| Stratum | Field | Reviewed n | Valid n | Accuracy |
|---|---|---:|---:|---:|
| tc_50_80_gap | formula_valid | 150 | 150 | 100.0% |
| tc_50_80_gap | family_valid | 150 | 143 | 95.3% |
| tc_50_80_gap | tc_valid | 150 | 147 | 98.0% |
| tc_50_80_gap | pressure_valid | 150 | 150 | 100.0% |
| tc_50_80_gap | pressure_role_valid | 150 | 144 | 96.0% |
| tc_50_80_gap | ambient_valid | 69 | 68 | 98.6% |
| tc_50_80_gap | evidence_type_valid | 150 | 95 | 63.3% |
| tc_50_80_gap | is_theoretical_valid | 150 | 142 | 94.7% |
| tc_80_100_plateau | formula_valid | 150 | 150 | 100.0% |
| tc_80_100_plateau | family_valid | 150 | 143 | 95.3% |
| tc_80_100_plateau | tc_valid | 150 | 147 | 98.0% |
| tc_80_100_plateau | pressure_valid | 150 | 150 | 100.0% |
| tc_80_100_plateau | pressure_role_valid | 150 | 149 | 99.3% |
| tc_80_100_plateau | ambient_valid | 90 | 90 | 100.0% |
| tc_80_100_plateau | evidence_type_valid | 150 | 65 | 43.3% |
| tc_80_100_plateau | is_theoretical_valid | 150 | 134 | 89.3% |

## Initial Findings

- Rows currently marked for exclusion among reviewed target rows: 11.
- Rows left pending rather than excluded because evidence is unresolved at API/abstract level: 131.
- Theory/experiment mismatches among target rows: 24.
- Non-primary or unresolved evidence rows among target rows: 140.
- Tc mismatches among target rows: 6.
- These are preliminary API/abstract-level checks; review-queue rows should be full-text checked before manuscript-level claims.

Detailed review queue: `tc_band_review_queue.csv`.
