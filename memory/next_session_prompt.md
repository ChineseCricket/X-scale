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
- Lx-M500 beta=1.09 -0.45/+0.47, scatter=0.165 dex.
- Tx-M500 beta=0.51 -0.25/+0.24, scatter=0.116 dex.
- Lx-Tx beta=0.77 -0.43/+0.46, scatter=0.227 dex.

good_only N=11:
- Lx-M500 beta=0.51 -0.61/+0.71, scatter=0.227 dex.
- Tx-M500 beta=0.43 -0.21/+0.23, scatter=0.071 dex.
- Lx-Tx beta=1.17 -0.93/+0.90, scatter=0.231 dex.

Sensitivity:
- Leave-one-out removes Abell_0068, Abell_0611, MACSJ0647.7+7015, and MACSJ1206.2-0847 one at a time from exclude_bad.
- Single-cluster removals shift M500-relation slopes by less than current statistical errors.
- Lx-Tx is noisier and most sensitive to Abell_0611/MACSJ1206.2-0847.

## Core-excised results

Main exclude_bad N=18:
- Lx-M500 beta=1.15 -0.51/+0.54, scatter=0.186 dex.
- Tx-M500 beta=0.55 -0.34/+0.36, scatter=0.157 dex.
- Lx-Tx beta=0.69 -0.41/+0.40, scatter=0.245 dex.

good_only N=6:
- Lx-M500 beta=2.29 -5.52/+6.23, scatter=0.398 dex.
- Tx-M500 beta=0.54 -3.07/+2.62, scatter=0.160 dex.
- Lx-Tx beta=2.53 -1.80/+2.15, scatter=0.319 dex.

Core-excised caveat:
- Included core-excised Lx uncertainties are native `sherpa.sample_energy_flux`.
- Core-excised T_X confidence intervals are missing in the JSONs, so Tx-M500 and Lx-Tx currently use the documented 10% Tx fallback.
- Decision: do not block final reporting on core-excised Tx confidence interval recovery; explicitly report the 10% fallback in final methods and tables.

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
