# Final Report Follow-up Tasks for Server Agent

Date: 2026-05-29

The final report has been written from local products only. Do not rerun these tasks on the local laptop unless the full CIAO/Sherpa environment is available.

## Completed: Backfilled core-excised temperature confidence intervals

This task was completed on the server and pulled locally on 2026-05-29. The 18 included core-excised clusters now use Sherpa `conf()` intervals for `icm_src.kT`; see `output/products/scaling/core_excised/tx_confidence_backfill_change_note.md`. No further server action is needed for the headline core-excised Tx uncertainty provenance.

## Task 1: Replace remaining full-R500 luminosity uncertainty fallbacks

Prompt for server agent:

> For retained full-R500 clusters whose canonical table still marks `Lx_uncertainty_flag=native_flux_sampling_missing`, rerun only the Sherpa flux-uncertainty sampling step needed to save native `sample_energy_flux` intervals. Do not redo Chandra repro, merge, source detection, or spectral extraction. Update the affected JSON files in `output/products/spectral/`, rebuild `output/products/spectral/spectral_summary.csv`, rerun the full-R500 scaling fits, and summarize whether any reported slope or scatter changes beyond the quoted statistical uncertainty.

## Figure status after pull

The final scaling figures were present after `git pull --ff-only` in:

- `output/figures/scaling/`
- `output/figures/scaling/core_excised/`

No server-side figure regeneration is required for the current report unless later edits change the canonical scaling tables.
