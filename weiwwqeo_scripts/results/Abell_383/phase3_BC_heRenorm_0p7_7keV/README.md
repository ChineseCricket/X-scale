# Abell 383 Phase-3 B+C Example Result

This is the latest lightweight example output from the Phase-3 source+annulus Sherpa spectral pipeline.

Run configuration:

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python src/02_spectral/fit_spectral_joint.py \
  --no-run-repro --no-run-imaging --no-run-blanksky --no-run-specextract \
  --xrb-policy fixed_shape \
  --renormalize-blanksky-pha \
  --fit-min-kev 0.7 --fit-max-kev 7.0
```

Key result:

- Cluster: Abell 383
- Aperture: full R500, with point-source masks
- Background: CIAO blank-sky PHA, high-energy renormalized in 9.5-12.0 keV
- Statistic: Sherpa WSTAT
- Model: `lhb + phabs*(halo + cxb + icm_src)` for source, with annulus-constrained XRB
- `T_X = 4.9326 keV` with 1-sigma interval `-0.0956/+0.0948 keV`
- `L_X,bol = 9.716e44 erg/s`
- `L_X,0.5-2 = 3.482e44 erg/s`
- Source WSTAT: `1664.03`
- Source reduced statistic: `1.283`

Files:

- `results/*summary.json`: full pipeline summary, input files, apertures, blank-sky renormalization diagnostics, and fit result.
- `fits/*fit_results.json`: Sherpa fit output.
- `fits/*fit_plot.png`: source spectra/model/residual plot.
- `figures/*source_aperture.png`: R500 aperture and point-source masks on the smoothed flux image.
- `figures/*beta_profile.png`: radial surface-brightness profile and beta-model fit.

Large intermediate products such as spectra, ARF/RMF files, blank-sky events, and merged FITS images are intentionally not included here.
