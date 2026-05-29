---
note: 将此文件内容直接粘贴到新 session 作为初始 prompt，然后删除本文件。
---

# Next Session Prompt: Phase 4 Core-Excised Finish + Final Reporting

Read `CLAUDE.md`, `memory/pipeline_status.csv`, and `memory/workflow_plan.md` first.

## Current status

- Phase 4 full-R500 uncertainty + Lx-Tx + leave-one-out sensitivity upgrade is complete.
- Full-R500 canonical spectral table: `output/products/spectral/spectral_summary.csv`.
- M500 reference table: `configs/m500_reference.csv`.
- Main full-R500 scaling sample: 18 included, 5 excluded.
- Excluded clusters: Abell_0697, Abell_0750, MS2137-2353, RXJ1347.5-1145, ZwCl_0857.9+2107.
- Full-R500 `good_only` sample exists and currently has 11 clusters.
- Abell_0068 and MACSJ0647.7+7015 full-R500 native Sherpa `sample_energy_flux` Lx intervals are now complete; they no longer carry missing/fallback Lx flags in the exclude_bad main sample.
- Core-excised formal branch exists and is in progress:
  - aperture: `0.15-1.0 R500`
  - products: `output/products/spectral/core_excised/`
  - summary: `output/products/spectral/spectral_summary_core_excised.csv`
  - scaling products: `output/products/scaling/core_excised/`
  - figures: `output/figures/spectral/core_excised/` and `output/figures/scaling/core_excised/`
  - cluster working dirs: `processed_joint_bxc_coreexcised/`

## Formal scripts

- `src/02_spectral/fit_spectral_xrb.py`
  - supports `--excise-core/--no-excise-core`
  - supports `--core-inner-r500 0.15`
  - writes full-R500 and core-excised products to separate paths
  - writes native Sherpa `sample_energy_flux` intervals on reruns
- `src/03_scaling/build_spectral_summary.py`
  - supports `--results-dir` and `--output`
  - use this for both full-R500 and core-excised summaries
- `src/03_scaling/fit_scaling_relations.py`
  - supports `--summary`, `--outdir`, and `--figdir`
  - fits Lx-M500, Tx-M500, and Lx-Tx for all/exclude_bad/good_only when enough clusters exist
  - skips under-populated samples rather than aborting
- `src/03_scaling/backfill_lx_uncertainties.py`

## Key full-R500 outputs

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

## Full-R500 results

Main exclude_bad:
- Lx-M500 beta=1.09 -0.45/+0.47, scatter=0.165 dex.
- Tx-M500 beta=0.51 -0.25/+0.24, scatter=0.116 dex.
- Lx-Tx beta=0.77 -0.43/+0.46, scatter=0.227 dex.

good_only:
- Lx-M500 beta=0.51 -0.61/+0.71, scatter=0.227 dex.
- Tx-M500 beta=0.43 -0.21/+0.23, scatter=0.071 dex.
- Lx-Tx beta=1.17 -0.93/+0.90, scatter=0.231 dex.

Sensitivity:
- Leave-one-out removes Abell_0068, Abell_0611, MACSJ0647.7+7015, and MACSJ1206.2-0847 one at a time from exclude_bad.
- Single-cluster removals shift M500-relation slopes by less than current statistical errors.
- Lx-Tx is noisier and most sensitive to Abell_0611/MACSJ1206.2-0847.

## Core-excised status

- Current core-excised summary has 14 done clusters, all in the included/exclude_bad sample.
- Done: Abell_0209, Abell_0068, Abell_0267, Abell_0383, Abell_0586, Abell_0611, Abell_2261, MACSJ0329.7-0211, MACSJ0429.6-0253, MACSJ0647.7+7015, MACSJ0744.9+3927, MACSJ1115.9+0129, MACSJ1206.2-0847, MACSJ1720.3+3536.
- Remaining included clusters to run: MACSJ1931.8-2635, RXJ1532.9+3021, RXJ2129.7+0005, RXJ2248.7-4431.
- Excluded bad clusters can be run later for completeness only: Abell_0697, Abell_0750, MS2137-2353, RXJ1347.5-1145, ZwCl_0857.9+2107.
- Current core-excised Lx uncertainties use native `sherpa.sample_energy_flux`.
- Current core-excised T_X confidence intervals are missing, so scaling uses the documented 10% Tx fallback for Tx-M500 and Lx-Tx.

Current core-excised exclude_bad N=14:
- Lx-M500 beta=1.20 -0.47/+0.51, scatter=0.165 dex.
- Tx-M500 beta=0.49 -0.51/+0.45, scatter=0.169 dex.
- Lx-Tx beta=0.78 -0.37/+0.41, scatter=0.225 dex.

## Commands

Run a core-excised cluster:

```bash
source /data/jyz/Applications/ciao-4.18/ciao-4.18/bin/ciao.sh && python src/02_spectral/fit_spectral_xrb.py --cluster <key> --excise-core --core-inner-r500 0.15 --xrb-policy fixed_shape --renormalize-blanksky-pha --no-run-blanksky --no-run-specextract --flux-samples 3000
```

If a cluster needs flexible XRB, use `--xrb-policy flexible` consistently with the full-R500 judgment.

Rebuild core-excised products:

```bash
python src/03_scaling/build_spectral_summary.py --results-dir output/products/spectral/core_excised --output output/products/spectral/spectral_summary_core_excised.csv --default-aperture-label core_excised_0.15_1.0R500
source /data/jyz/Applications/ciao-4.18/ciao-4.18/bin/ciao.sh && python src/03_scaling/fit_scaling_relations.py --summary output/products/spectral/spectral_summary_core_excised.csv --outdir output/products/scaling/core_excised --figdir output/figures/scaling/core_excised --skip-sensitivity
```

## Important caveats

- Do not use old `output/products/spectral/spectral_twostep_summary.csv` as final input.
- `weiwwqeo_scaling/` is a raw reference, not the formal output location.
- Full-R500 remains canonical until the core-excised included batch is complete and checked.
- Core-excised luminosity must be labeled explicitly as `0.15-1.0 R500`; do not mix it silently with full-R500 luminosity.
- R500 uncertainties are aperture provenance propagated from M500; they are not independent linmix errors.
- Component curves in spectral QA plots are folded source-region model components: ICM, LHB, Galactic halo, and CXB. Blank-sky particle/background remains separate in the top panel.
- Output figures under `output/figures/` are ignored by git; product CSV/JSON/Markdown under `output/products/` are tracked.

## Next priority

1. Finish the remaining 4 included core-excised clusters.
2. Rebuild `spectral_summary_core_excised.csv` and `output/products/scaling/core_excised/`.
3. Decide whether to add core-excised T_X confidence interval support or explicitly keep/report the 10% Tx fallback.
4. Start final README/wiki/method notes and final comparison table/figures.

## Are we near the final step?

Yes. The full-R500 science result is essentially ready to freeze. The main remaining analysis work is finishing the core-excised included batch and documenting final methods/results; after that the project moves into final reporting rather than new pipeline development.
