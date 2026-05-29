# Full-R500 vs Core-Excised Scaling Comparison

Date: 2026-05-29

## Main Sample

Both comparisons use the same 18-cluster `exclude_bad` sample. Excluded clusters are Abell_0697, Abell_0750, MS2137-2353, RXJ1347.5-1145, and ZwCl_0857.9+2107.

| Relation | Full-R500 beta | Full scatter dex | Core-excised beta | Core scatter dex | Interpretation |
|---|---:|---:|---:|---:|---|
| Lx-M500 | 1.08 -0.49/+0.53 | 0.169 | 1.16 -0.49/+0.53 | 0.192 | Slopes agree well; core-excised Lx-M500 is marginally steeper with slightly larger scatter. |
| Tx-M500 | 0.48 -0.25/+0.26 | 0.117 | 0.56 -0.31/+0.30 | 0.134 | Slopes agree and remain consistent with self-similar within current uncertainty. |
| Lx-Tx | 0.76 -0.41/+0.43 | 0.227 | 0.90 -0.43/+0.46 | 0.230 | Lx-Tx remains the noisiest relation and is shallow relative to common literature values. |

## Good-Only Sensitivity

Full-R500 good-only has 11 clusters; core-excised good-only has 6 clusters. The core-excised good-only posteriors are therefore very broad and should be treated as a quality-sensitivity check, not as a primary result.

| Relation | Full-R500 good-only beta | Core-excised good-only beta |
|---|---:|---:|
| Lx-M500 | 0.55 -0.68/+0.68 | 2.58 -5.47/+8.48 |
| Tx-M500 | 0.44 -0.17/+0.20 | 0.55 -2.54/+2.38 |
| Lx-Tx | 1.23 -0.96/+0.85 | 2.68 -1.60/+1.53 |

## Reporting Interpretation

The main conclusion is stable to core excision: the mass-based slopes change by much less than the current statistical errors. Core excision does not reduce the Lx-M500 scatter in this sample; this likely reflects the small heterogeneous CLASH+LoCuSS sample, residual high-temperature systems, and remaining background/aperture sensitivity. The pulled 2026-05-29 server update backfilled native Sherpa `conf()` Tx intervals for all 18 included core-excised clusters, so the earlier 10% Tx fallback no longer applies to the headline core-excised comparison.

Use full-R500 as the canonical baseline. Use the core-excised branch as the formal literature-style comparison, with the aperture explicitly labeled as `0.15-1.0 R500`.
