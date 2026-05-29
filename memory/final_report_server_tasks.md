# Final Report Follow-up Tasks for Server Agent

Date: 2026-05-29

The final report has been written from local products only. Do not rerun these tasks on the local laptop unless the full CIAO/Sherpa environment is available.

## Task 1: Backfill core-excised temperature confidence intervals

Prompt for server agent:

> Use the existing CIAO/Sherpa environment and the already extracted core-excised spectra in `processed_joint_bxc_coreexcised/` to compute and store `T_X` confidence intervals for the 18 included clusters. Do not change the best-fit values unless the confidence calculation exposes a real fit failure. Update the core-excised result JSON files under `output/products/spectral/core_excised/`, rebuild `output/products/spectral/spectral_summary_core_excised.csv`, and rerun the core-excised scaling fits. Compare the new `Tx-M500` and `Lx-Tx` results against the current 10 percent fallback results and write a short change note to `output/products/scaling/core_excised/`.

## Task 2: Replace remaining full-R500 luminosity uncertainty fallbacks

Prompt for server agent:

> For retained full-R500 clusters whose canonical table still marks `Lx_uncertainty_flag=native_flux_sampling_missing`, rerun only the Sherpa flux-uncertainty sampling step needed to save native `sample_energy_flux` intervals. Do not redo Chandra repro, merge, source detection, or spectral extraction. Update the affected JSON files in `output/products/spectral/`, rebuild `output/products/spectral/spectral_summary.csv`, rerun the full-R500 scaling fits, and summarize whether any reported slope or scatter changes beyond the quoted statistical uncertainty.

## Figure status after pull

The final scaling figures were present after `git pull --ff-only` in:

- `output/figures/scaling/`
- `output/figures/scaling/core_excised/`

No server-side figure regeneration is required for the current report unless later edits change the canonical scaling tables.
