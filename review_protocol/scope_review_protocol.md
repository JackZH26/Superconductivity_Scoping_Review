# SCLib 1996-2026 Superconductivity Scoping Review Protocol

Author: Jian Zhou, Principal Investigator, JZ Institute of Science, Hong Kong, China. Email: jack@jzis.org. ORCID: 0009-0000-3536-9500.

Protocol date: 2026-05-13

Working title:

**Thirty Years of Superconducting Materials Research, 1996-2026: A Scoping Review Based on a Provenance-Traced LLM-Curated arXiv Materials Database**

Primary dataset for protocol drafting: SCLib data snapshot visible on 2026-05-13, dataset version `v2026.05.12`.

Primary public sources:

- SCLib timeline: https://jzis.org/sclib/timeline
- SCLib materials: https://jzis.org/sclib/materials
- SCLib stats/API: https://api.jzis.org/sclib/v1/stats
- SCLib source code: https://github.com/JackZH26/SCLib_JZIS

## 1. Central Thesis

This review will use the SCLib timeline not only as a visualization, but as a quantitative map of the superconductivity literature. The main thesis is:

> From 1996 to 2026, superconducting materials research did not evolve as a smooth monotonic rise in critical temperature. Instead, it formed a stratified landscape: a dense low-Tc region below 50 K, a sparse 50-80 K middle-high-temperature gap, an 80-100 K cuprate plateau, and a 150 K+ high-pressure hydride frontier dominated by theory and pressure-dependent experiments. Family-level burst events, such as MgB2 in 2001, iron-based superconductors in 2008, hydrides after 2015, kagome superconductors in 2021, and nickelates after 2019 and 2023, can be detected quantitatively from the literature-derived materials timeline.

The paper should therefore be framed as a database-driven scoping review plus a methods-aware data paper, not as a conventional narrative review alone.

## 2. Scope And Temporal Boundary

Primary analysis window:

- Main complete-year analysis: 1996-2025.
- Partial-year extension: 2026 through the SCLib snapshot date, reported separately.
- If the article is submitted before 2027, the title or abstract must state "through May 2026" or "1996-2025 with partial 2026 update" to avoid implying a complete 2026 corpus.

Corpus definition:

- Primary source: arXiv `cond-mat.supr-con` papers ingested by SCLib.
- Supplementary provenance: NIMS SuperCon and Materials Project are used only where explicitly tagged and must not be silently merged into arXiv-derived evidence.
- Public-facing SCLib default filters exclude `needs_review=true` entries and skeleton entries. The paper's primary analyses should follow the same conservative default unless a section explicitly examines audit failures.

Current corpus scale from SCLib API, 2026-05-13:

- Papers: 40,057.
- Materials: 14,083 total database rows.
- Chunks: 895,622.
- Default public material rows: about 6,585.
- Timeline points: 13,999 points from 4,949 materials.
- Experimental-only timeline points: 10,928 points from 3,805 materials.

These numbers are protocol anchors only. All manuscript figures must use a frozen exported snapshot.

## 3. Research Questions

RQ1. What is the global Tc landscape of superconducting materials from 1996 to 2026?

RQ2. Is the visually apparent 50-80 K gap a robust signal after de-duplication by material, paper, and family, or is it an artifact of repeated cuprate measurements and sparse non-cuprate high-Tc data?

RQ3. Is the 80-100 K region a general high-temperature superconductivity band, or specifically a cuprate/YBCO-dominated plateau?

RQ4. Which material families show burst-like research emergence, and which papers or discoveries triggered those bursts?

RQ5. How do theoretical/computational records differ from experimentally verified records in Tc, pressure, family distribution, and time lag to validation?

RQ6. What are the limitations and error modes of LLM-curated superconductivity data, especially for high-Tc outliers, pressure, ambient claims, and citation conflation?

## 4. Working Hypotheses

H1. The 50-80 K region is underpopulated relative to both the lower 0-50 K regime and the cuprate-dominated 80-100 K plateau, even after material-level de-duplication.

H2. The 80-100 K band is dominated by cuprates, especially YBCO-family and related oxygen-doped copper oxides. It should not be interpreted as a broad multi-family plateau.

H3. Iron-based superconductivity in 2008 is the strongest family-level burst in the 1996-2026 corpus. It should be detectable by paper count, material count, and timeline-point count.

H4. Hydrides above 150 K occupy a different evidence regime from cuprates: high pressure is essential, and theoretical/computational records dominate the high-Tc frontier.

H5. Kagome superconductors represent a topic/mechanism burst rather than a Tc-record burst: low Tc but high density of topological/CDW/competing-order claims.

H6. Nickelates show a two-stage emergence: low-Tc nickel pnictides/oxypnictides around 2008-2010, then oxide nickelates after 2019, and high-pressure bilayer nickelates after 2023.

## 5. Data Units And Analysis Levels

Three levels must be kept separate throughout the manuscript.

1. Measurement-level records:
   - One point per reported Tc measurement after SCLib flattening and de-duplication.
   - Best for visualizing research density and repeated measurements.
   - Risk: heavily studied materials are overrepresented.

2. Material-year-level records:
   - One point per material, year, rounded Tc, pressure bin, and theory/experiment class.
   - Best for timeline analyses.
   - This approximates the current SCLib timeline endpoint.

3. Material-level records:
   - One row per canonical material formula.
   - Best for claims about material discovery space, family composition, and Tc-band occupancy.
   - Use `tc_max`, `tc_ambient`, `family`, `total_papers`, `needs_review`, and `records`.

Any result about "how many materials" must use material-level or material-year-level data, not raw measurement counts.

## 6. Core Data Fields

Required fields for frozen analysis:

- `paper_id`
- `arxiv_id`
- `title`
- `authors`
- `date_submitted`
- `year`
- `material_id`
- `formula`
- `formula_normalized`
- `family`
- `tc_kelvin`
- `tc_type`
- `pressure_gpa`
- `ambient_sc`
- `measurement`
- `paper_type`
- `is_theoretical`
- `evidence_type`
- `confidence`
- `needs_review`
- `review_reason`
- `is_unconventional`
- `is_topological`
- `is_2d_or_interface`
- `has_competing_order`
- `competing_order`
- `pairing_symmetry`
- `structure_phase`
- `sample_form`
- `substrate`
- `doping_type`
- `doping_level`

Optional fields for mechanism-focused analyses:

- `gap_structure`
- `hc2_tesla`
- `lambda_eph`
- `omega_log_k`
- `rho_exponent`
- `t_cdw_k`
- `t_sdw_k`
- `t_afm_k`
- `mp_id`

## 7. Inclusion And Exclusion Rules

Primary inclusion:

- Years 1996-2025 for complete-year main analysis.
- 2026 included only as a partial-year supplement.
- Materials with `needs_review=false`.
- Records with positive finite `tc_kelvin`.
- Records with valid `year`.
- Records marked primary evidence or with no legacy `evidence_type` when the aggregation already passed audit.

Primary exclusion:

- `needs_review=true` unless in the audit/error analysis chapter.
- `tc_kelvin <= 0` or `tc_kelvin > 250` for public timeline analyses, following SCLib's default timeline sanity gate.
- Records from retracted papers.
- Citation-only records when `evidence_type="cited"`.
- Skeleton materials with no real measurement support.

Sensitivity analyses:

- Re-run key figures with and without 2026.
- Re-run Tc-band figures using experimental-only data.
- Re-run Tc-band figures using material-level `tc_max` instead of measurement-level timeline points.
- Re-run high-Tc hydride figures with theory-only excluded.

## 8. Preliminary Timeline Signals To Test

From the current SCLib timeline endpoint:

| Tc band (K) | Points | Experimental | Theoretical | Unique material-like entries |
|---|---:|---:|---:|---:|
| 0-10 | 6,149 | 5,024 | 1,125 | 2,406 |
| 10-20 | 2,143 | 1,655 | 488 | 961 |
| 20-30 | 1,501 | 1,181 | 320 | 708 |
| 30-40 | 1,231 | 977 | 254 | 580 |
| 40-50 | 540 | 396 | 144 | 305 |
| 50-60 | 359 | 275 | 84 | 176 |
| 60-70 | 286 | 191 | 95 | 141 |
| 70-80 | 272 | 208 | 64 | 140 |
| 80-90 | 560 | 436 | 124 | 211 |
| 90-100 | 561 | 420 | 141 | 157 |
| 100-120 | 154 | 95 | 59 | 82 |
| 120-150 | 98 | 48 | 50 | 59 |
| 150-200 | 78 | 11 | 67 | 38 |
| 200-251 | 67 | 11 | 56 | 23 |

Preliminary interpretation to verify:

- 50-80 K is sparse relative to adjacent regimes.
- 80-100 K is dominated by cuprates.
- 150 K+ is dominated by high-pressure hydrides and theoretical records.
- Repeated measurements of a few canonical compounds create visible horizontal bands.

## 9. Tc-Band Analysis Plan

Define main Tc bands:

- `ultra_low`: 0-10 K.
- `low`: 10-30 K.
- `intermediate`: 30-50 K.
- `gap_candidate`: 50-80 K.
- `cuprate_plateau`: 80-100 K.
- `upper_cuprate`: 100-150 K.
- `hydride_frontier`: 150-250 K.

For each band report:

- Number of timeline points.
- Number of unique materials.
- Number of source papers.
- Family composition.
- Experimental/theoretical ratio.
- Ambient/high-pressure ratio.
- Top 10 materials by repeated records.

Gap quantification:

```text
band_density = count / band_width_K
gap_ratio = density_50_80 / mean(density_30_50, density_80_100)
```

Also compute a material-weighted version:

```text
material_band_density = unique_materials_in_band / band_width_K
material_gap_ratio = material_density_50_80 / mean(material_density_30_50, material_density_80_100)
```

Uncertainty:

- Bootstrap by `paper_id`, not by individual record, to avoid treating repeated records from the same paper as independent.
- Report 95% bootstrap confidence intervals for `gap_ratio` and `material_gap_ratio`.

Statistical test:

- Use a negative-binomial or Poisson regression on band counts with offsets for band width.
- Run sensitivity with material-level data to check that the gap is not only a measurement-density artifact.

## 10. Cuprate Plateau Analysis

Target claim:

The 80-100 K band is a cuprate plateau dominated by YBCO and related copper oxides.

Required analyses:

- Share of `family="cuprate"` among 80-100 K points.
- Share of cuprate among unique materials in 80-100 K.
- Top materials in 80-100 K, with repeated-record counts.
- Re-run after collapsing formula variants to parent families such as YBCO, Bi2212, Hg-based, Tl-based.
- Compare 80-100 K with 50-80 K and 100-150 K.

Preliminary current signal:

- 80-100 K: 1,121 points.
- Cuprate points in 80-100 K: 1,044.
- Top repeated entry: `YBa2Cu3O7-delta`, about 369 timeline points in 80-100 K.

Manuscript framing:

This should be presented as "a plateau of repeated, reproducible cuprate systems" rather than "many unrelated materials around 90 K."

## 11. Family Burst Analysis

For each family `f` and year `y`, compute:

- `C_f,y`: timeline point count.
- `M_f,y`: unique material count.
- `P_f,y`: unique source-paper count.
- `E_f,y`: experimental point count.
- `T_f,y`: theoretical point count.
- `Tcmax_f,y`: maximum Tc in that family-year.

Burst score:

```text
baseline_f,y = mean(C_f,y-1, C_f,y-2, C_f,y-3)
burst_score_f,y = (C_f,y + 1) / (baseline_f,y + 1)
```

Primary burst criterion:

- `C_f,y >= 20`.
- `burst_score_f,y >= 3`.
- `M_f,y >= 3`.
- Not solely caused by one review paper or one multi-material table.

Secondary confirmation:

- Use `P_f,y` and `M_f,y` to confirm that a burst is literature-wide, not only record-heavy.

Preliminary candidate bursts:

| Family | Candidate burst | Preliminary signal | Interpretation |
|---|---:|---|---|
| Cuprate | 1996 | 37 points, 20 materials | Start of the selected arXiv-era corpus, not a true discovery burst |
| MgB2 | 2001-2002 | 2002: 34 points, 25 materials | Discovery-driven burst after MgB2 39 K |
| Iron-based | 2008 | 356 points, 206 materials, 190 papers | Strongest new-family burst |
| Hydride | 2015 onward | H3S/LaH10 high-pressure frontier | Pressure-driven high-Tc frontier |
| Kagome | 2021 | 30 points, 15 papers, 3 materials | Mechanism/topology/CDW burst, not high-Tc burst |
| Nickelate | 2019 and 2023-2026 | Infinite-layer and bilayer high-pressure waves | Oxide-family revival |

Key discovery anchors to verify and cite:

- MgB2: Nagamatsu et al., Nature 2001, "Superconductivity at 39 K in magnesium diboride."
- Iron-based: Kamihara et al., JACS 2008, "Iron-Based Layered Superconductor La[O1-xFx]FeAs ... Tc = 26 K."
- Hydride: Drozdov et al., Nature 2015, "Conventional superconductivity at 203 kelvin at high pressures in the sulfur hydride system."
- Nickelate: Li et al., Nature 2019, "Superconductivity in an infinite-layer nickelate"; Sun et al., Nature 2023, "Signatures of superconductivity near 80 K in a nickelate under high pressure."
- Kagome: AV3Sb5/CsV3Sb5 2020-2021 papers, including `arxiv:2102.08356` and `arxiv:2103.12507` as SCLib-visible early nodes.

## 12. Theory Versus Experiment Analysis

Classify each point into four evidence regimes:

1. Experimental ambient.
2. Experimental high-pressure.
3. Theoretical ambient or unspecified pressure.
4. Theoretical high-pressure.

If pressure is missing, keep it as unknown rather than assuming ambient.

Core plots:

- Yearly maximum Tc envelope for each evidence regime.
- Family composition of theoretical-only records.
- Family composition of experimental-only records.
- Pressure vs Tc scatter for hydrides and nickelates.
- Prediction-to-validation lag distribution.

Lag definition:

For each canonical material:

```text
first_theory_year = earliest year with is_theoretical=true
first_experimental_year = earliest year with is_theoretical=false
lag = first_experimental_year - first_theory_year
```

Use only cases where both theory and experiment exist. Manually validate all lag cases with `tc_kelvin >= 100 K` or hydride/nickelate family tags.

Expected interpretation:

- Cuprates: experimental ambient plateau.
- Iron-based: mostly experimental after 2008, with theory following rapidly.
- Hydrides: high theoretical fraction, high-pressure dependence, and a smaller experimental-confirmation subset.
- Nickelates: mixed theory/experiment with rapid growth after key experimental claims.
- Kagome: experiment-heavy low-Tc but mechanism-rich.

## 13. Case Study Modules

Case Study A: Iron-based 2008 burst

- Start with Kamihara JACS 2008 as the canonical discovery anchor.
- Use SCLib arXiv nodes such as `arxiv:0803.0128`, `arxiv:0804.2105`, `arxiv:0804.2582`, `arxiv:0804.3727`, and `arxiv:0804.4290` to show rapid propagation from LaFeAsO to rare-earth FeAsO systems above 50 K.
- Quantify monthly acceleration within 2008.

Case Study B: 50-80 K gap

- Compare families that approach but rarely fill this band: iron-based high end, FeSe/interface/pressure, nickelates, selected cuprates.
- Distinguish "few independent materials" from "many repeated records."
- Discuss whether the band marks a mechanistic bottleneck between non-cuprate systems and cuprate-like high-Tc physics.

Case Study C: Hydride frontier

- Separate high-pressure experimental records from theoretical predictions.
- Report pressure distributions together with Tc.
- Treat room-temperature or near-room-temperature claims as audit-sensitive, not ordinary data points.

Case Study D: Nickelate revival

- Split nickelates into early low-Tc nickel pnictide/oxypnictide records and later oxide nickelates.
- Treat 2019 infinite-layer and 2023 bilayer high-pressure nickelates as separate waves.

Case Study E: Kagome mechanism burst

- Show that kagome burst is not a high-Tc story.
- Emphasize CDW, topology, competing orders, pressure domes, and gap symmetry.

## 14. Validation Plan

Validation must be performed before any strong scientific claim.

Manual review fields:

- Formula correctness.
- Material family.
- Tc value and units.
- Pressure value and units.
- Ambient vs high pressure.
- Experimental vs theoretical.
- Primary measurement vs cited prior work.
- Paper year.
- Retraction/dispute status.

Minimum validation sample:

- Random timeline records: 300.
- Tc 50-80 K gap records: 150.
- Tc 80-100 K plateau records: 150.
- Tc >= 150 K records: all experimental records plus 100 theoretical records.
- Iron-based 2008 records: 100.
- Hydride records: 100.
- Nickelate records: 100.
- Kagome records: 50.
- Records with missing family or unusual formula: 100.

Target total: about 1,000 reviewed records.

Metrics:

- Formula precision.
- Family accuracy.
- Tc absolute error and exact-match rate.
- Pressure accuracy.
- Ambient classification precision.
- Theory/experiment classification accuracy.
- Primary/cited evidence accuracy.
- High-risk false-positive rate for `tc_kelvin >= 150 K`.

Acceptance thresholds for manuscript-level claims:

- All headline record-high examples must be manually validated.
- Family burst claims require at least 90% family classification precision in the sampled burst year.
- 50-80 K gap claim must hold in both measurement-level and material-level analyses.
- Theory/experiment comparison must be reported with observed classification accuracy.

## 15. Proposed Manuscript Structure

1. Abstract
2. Introduction
   - Why a database-driven scoping review is needed.
   - Why the timeline reveals a structured Tc landscape.
3. Data And Methods
   - SCLib corpus.
   - LLM extraction and provenance.
   - Aggregation and audit rules.
   - Timeline construction.
   - Validation protocol.
4. The Global Tc Landscape, 1996-2026
   - Tc bands.
   - 50-80 K gap.
   - 80-100 K cuprate plateau.
   - 150 K+ high-pressure frontier.
5. Family Burst Events
   - MgB2.
   - Iron-based 2008.
   - Hydrides.
   - Kagome.
   - Nickelates.
6. Theory Versus Experiment
   - Evidence regimes.
   - Pressure dependence.
   - Prediction-to-validation lag.
7. Mechanistic Synthesis By Tc Regime
   - 0-10 K.
   - 10-50 K.
   - 50-80 K.
   - 80-100 K.
   - 100-150 K.
   - 150 K+.
8. Data Quality, Biases, And Limitations
   - arXiv bias.
   - LLM extraction errors.
   - Repeated-measurement bias.
   - Theory/experiment classification.
   - 2026 partial-year limitation.
9. Outlook
   - Material search gaps.
   - Underfilled Tc regimes.
   - Future database and validation work.
10. Declarations
11. References

## 16. Required Figure Set

Minimum publishable figure set:

1. PRISMA-style SCLib data flow.
2. Global Tc-year scatter with experimental/theoretical and pressure distinctions.
3. Tc density histogram, measurement-level and material-level.
4. Tc-band family composition.
5. Zoomed 50-80 K gap and 80-100 K plateau comparison.
6. Family burst heatmap.
7. Iron-based 2008 monthly burst case study.
8. Theory versus experiment Tc envelope.
9. Pressure-Tc map for hydrides and nickelates.
10. Validation/error-rate summary.

Optional supplementary figures:

- Family-specific Tc quantile plot.
- Top repeated materials by band.
- Prediction-to-validation lag distribution.
- Missingness map for extracted fields.

## 17. Immediate Next Tasks

Task 1. Freeze a reproducible dataset.

- Export `papers_snapshot`, `materials_snapshot`, and flattened `tc_records_snapshot`.
- Record exact timestamp, SCLib dataset version, API commit if available, and code commit hash.

Task 2. Generate the first analysis notebook.

- Build the Tc-band table.
- Build family-year counts.
- Build theory/experiment evidence-regime counts.
- Reproduce all preliminary numbers in this protocol from the frozen snapshot.

Task 3. Start validation.

- Generate stratified random sample according to Section 14.
- Create a manual validation CSV using `validation_schema.csv`.
- Validate all headline outliers before drafting claims.

Task 4. Draft the manuscript skeleton.

- Create LaTeX file using the required author block for Jian Zhou.
- Insert section headings and placeholder figure calls.
- Add Declarations section before References.

## 18. Manuscript Authorship And Declarations

Use this author identity in the eventual manuscript:

```latex
\author{Jian Zhou}
\thanks{Principal Investigator, JZ Institute of Science, Hong Kong, China.
Email: \texttt{jack@jzis.org}.}
```

Required declarations section:

```latex
\section*{Declarations}

\textbf{Funding}: Not applicable.

\textbf{Conflict of interest}: The author declares no conflict of interest.

\textbf{Data availability}: All data and code supporting this work are available 
from the corresponding author upon reasonable request.

\textbf{Ethics approval}: Not applicable.
```

