# Preliminary Scaling Relation Fits

Input: `output/products/spectral/spectral_summary_core_excised.csv`

Model:

`log10(Y / E(z)^gamma_fixed) = alpha + beta log10(X / X_pivot)`

M500c is the weak-lensing mass for the mass-scaling relations. The redshift exponent is fixed to the literature comparison value rather than fit freely.

- Lx-M500c: `E(z)^-2 Lx_bol = A (M500c / 3e14 Msun)^beta`
- Tx-M500c: `E(z)^(-2/3) Tx = A (M500c / 3e14 Msun)^beta`
- Lx-Tx: `E(z)^-1 Lx_bol = A (Tx / 5 keV)^beta`

## Results

| Sample | Relation | N | quality counts | alpha | beta | fixed gamma | intrinsic scatter (dex) | observed RMS (dex) | self-similar beta/gamma |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| good_only | Lx-M500 | 6 | good:6 | -0.274 -3.328/+2.995 | 2.287 -5.523/+6.226 | 2.000 -0.000/+0.000 | 0.398 -0.205/+0.454 | 0.167 | 1.333/2.000 |
| good_only | Tx-M500 | 6 | good:6 | 0.596 -1.418/+1.663 | 0.542 -3.074/+2.616 | 0.667 -0.000/+0.000 | 0.160 -0.078/+0.200 | 0.083 | 0.667/0.667 |
| good_only | Lx-Tx | 6 | good:6 | 0.427 -0.527/+0.435 | 2.525 -1.804/+2.150 | 1.000 -0.000/+0.000 | 0.319 -0.145/+0.342 | 0.166 | 2.000/1.000 |

## Figures

- `output/figures/scaling/core_excised/lx_m500_linmix_good_only.png`
- `output/figures/scaling/core_excised/lx_m500_linmix_good_only.pdf`
- `output/figures/scaling/core_excised/tx_m500_linmix_good_only.png`
- `output/figures/scaling/core_excised/tx_m500_linmix_good_only.pdf`
- `output/figures/scaling/core_excised/lx_tx_linmix_good_only.png`
- `output/figures/scaling/core_excised/lx_tx_linmix_good_only.pdf`
- `output/figures/scaling/core_excised/m500_tx_literature_style_good_only.png`
- `output/figures/scaling/core_excised/m500_tx_literature_style_good_only.pdf`

## Uncertainty Provenance

- M500 errors come from `M500_err_lo/M500_err_hi` in the canonical spectral table.
- Tx errors come from `Tx_err_lo/Tx_err_hi` and are used as Y errors for Tx-M500 or X errors for Lx-Tx.
- R500 errors are propagated from M500 and documented as aperture provenance; they are not included as independent linmix errors.
- Lx errors come from `Lx_bol_err_lo/Lx_bol_err_hi`; missing values fall back only where reported below.
- good_only Tx-M500: X fallback=none; Y fallback=Abell_0209, Abell_0586, MACSJ0429.6-0253, MACSJ0744.9+3927, MACSJ1931.8-2635, RXJ2248.7-4431.
- good_only Lx-Tx: X fallback=Abell_0209, Abell_0586, MACSJ0429.6-0253, MACSJ0744.9+3927, MACSJ1931.8-2635, RXJ2248.7-4431; Y fallback=none.

## Literature Context

### Lx-M500
- Mantz et al. 2010: core-excised Lx-M500 slope = 1.33 +/- 0.08. wiki/papers/mantz_2010.md; ROSAT 0.1-2.4 keV, core-excised.
- Pratt et al. 2009: wiki/papers/pratt_2009.md; REXCESS bolometric Lx slopes are steeper than self-similar, mass is Yx-derived.

### Tx-M500
- Mantz et al. 2010: wiki/papers/mantz_2010.md; slope consistent with or slightly steeper than self-similar, 10-15% scatter.
- Maughan et al. 2012: wiki/papers/maughan_2012.md; core-excised relaxed Lx-T is close to self-similar, disturbed systems are steeper.

### Lx-Tx
- Maughan et al. 2012: Lx-Tx slope = 2.96 +/- 0.15. wiki/papers/maughan_2012.md; Chandra sample, used here as literature context.
- Self-similar: bolometric Lx-Tx slope = 2.00. Bolometric self-similar expectation is Lx ∝ E(z) Tx^2.

## Assumptions

- M500 errors use per-cluster literature columns M500_err_lo/M500_err_hi.
- Lx errors from Lx_bol_err_lo/Lx_bol_err_hi; fallbacks are reported cluster-by-cluster.
- R500 uncertainties are propagated from M500 for aperture provenance only and are not added as independent linmix errors.
- Includes only rows with quality=good in the canonical spectral table.
- Evolution exponent gamma is fixed to 2 for literature-style comparison.
- All logarithms are base 10.
- Rows with status != done or missing positive Y/M500 were excluded.
- Tx errors from Tx_err_lo/Tx_err_hi; fallbacks are reported cluster-by-cluster.
- Tx-M500 Y fallback 10% fractional 1-sigma used for: Abell_0209, Abell_0586, MACSJ0429.6-0253, MACSJ0744.9+3927, MACSJ1931.8-2635, RXJ2248.7-4431.
- Evolution exponent gamma is fixed to 0.666667 for literature-style comparison.
- Tx errors from Tx_err_lo/Tx_err_hi.
- Lx-Tx X fallback 10% fractional 1-sigma used for: Abell_0209, Abell_0586, MACSJ0429.6-0253, MACSJ0744.9+3927, MACSJ1931.8-2635, RXJ2248.7-4431.
- Evolution exponent gamma is fixed to 1 for literature-style comparison.
