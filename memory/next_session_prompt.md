---
note: 将此文件内容直接粘贴到新 session 作为初始 prompt，然后删除本文件。
---

# Next Session Prompt: Phase 4 Sensitivity Follow-up

Read `CLAUDE.md`, `memory/pipeline_status.csv`, and `memory/workflow_plan.md` first.

## Current status

- Phase 4 uncertainty upgrade is complete.
- Canonical spectral table: `output/products/spectral/spectral_summary.csv`.
- M500 reference table: `configs/m500_reference.csv`.
- Main scaling sample: 18 included, 5 excluded.
- Excluded clusters: Abell_0697, Abell_0750, MS2137-2353, RXJ1347.5-1145, ZwCl_0857.9+2107.
- `good_only` sample exists and currently has 11 clusters.
- Formal scripts:
  - `src/03_scaling/build_spectral_summary.py`
  - `src/03_scaling/fit_scaling_relations.py`
  - `src/03_scaling/backfill_lx_uncertainties.py`
  - `src/02_spectral/fit_spectral_xrb.py` now writes native Sherpa `sample_energy_flux` intervals on future reruns.

## Key outputs

- `output/products/scaling/scaling_linmix_fixed_evolution_comparison_summary.csv`
- `output/products/scaling/scaling_linmix_fixed_evolution_exclude_bad_report.md`
- `output/products/scaling/scaling_linmix_fixed_evolution_good_only_report.md`
- `output/products/scaling/scaling_quality_classification.csv`
- `output/figures/scaling/lx_m500_linmix_exclude_bad.png`
- `output/figures/scaling/tx_m500_linmix_exclude_bad.png`
- `output/figures/scaling/m500_tx_literature_style_exclude_bad.png`
- `output/figures/scaling/lx_m500_linmix_good_only.png`
- `output/figures/scaling/tx_m500_linmix_good_only.png`

Main exclude_bad results:
- Lx-M500 beta=1.07 -0.47/+0.48, scatter=0.172 dex.
- Tx-M500 beta=0.51 -0.25/+0.28, scatter=0.116 dex.

good_only results:
- Lx-M500 beta=0.51 -0.65/+0.66, scatter=0.225 dex.
- Tx-M500 beta=0.45 -0.18/+0.23, scatter=0.061 dex.

## Important caveats

- Do not use old `output/products/spectral/spectral_twostep_summary.csv` as final input.
- `weiwwqeo_scaling/` is a raw reference, not the formal output location.
- Current Lx uncertainties mostly use `confidence_interval_parameter_fallback` from saved `icm_src.kT` and `icm_src.norm` confidence intervals.
- Missing Lx uncertainties remain explicitly flagged for Abell_0068, MACSJ0647.7+7015, and several excluded bad clusters.
- R500 uncertainties are stored as aperture provenance propagated from M500; they are not independent linmix errors.
- Core-excised scaling remains future work.

## Next priority

1. Rerun selected spectra with native `sample_energy_flux`, especially Abell_0068 and MACSJ0647.7+7015, to replace Lx fallback/missing intervals.
2. Add Lx-Tx fixed-evolution or no-evolution fit to `src/03_scaling/fit_scaling_relations.py`.
3. Add leave-one-out or high/suspect sensitivity tests for Abell_0068, Abell_0611, MACSJ0647.7+7015, MACSJ1206.2-0847.
4. Start planning core-excised spectral extraction/fitting for final literature-style comparison.
