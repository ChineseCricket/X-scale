# Preliminary Scaling Relation Fits

Input: `output/products/spectral/spectral_summary.csv`

Model:

`log10(Y / E(z)^gamma_fixed) = alpha + beta log10(M500c / 3e14 Msun)`

M500c is the weak-lensing mass, independent of the X-ray observables. The redshift exponent is fixed to the literature comparison value rather than fit freely.

- Lx-M500c: `E(z)^-2 Lx_bol = A (M500c / 3e14 Msun)^beta`
- Tx-M500c: `E(z)^(-2/3) Tx = A (M500c / 3e14 Msun)^beta`

## Results

| Sample | Relation | N | quality counts | alpha | beta | fixed gamma | intrinsic scatter (dex) | observed RMS (dex) | self-similar beta/gamma |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| good_only | Lx-M500 | 11 | good:11 | 1.055 -0.348/+0.315 | 0.511 -0.654/+0.662 | 2.000 -0.000/+0.000 | 0.225 -0.054/+0.082 | 0.187 | 1.333/2.000 |
| good_only | Tx-M500 | 11 | good:11 | 0.638 -0.114/+0.093 | 0.449 -0.180/+0.228 | 0.667 -0.000/+0.000 | 0.061 -0.030/+0.035 | 0.061 | 0.667/0.667 |

## Figures

- `output/figures/scaling/lx_m500_linmix_good_only.png`
- `output/figures/scaling/lx_m500_linmix_good_only.pdf`
- `output/figures/scaling/tx_m500_linmix_good_only.png`
- `output/figures/scaling/tx_m500_linmix_good_only.pdf`
- `output/figures/scaling/m500_tx_literature_style_good_only.png`
- `output/figures/scaling/m500_tx_literature_style_good_only.pdf`

## Uncertainty Provenance

- M500 errors come from `M500_err_lo/M500_err_hi` in the canonical spectral table.
- R500 errors are propagated from M500 and documented as aperture provenance; they are not included as independent linmix errors.
- Lx errors come from `Lx_bol_err_lo/Lx_bol_err_hi`; missing values fall back only where reported below.

## Literature Context

### Lx-M500
- Mantz et al. 2010: core-excised Lx-M500 slope = 1.33 +/- 0.08. wiki/papers/mantz_2010.md; ROSAT 0.1-2.4 keV, core-excised.
- Pratt et al. 2009: wiki/papers/pratt_2009.md; REXCESS bolometric Lx slopes are steeper than self-similar, mass is Yx-derived.

### Tx-M500
- Mantz et al. 2010: wiki/papers/mantz_2010.md; slope consistent with or slightly steeper than self-similar, 10-15% scatter.
- Maughan et al. 2012: wiki/papers/maughan_2012.md; core-excised relaxed Lx-T is close to self-similar, disturbed systems are steeper.

## Assumptions

- M500 errors use per-cluster literature columns M500_err_lo/M500_err_hi.
- Lx errors from Lx_bol_err_lo/Lx_bol_err_hi; fallbacks are reported cluster-by-cluster.
- R500 uncertainties are propagated from M500 for aperture provenance only and are not added as independent linmix errors.
- Includes only rows with quality=good in the canonical spectral table.
- Evolution exponent gamma is fixed to 2 for literature-style comparison.
- All logarithms are base 10.
- Rows with status != done or missing positive Y/M500 were excluded.
- Tx errors from Tx_err_lo/Tx_err_hi; fallbacks are reported cluster-by-cluster.
- Evolution exponent gamma is fixed to 0.666667 for literature-style comparison.
