# Final Report Polish Notes

Date: 2026-05-29

Source products:
- Full-R500 spectral table: `output/products/spectral/spectral_summary.csv`
- Core-excised spectral table: `output/products/spectral/spectral_summary_core_excised.csv`
- Full-R500 scaling products: `output/products/scaling/`
- Core-excised scaling products: `output/products/scaling/core_excised/`

## Manuscript Positioning

This analysis measures X-ray scaling relations for a weak-lensing calibrated cluster sample using Chandra spectroscopy. The formal baseline uses luminosities and temperatures measured within full R500 apertures. A core-excised branch, measured over `0.15-1.0 R500`, is retained as the literature-style comparison because many reference scaling analyses remove the cool core when estimating temperature and luminosity.

The final scaling sample contains 18 clusters. Five systems are excluded from the main fits because their full-R500 spectra have failed or suspect fit quality, or because the external reference comparison is inconsistent with the recovered Chandra measurement: Abell_0697, Abell_0750, MS2137-2353, RXJ1347.5-1145, and ZwCl_0857.9+2107. These systems should be described as excluded quality-control objects, not as non-detections.

## Sample Definition Text

The parent working sample consists of 23 CLASH and LoCuSS clusters with Chandra imaging/spectroscopy and weak-lensing M500 measurements. We use the literature weak-lensing masses as the independent mass scale: CLASH masses are taken from Umetsu et al. (2016), while LoCuSS masses are taken from Okabe et al. (2016), with the tabulated values converted to the adopted h70 convention where required. R500 is derived from M500 and the critical density at the cluster redshift; its uncertainty is therefore aperture provenance propagated from the mass uncertainty, not an additional independent error in the regression.

After the spectral QA pass, the main scaling sample includes 18 clusters. Abell_0697, Abell_0750, MS2137-2353, RXJ1347.5-1145, and ZwCl_0857.9+2107 are removed from the baseline fits because their spectra or reference comparisons fail the adopted quality criteria. The retained sample still includes several high-temperature or low-q systems, which are carried through the baseline analysis and addressed with the `good_only` and leave-one-out sensitivity checks.

## Spectral Method Text

Spectra are extracted per ObsID and fit jointly in Sherpa over 0.7-7 keV. The source model is an absorbed APEC plasma with fixed abundance unless otherwise documented. The particle/background contribution is handled with blank-sky spectra renormalized in the 9.5-12 keV band, while the sky background is represented by folded source-region components for the local hot bubble, Galactic halo, and cosmic X-ray background. The adopted default XRB treatment is the fixed-shape model; flexible XRB tests are used only where the full-R500 behavior warrants them.

For the baseline branch, source regions extend to R500. For the comparison branch, source regions cover `0.15-1.0 R500`. Full-R500 and core-excised products are kept in separate spectral and scaling directories so that full-aperture luminosities are never mixed silently with core-excised luminosities.

Full-R500 luminosity and temperature uncertainties use the stored spectral confidence information where available, with documented fallbacks in the canonical summary table. Core-excised luminosity intervals for the included sample use native Sherpa `sample_energy_flux` intervals. Core-excised temperature confidence intervals are not stored in the current JSON products, so the core-excised Tx-M500 and Lx-Tx fits use the documented 10 percent fractional Tx fallback. This fallback must remain explicit in the methods text and table notes.

## Scaling Method Text

Scaling relations are fit with `linmix` using base-10 logarithms and fixed self-similar redshift evolution:

- `E(z)^-2 Lx,bol = A (M500 / 3e14 Msun)^beta`
- `E(z)^(-2/3) Tx = A (M500 / 3e14 Msun)^beta`
- `E(z)^-1 Lx,bol = A (Tx / 5 keV)^beta`

The reported intrinsic scatter is in dex in the dependent variable at fixed independent variable. The main reported sample is `exclude_bad` with N=18. The `good_only` sample is a quality-sensitivity subset rather than the primary inference, especially for core-excised products where only six clusters pass the strict quality cut.

## Results Text

The full-R500 baseline yields mass-relation slopes of beta = 1.08 -0.48/+0.45 for Lx-M500 and beta = 0.50 -0.27/+0.29 for Tx-M500, with intrinsic scatters of 0.169 dex and 0.117 dex, respectively. The Lx-Tx relation is substantially noisier, with beta = 0.77 -0.44/+0.47 and intrinsic scatter of 0.227 dex.

The core-excised `0.15-1.0 R500` comparison gives beta = 1.15 -0.51/+0.54 for Lx-M500 and beta = 0.55 -0.34/+0.36 for Tx-M500, with intrinsic scatters of 0.186 dex and 0.157 dex. The core-excised Lx-Tx slope is beta = 0.69 -0.41/+0.40 with intrinsic scatter of 0.245 dex. These values agree with the full-R500 baseline within the current statistical uncertainties.

The principal interpretation is that the mass-based slopes are stable to core excision at the present precision. Core excision does not reduce the measured scatter in this heterogeneous small sample, likely because the result is limited by sample size, high-temperature systems, variable fit quality, and the temporary 10 percent Tx fallback in the core-excised branch. The Lx-Tx relation remains the least stable relation and should be discussed as sensitivity-limited rather than used as the headline result.

## Final Tables

Use these generated final table products:

- `output/products/final_spectral_table.csv`: 18-cluster included sample with full-R500 and core-excised spectral quantities.
- `output/products/final_scaling_table.csv`: full-R500 and core-excised scaling results for `exclude_bad` and `good_only`.

Compact manuscript table for the main `exclude_bad` scaling sample:

| Aperture | Relation | N | beta | Intrinsic scatter dex | Note |
|---|---|---:|---:|---:|---|
| Full R500 | Lx-M500 | 18 | 1.08 -0.48/+0.45 | 0.169 | Baseline |
| Full R500 | Tx-M500 | 18 | 0.50 -0.27/+0.29 | 0.117 | Baseline |
| Full R500 | Lx-Tx | 18 | 0.77 -0.44/+0.47 | 0.227 | Noisiest baseline relation |
| 0.15-1.0 R500 | Lx-M500 | 18 | 1.15 -0.51/+0.54 | 0.186 | Core-excised comparison |
| 0.15-1.0 R500 | Tx-M500 | 18 | 0.55 -0.34/+0.36 | 0.157 | Core Tx uses 10 percent fallback |
| 0.15-1.0 R500 | Lx-Tx | 18 | 0.69 -0.41/+0.40 | 0.245 | Core Tx uses 10 percent fallback |

## Final Figure Selection

Use PDFs for manuscript submission and PNGs for quick review.

Primary full-R500 figures:
- `output/figures/scaling/lx_m500_linmix_exclude_bad.pdf`
- `output/figures/scaling/m500_tx_literature_style_exclude_bad.pdf`
- `output/figures/scaling/lx_tx_linmix_exclude_bad.pdf`

Core-excised comparison figures:
- `output/figures/scaling/core_excised/lx_m500_linmix_exclude_bad.pdf`
- `output/figures/scaling/core_excised/m500_tx_literature_style_exclude_bad.pdf`
- `output/figures/scaling/core_excised/lx_tx_linmix_exclude_bad.pdf`

Sensitivity or appendix figures:
- `output/figures/scaling/lx_m500_linmix_good_only.pdf`
- `output/figures/scaling/m500_tx_literature_style_good_only.pdf`
- `output/figures/scaling/lx_tx_linmix_good_only.pdf`
- `output/figures/scaling/core_excised/lx_m500_linmix_good_only.pdf`
- `output/figures/scaling/core_excised/m500_tx_literature_style_good_only.pdf`
- `output/figures/scaling/core_excised/lx_tx_linmix_good_only.pdf`

Avoid using `all` sample figures as headline figures unless explicitly discussing why the excluded bad clusters bias or destabilize the fits.

