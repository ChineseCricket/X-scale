---
note: 将此文件内容直接粘贴到新 session 作为初始 prompt，然后删除本文件。
---

# Next Session Prompt: Final Report Polish

Read `CLAUDE.md`, `memory/pipeline_status.csv`, and `memory/workflow_plan.md` first.

## Current status

- Phase 4 full-R500 scaling is complete.
- Core-excised spectral fitting for the main included sample is complete: 18/18 included clusters have `0.15-1.0 R500` result JSONs.
- Core-excised lightweight QA is complete; see `output/products/spectral/core_excised_spectral_qa_report.md`.
- Full-vs-core interpretation is drafted; see `output/products/scaling/full_vs_core_excised_comparison.md`.
- The five excluded bad clusters do not have core-excised JSONs yet; this is optional completeness/appendix work only.
- Full-R500 remains the canonical baseline, and core-excised is now available as the formal literature-style comparison branch.

## Main sample and exclusions

- Main scaling sample: 18 included, 5 excluded.
- Excluded clusters: Abell_0697, Abell_0750, MS2137-2353, RXJ1347.5-1145, ZwCl_0857.9+2107.
- Included clusters with core-excised results:
  Abell_0209, Abell_0068, Abell_0267, Abell_0383, Abell_0586, Abell_0611, Abell_2261, MACSJ0329.7-0211, MACSJ0429.6-0253, MACSJ0647.7+7015, MACSJ0744.9+3927, MACSJ1115.9+0129, MACSJ1206.2-0847, MACSJ1720.3+3536, MACSJ1931.8-2635, RXJ1532.9+3021, RXJ2129.7+0005, RXJ2248.7-4431.

## Key products

- Full-R500 spectral summary: `output/products/spectral/spectral_summary.csv`
- Core-excised spectral summary: `output/products/spectral/spectral_summary_core_excised.csv`
- Full-R500 scaling products: `output/products/scaling/`
- Core-excised scaling products: `output/products/scaling/core_excised/`
- Core-excised spectral JSONs: `output/products/spectral/core_excised/`
- Core-excised spectral figures: `output/figures/spectral/core_excised/`
- Core-excised scaling figures: `output/figures/scaling/core_excised/`
- Core-excised spectral QA report: `output/products/spectral/core_excised_spectral_qa_report.md`
- Full-vs-core comparison note: `output/products/scaling/full_vs_core_excised_comparison.md`

## Formal scripts

- `src/02_spectral/fit_spectral_xrb.py`
  - supports `--excise-core/--no-excise-core`
  - supports `--core-inner-r500 0.15`
  - writes full-R500 and core-excised products to separate paths
  - writes native Sherpa `sample_energy_flux` Lx intervals on reruns
- `src/03_scaling/build_spectral_summary.py`
  - supports `--results-dir` and `--output`
  - use this for both full-R500 and core-excised summaries
- `src/03_scaling/fit_scaling_relations.py`
  - supports `--summary`, `--outdir`, and `--figdir`
  - fits Lx-M500, Tx-M500, and Lx-Tx for all/exclude_bad/good_only

## Full-R500 results

Main exclude_bad N=18:
- Lx-M500 beta=1.08 -0.49/+0.53, scatter=0.169 dex.
- Tx-M500 beta=0.48 -0.25/+0.26, scatter=0.117 dex.
- Lx-Tx beta=0.76 -0.41/+0.43, scatter=0.227 dex.

good_only N=11:
- Lx-M500 beta=0.55 -0.68/+0.68, scatter=0.223 dex.
- Tx-M500 beta=0.44 -0.17/+0.20, scatter=0.064 dex.
- Lx-Tx beta=1.23 -0.96/+0.85, scatter=0.228 dex.

Sensitivity:
- Leave-one-out removes Abell_0068, Abell_0611, MACSJ0647.7+7015, and MACSJ1206.2-0847 one at a time from exclude_bad.
- Single-cluster removals shift M500-relation slopes by less than current statistical errors.
- Lx-Tx is noisier and most sensitive to Abell_0611/MACSJ1206.2-0847.

## Core-excised results

Main exclude_bad N=18:
- Lx-M500 beta=1.16 -0.49/+0.53, scatter=0.192 dex.
- Tx-M500 beta=0.56 -0.31/+0.30, scatter=0.134 dex.
- Lx-Tx beta=0.90 -0.43/+0.46, scatter=0.230 dex.

good_only N=6:
- Lx-M500 beta=2.58 -5.47/+8.48, scatter=0.392 dex.
- Tx-M500 beta=0.55 -2.54/+2.38, scatter=0.157 dex.
- Lx-Tx beta=2.68 -1.60/+1.53, scatter=0.288 dex.

Core-excised caveat:
- Included core-excised Lx uncertainties are native `sherpa.sample_energy_flux`.
- Included core-excised T_X uncertainties are now native Sherpa `conf()` intervals for `icm_src.kT` after the 2026-05-29 server backfill.
- Decision: final reporting should describe the native core-excised Tx intervals; the earlier 10% Tx fallback no longer applies to the 18-cluster included core-excised comparison.

Core-excised QA:
- 18/18 included core-excised JSONs and QA plots exist.
- Low-q clusters: Abell_0209, Abell_0383, Abell_2261, MACSJ0329.7-0211, MACSJ1720.3+3536.
- High core-excised Tx relative to ACCEPT: Abell_0383, Abell_0611, MACSJ0329.7-0211, MACSJ0647.7+7015, MACSJ1206.2-0847, MACSJ1720.3+3536.
- Abell_0267 has one low-count ObsID residual-summary outlier, but joint rstat/q are acceptable; do not exclude on that basis.

## Rebuild commands

Rebuild core-excised summary and scaling:

```bash
python src/03_scaling/build_spectral_summary.py --results-dir output/products/spectral/core_excised --output output/products/spectral/spectral_summary_core_excised.csv --default-aperture-label core_excised_0.15_1.0R500
source /data/jyz/Applications/ciao-4.18/ciao-4.18/bin/ciao.sh && python src/03_scaling/fit_scaling_relations.py --summary output/products/spectral/spectral_summary_core_excised.csv --outdir output/products/scaling/core_excised --figdir output/figures/scaling/core_excised --skip-sensitivity
```

Run an optional excluded bad core-excised cluster:

```bash
source /data/jyz/Applications/ciao-4.18/ciao-4.18/bin/ciao.sh && python src/02_spectral/fit_spectral_xrb.py --cluster <key> --excise-core --core-inner-r500 0.15 --xrb-policy fixed_shape --renormalize-blanksky-pha --no-run-blanksky --no-run-specextract --flux-samples 3000
```

Use `--xrb-policy flexible` only when scientifically justified by the full-R500 behavior.

## Important caveats

- Do not use old `output/products/spectral/spectral_twostep_summary.csv` as final input.
- `weiwwqeo_scaling/` is a raw reference, not the formal output location.
- Core-excised luminosity must be labeled explicitly as `0.15-1.0 R500`; do not mix it silently with full-R500 luminosity.
- R500 uncertainties are aperture provenance propagated from M500; they are not independent linmix errors.
- Do not over-interpret the Lx-M500 `good_only` normalization `A` at the fixed `3e14 Msun` pivot. The good-only samples lie well above that pivot, especially core-excised good-only (N=6, M500=6.85-12.45e14 Msun), so `alpha` and `beta` are strongly degenerate. Treat good-only as a sensitivity check and compare normalization near the sample mass range instead of at the extrapolated pivot.
- Component curves in spectral QA plots are folded source-region model components: ICM, LHB, Galactic halo, and CXB. Blank-sky particle/background remains separate in the top panel.
- Spectral QA residual panels use robust y-axis limits for readability; JSON residual summaries preserve original extrema.
- Output figures under `output/figures/` are ignored by git; product CSV/JSON/Markdown under `output/products/` are tracked.

## Next priority

1. Polish final report/manuscript text around sample definition, exclusions, spectral method, and scaling interpretation.
2. Make final tables from `spectral_summary.csv`, `spectral_summary_core_excised.csv`, and scaling summaries.
3. Choose final figures from `output/figures/scaling/` and `output/figures/scaling/core_excised/`.
4. Optional only: run the five excluded bad clusters core-excised for appendix completeness.

## Are we at the final step?

Yes. The main analysis products now exist for both full-R500 and core-excised included samples, and final QA/reporting notes are in place. The remaining work is final prose/table/figure polish unless you choose optional excluded-bad appendix runs or core-excised Tx confidence recovery.
