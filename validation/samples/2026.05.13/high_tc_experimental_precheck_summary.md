# High-Tc Experimental Precheck Summary

Snapshot: `2026.05.13`

Date: 2026-05-13

Reviewer label in CSV: `Codex preliminary`

Scope:

- Stratum: `tc_ge_150_experimental_all`
- Rows reviewed: 22
- Source basis: SCLib paper endpoint, SCLib extracted material records where available, and arXiv abstract metadata.
- Status: preliminary. Final manuscript validation still requires human full-text verification for all retained headline records.

## Metrics

| Field | Reviewed | Valid | Accuracy |
|---|---:|---:|---:|
| Formula | 22 | 21 | 95.5% |
| Family | 22 | 21 | 95.5% |
| Tc | 22 | 21 | 95.5% |
| Pressure | 22 | 17 | 77.3% |
| Pressure role | 22 | 16 | 72.7% |
| Ambient status | 22 | 22 | 100.0% |
| Evidence type | 22 | 20 | 90.9% |
| Theory/experiment flag | 22 | 21 | 95.5% |
| Excluded from main analysis | 22 | 2 | 9.1% |

## Notable Issues

1. Pressure value and pressure role are the weakest fields in this subset. Several retained high-Tc hydride records have missing pressure despite the source clearly being high-pressure, and secondary/contextual records must not be treated as primary pressure-Tc measurements.
2. `arxiv:2010.10434` / `Hx(S,C)y` is a secondary analysis of previously reported carbonaceous sulfur hydride data, not a primary synthesis/measurement record. It is marked `should_exclude_from_main=true`.
3. `arxiv:2408.13419` / `LaH10` is an NMR/hydrogen-diffusion study rather than a primary superconducting Tc measurement. It is marked `should_exclude_from_main=true`.
4. `Fm3̄m-La0.5Ce0.5H10` contains a phase prefix in the formula field. Corrected formula: `La0.5Ce0.5H10`.
5. `H3S` at 203 K from `arxiv:1506.08190` has valid Tc/family/formula, but the extracted pressure `90 GPa` is likely not the exact pressure for the 203 K transition and is marked pressure-invalid pending full-text check.

## Interpretation For Manuscript

The high-Tc experimental frontier in the current public SCLib snapshot is overwhelmingly a high-pressure hydride regime. The preliminary check supports retaining most records as genuine high-pressure experimental superconductivity reports, but pressure values require stricter validation before drawing pressure-Tc envelopes or comparing hydrides to ambient cuprates.
