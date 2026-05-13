# Iron-Based 2008 Review Queue Resolutions

Snapshot: `2026.05.13`

Reviewer label in CSV: `Codex preliminary`

Status: detailed API/abstract-level review. Final manuscript validation should
still check full text for rows used as named examples.

## Resolution Table

| Validation id | Resolution | Main-analysis action |
|---|---|---|
| VAL-000074 | `Pr[O1-xFx]FeAs` at 42 K appears as a contextual material in a LaO0.9F0.1-deltaFeAs point-contact spectroscopy paper rather than the paper's primary studied material. | Exclude |
| VAL-000093 | NdFeAsO0.85 at 45.5 K is an experimental point-contact Andreev-reflection spectroscopy record; the theory flag is wrong, but the material/Tc evidence is retained. | Retain |
| VAL-000095 | DyFeAs(O,F) at 45 K is valid, but 10--12 GPa is a synthesis condition, not a Tc measurement pressure. | Retain; pressure role corrected to `synthesis` |
| VAL-000096 | TbFeAs(O,F) at 46 K is valid, but 10--12 GPa is a synthesis condition, not a Tc measurement pressure. | Retain; pressure role corrected to `synthesis` |
| VAL-000105 | LaFeAsO0.9F0.1 at 23.7 K is an experimental microwave/transport record; the theory flag is wrong. | Retain |
| VAL-000107 | `Ba0.5K0.5OFe2As2` contains an extra oxygen in the formula relative to the Ba1-xKxFe2As2 source chemistry. | Retain with formula correction to `Ba0.5K0.5Fe2As2` |
| VAL-000116 | LaOFeAs at 28.5 K is an experimental synthesis/upper-critical-field record; the theory flag is wrong. | Retain |
| VAL-000122 | The 0.5 K value in the phonon-density-of-states paper is not a superconducting Tc. The supported superconducting values are around 23--27 K. | Exclude |
| VAL-000125 | (Ba0.6K0.4)Fe2As2 at 38 K is an experimental crystal-structure/superconductivity record; the theory flag is wrong. | Retain |
| VAL-000126 | (Ba0.9K0.1)Fe2As2 at 3 K is an experimental composition-series record; the theory flag is wrong. | Retain |
| VAL-000159 | SmFeAsO0.8F0.2 at 53 K is an experimental point-contact Andreev-reflection spectroscopy record; the theory flag is wrong. | Retain |
| VAL-000165 | CeO0.9F0.1FeAs at 38.4 K is an experimental synthesis/upper-critical-field record; the theory flag is wrong. | Retain |
| VAL-000502 | LaFeAsO:F at 26 K is an experimental photoemission record; the theory flag is wrong. | Retain |

## Manuscript Implications

- The iron-based 2008 burst remains robust after queue review: only 2 of 100
  sampled rows are currently excluded.
- The dominant issue is not formula or Tc extraction; it is source-type
  classification. Experimental spectroscopy and transport papers are sometimes
  tagged as theoretical.
- Pressure role needs to be explicit. High-pressure synthesis is scientifically
  important, but it should not be plotted as a high-pressure Tc measurement.
