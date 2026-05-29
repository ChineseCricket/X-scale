# Full-R500 vs Core-Excised Scaling Comparison

Date: 2026-05-29

## Main Sample

Both comparisons use the same 18-cluster `exclude_bad` sample. Excluded clusters are Abell_0697, Abell_0750, MS2137-2353, RXJ1347.5-1145, and ZwCl_0857.9+2107.

| Relation | Full-R500 beta | Full scatter dex | Core-excised beta | Core scatter dex | Interpretation |
|---|---:|---:|---:|---:|---|
| Lx-M500 | 1.08 -0.48/+0.45 | 0.169 | 1.15 -0.51/+0.54 | 0.186 | Slopes agree well; core-excised Lx-M500 is marginally steeper with slightly larger scatter. |
| Tx-M500 | 0.50 -0.27/+0.29 | 0.117 | 0.55 -0.34/+0.36 | 0.157 | Slopes agree and remain consistent with self-similar within current uncertainty. |
| Lx-Tx | 0.77 -0.44/+0.47 | 0.227 | 0.69 -0.41/+0.40 | 0.245 | Lx-Tx remains the noisiest relation and is shallow relative to common literature values. |

## Good-Only Sensitivity

Full-R500 good-only has 11 clusters; core-excised good-only has 6 clusters. The core-excised good-only posteriors are therefore very broad and should be treated as a quality-sensitivity check, not as a primary result.

| Relation | Full-R500 good-only beta | Core-excised good-only beta |
|---|---:|---:|
| Lx-M500 | 0.52 -0.62/+0.64 | 2.29 -5.52/+6.23 |
| Tx-M500 | 0.43 -0.17/+0.20 | 0.54 -3.07/+2.62 |
| Lx-Tx | 1.18 -0.89/+0.84 | 2.53 -1.80/+2.15 |

## Reporting Interpretation

The main conclusion is stable to core excision: the mass-based slopes change by much less than the current statistical errors. Core excision does not reduce the scatter in this sample; this likely reflects the small heterogeneous CLASH+LoCuSS sample, residual high-temperature systems, and the fact that the core-excised branch currently uses 10% Tx fallback uncertainties.

Use full-R500 as the canonical baseline. Use the core-excised branch as the formal literature-style comparison, with the aperture explicitly labeled as `0.15-1.0 R500`.
