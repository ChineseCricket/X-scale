---
note: 将此文件内容直接粘贴到新 session 作为初始 prompt，然后删除本文件。
---

# Next Session Prompt: Phase 4 Spectral-Uncertainty/Core-Excised Follow-up

Read `CLAUDE.md`, `memory/pipeline_status.csv`, and `memory/workflow_plan.md` first.

## Current status

- Phase 4 uncertainty + Lx-Tx + leave-one-out sensitivity upgrade is complete.
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
- Spectral fit QA figures in `output/figures/spectral/*_fit.png` are now three-panel background-aware displays: raw source vs blank-sky/background, net source data vs folded total/component source models, and `(net-total)/sigma` residuals. The WSTAT fitting itself is unchanged.

## Key outputs

- `output/products/scaling/scaling_linmix_fixed_evolution_comparison_summary.csv`
- `output/products/scaling/scaling_linmix_fixed_evolution_exclude_bad_report.md`
- `output/products/scaling/scaling_linmix_fixed_evolution_good_only_report.md`
- `output/products/scaling/scaling_linmix_fixed_evolution_sensitivity_summary.csv`
- `output/products/scaling/scaling_linmix_fixed_evolution_sensitivity_report.md`
- `output/products/scaling/scaling_quality_classification.csv`
- `output/figures/scaling/lx_m500_linmix_exclude_bad.png`
- `output/figures/scaling/tx_m500_linmix_exclude_bad.png`
- `output/figures/scaling/lx_tx_linmix_exclude_bad.png`
- `output/figures/scaling/m500_tx_literature_style_exclude_bad.png`
- `output/figures/scaling/lx_m500_linmix_good_only.png`
- `output/figures/scaling/tx_m500_linmix_good_only.png`
- `output/figures/scaling/lx_tx_linmix_good_only.png`

Main exclude_bad results:
- Lx-M500 beta=1.09 -0.45/+0.47, scatter=0.165 dex.
- Tx-M500 beta=0.51 -0.25/+0.24, scatter=0.116 dex.
- Lx-Tx beta=0.77 -0.43/+0.46, scatter=0.227 dex.

good_only results:
- Lx-M500 beta=0.51 -0.61/+0.71, scatter=0.227 dex.
- Tx-M500 beta=0.43 -0.21/+0.23, scatter=0.071 dex.
- Lx-Tx beta=1.17 -0.93/+0.90, scatter=0.231 dex.

Sensitivity tests:
- `src/03_scaling/fit_scaling_relations.py` now fits Lx-M500, Tx-M500, and Lx-Tx for all/good_only/exclude_bad.
- Default leave-one-out sensitivity removes Abell_0068, Abell_0611, MACSJ0647.7+7015, and MACSJ1206.2-0847 one at a time from exclude_bad.
- Single-cluster removals shift M500-relation slopes by less than the current statistical errors. Lx-Tx is noisier and most sensitive to Abell_0611/MACSJ1206.2-0847.

## Important caveats

- Do not use old `output/products/spectral/spectral_twostep_summary.csv` as final input.
- `weiwwqeo_scaling/` is a raw reference, not the formal output location.
- Current Lx uncertainties mostly use `confidence_interval_parameter_fallback` from saved `icm_src.kT` and `icm_src.norm` confidence intervals.
- Missing Lx uncertainties remain explicitly flagged for Abell_0068, MACSJ0647.7+7015, and several excluded bad clusters.
- R500 uncertainties are stored as aperture provenance propagated from M500; they are not independent linmix errors.
- Older spectral fit plots were qualitative WSTAT displays and could make good fits look systematically low because raw source data were compared to a source model without showing the blank-sky/background contribution in the same visual space.
- Component curves in spectral QA plots are folded source-region model components: ICM, LHB, Galactic halo, and CXB. Blank-sky particle/background remains separate in the top panel, not part of the folded source model.
- Core-excised scaling remains future work.

## Next priority

1. Rerun selected spectra with native `sample_energy_flux`, especially Abell_0068 and MACSJ0647.7+7015, to replace Lx fallback/missing intervals.
2. Consider bootstrap/jackknife uncertainty summaries if needed beyond the current leave-one-out sensitivity table.
3. Start planning core-excised spectral extraction/fitting for final literature-style comparison.
4. Update final README/wiki method notes once native Lx intervals and core-excised scope are settled.
