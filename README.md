# Superconductivity Scoping Review

This repository contains the working materials for a 1996--2026 scoping review
of superconducting-materials research based on SCLib, a provenance-traced
database built from more than 40,000 arXiv superconductivity papers.

## Current Snapshot

- Data freeze date: `2026.05.13`
- Complete-year analysis window: 1996--2025
- Public timeline points in complete-year analysis: 13,724
- Main manuscript draft:
  `manuscript/Zhou_Thirty_Years_Of_Superconducting_Materials_Research_1996_2026_A_Scoping_Review_Based_On_A_Provenance_Traced_LLM_Curated_ArXiv_Materials_Database_2026.tex`
- Compiled manuscript PDF is included in `manuscript/`.

## Repository Layout

- `data_freeze/`: scripts and frozen SCLib API snapshot used for analysis.
- `notebooks/`: first timeline-landscape notebook and batch runner.
- `analysis_outputs/`: generated tables and figures from the frozen snapshot.
- `review_protocol/`: research protocol, validation schema, figure plan, and
  preliminary metrics.
- `validation/`: stratified validation sample, scoring scripts, precheck
  scripts, and validation summaries.
- `manuscript/`: LaTeX manuscript skeleton, bibliography, figures, and compiled
  PDF.

## Validation Status

The current validation table contains 420 reviewed rows across high-priority
strata:

- `tc_ge_150_experimental_all`: high-Tc experimental hydride frontier.
- `iron_based_2008`: 2008 iron-based burst sample.
- `tc_50_80_gap`: sampled records from the 50--80 K sparse band.
- `tc_80_100_plateau`: sampled records from the 80--100 K cuprate-dominated
  plateau.

Pressure role is tracked separately from pressure value so that measurement
pressure, high-pressure synthesis, calculations, and cited/contextual pressure
mentions can be separated.

## Reproduce The Current Outputs

From the repository root:

```bash
python3 notebooks/run_timeline_landscape.py
python3 validation/apply_high_tc_experimental_precheck.py
python3 validation/apply_iron_based_2008_precheck.py
python3 validation/apply_tc_band_precheck.py
python3 validation/score_validation.py validation/samples/2026.05.13/validation_sample.csv
```

Compile the manuscript from `manuscript/`:

```bash
pdflatex Zhou_Thirty_Years_Of_Superconducting_Materials_Research_1996_2026_A_Scoping_Review_Based_On_A_Provenance_Traced_LLM_Curated_ArXiv_Materials_Database_2026.tex
bibtex Zhou_Thirty_Years_Of_Superconducting_Materials_Research_1996_2026_A_Scoping_Review_Based_On_A_Provenance_Traced_LLM_Curated_ArXiv_Materials_Database_2026
pdflatex Zhou_Thirty_Years_Of_Superconducting_Materials_Research_1996_2026_A_Scoping_Review_Based_On_A_Provenance_Traced_LLM_Curated_ArXiv_Materials_Database_2026.tex
pdflatex Zhou_Thirty_Years_Of_Superconducting_Materials_Research_1996_2026_A_Scoping_Review_Based_On_A_Provenance_Traced_LLM_Curated_ArXiv_Materials_Database_2026.tex
```

## Notes

LaTeX build byproducts, local OS files, virtual environments, and local secrets
are intentionally excluded by `.gitignore`. Frozen data, validation cache JSON,
analysis outputs, and the compiled manuscript PDF are retained for transparency
and reproducibility.
