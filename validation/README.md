# Validation Workflow

This directory contains stratified manual-validation samples and scoring scripts for the SCLib superconductivity scoping review.

## Generate Sample

```bash
python3 validation/generate_validation_sample.py
```

Current output:

```text
validation/samples/2026.05.13/validation_sample.csv
validation/samples/2026.05.13/validation_sample_summary.csv
```

The sample is intentionally stratified and overlapping. `sample_strata` records every reason a row was selected.

## Manual Review

Open `validation_sample.csv` and fill:

- `formula_valid`
- `family_valid`
- `tc_valid`
- `pressure_valid`
- `pressure_role_valid`
- `ambient_valid`
- `evidence_type_valid`
- `is_theoretical_valid`
- `should_exclude_from_main`
- correction fields where needed
- `source_quote_or_location` with a short section/table/figure pointer

Use `true` / `false` for boolean validation fields.

Two preliminary review helpers have been added for high-priority strata:

```bash
python3 validation/apply_high_tc_experimental_precheck.py
python3 validation/apply_iron_based_2008_precheck.py
python3 validation/apply_tc_band_precheck.py
```

The iron-based script caches SCLib paper endpoint metadata in
`validation/cache/sclib_papers_iron_based_2008.json`, updates the 100-row
`iron_based_2008` stratum, and writes:

```text
validation/samples/2026.05.13/iron_based_2008_precheck_summary.md
validation/samples/2026.05.13/iron_based_2008_review_queue.csv
```

The review queue is the next human-check target. It isolates rows with a
field-level validation failure, a pressure-role ambiguity, or a recommended
exclusion from the main quantitative analysis.

The Tc-band script reviews the sampled `tc_50_80_gap` and
`tc_80_100_plateau` rows without overwriting earlier high-Tc or iron-based
reviews. It writes:

```text
validation/samples/2026.05.13/tc_band_precheck_summary.md
validation/samples/2026.05.13/tc_band_review_queue.csv
```

Pressure role is intentionally separate from pressure value. Use
`measurement` for pressure applied during the superconducting Tc measurement,
`synthesis` for high-pressure preparation conditions, `calculation` for a
computed pressure condition, `cited/contextual` for secondary reports, `none`
when no pressure is part of the extracted record, and `unknown` when the role
cannot be resolved from the available source metadata.

## Score Validation

After manual review:

```bash
python3 validation/score_validation.py validation/samples/2026.05.13/validation_sample.csv
```

Outputs:

```text
validation/samples/2026.05.13/validation_metrics.csv
validation/samples/2026.05.13/validation_stratum_metrics.csv
```

These tables are intended for the manuscript's data-quality section.
