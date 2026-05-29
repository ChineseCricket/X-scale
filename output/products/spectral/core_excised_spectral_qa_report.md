# Core-Excised Spectral QA Report

Date: 2026-05-29

Input summary: `output/products/spectral/spectral_summary_core_excised.csv`

## Scope

- Main included sample: 18/18 clusters have core-excised `0.15-1.0 R500` result JSONs.
- Excluded bad clusters remain in the summary table as excluded rows, but do not have core-excised JSONs: Abell_0697, Abell_0750, MS2137-2353, RXJ1347.5-1145, ZwCl_0857.9+2107.
- QA plots exist for all 18 included clusters under `output/figures/spectral/core_excised/`.

## Product Checks

- Aperture label is consistently `core_excised_0.15_1.0R500` for the core-excised summary.
- Included core-excised rows all use native Sherpa `sample_energy_flux` luminosity intervals.
- Included core-excised rows now have stored `Tx_err_lo/Tx_err_hi` values from Sherpa `conf()` intervals after the 2026-05-29 server backfill; Tx-M500 and Lx-Tx no longer use the earlier 10% Tx fallback for the 18 included clusters.
- JSON `fit_plot_png` fields now point to the copied QA products in `output/figures/spectral/core_excised/`.
- Residual summaries are retained in JSON. The residual plot y-axis uses robust limits so one low-count bin cannot make a QA panel unreadable.

## Fit-Quality Flags

The included core-excised sample has quality counts: good=6, acceptable=6, high=6.

Clusters with `qval < 0.01`: Abell_0209, Abell_0383, Abell_2261, MACSJ0329.7-0211, MACSJ1720.3+3536.

Clusters with `qval < 0.05`: Abell_0209, Abell_0383, Abell_0586, Abell_2261, MACSJ0329.7-0211, MACSJ1206.2-0847, MACSJ1720.3+3536.

Clusters with core-excised `T_X / ACCEPT > 1.5`: Abell_0383, Abell_0611, MACSJ0329.7-0211, MACSJ0647.7+7015, MACSJ1206.2-0847, MACSJ1720.3+3536.

Abell_0267 has one low-count ObsID residual-summary outlier in ObsID 523 (`max_abs_residual` about 1144), but the joint WSTAT fit quality is acceptable (`rstat=1.030`, `qval=0.222`). This is treated as a QA-plot/display outlier rather than a reason to exclude the cluster from the main scaling sample.

## Tx-Interval Decision

The server-side confidence backfill is complete for the 18 included clusters. The current core-excised comparison is acceptable if the methods and tables explicitly state that:

- luminosity errors are native Sherpa `sample_energy_flux` intervals;
- Tx errors for core-excised Tx-M500 and Lx-Tx use native Sherpa `conf()` intervals for `icm_src.kT`;
- full-R500 remains the canonical baseline, while core-excised is a literature-style comparison branch.

The qualitative conclusion is unchanged by replacing the temporary fallback: full-R500 and core-excised mass-based slopes agree within the present statistical uncertainties.
