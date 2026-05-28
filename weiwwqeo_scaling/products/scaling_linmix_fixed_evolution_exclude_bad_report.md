# Preliminary Scaling Relation Fits

Input: `output/products/spectral/spectral_twostep_summary.csv`

Model:

`log10(Y / E(z)^gamma_fixed) = alpha + beta log10(M500c / 3e14 Msun)`

M500c is the weak-lensing mass, independent of the X-ray observables. The redshift exponent is fixed to the literature comparison value rather than fit freely.

- Lx-M500c: `E(z)^-2 Lx_bol = A (M500c / 3e14 Msun)^beta`
- Tx-M500c: `E(z)^(-2/3) Tx = A (M500c / 3e14 Msun)^beta`

## Results

| Sample | Relation | N | quality counts | alpha | beta | fixed gamma | intrinsic scatter (dex) | observed RMS (dex) | self-similar beta/gamma |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| exclude_bad | Lx-M500 | 20 | good:11, acceptable:3, high:6 | 0.827 -0.162/+0.157 | 0.961 -0.293/+0.339 | 2.000 -0.000/+0.000 | 0.190 -0.037/+0.045 | 0.189 | 1.333/2.000 |
| exclude_bad | Tx-M500 | 20 | good:11, acceptable:3, high:6 | 0.620 -0.092/+0.087 | 0.592 -0.164/+0.180 | 0.667 -0.000/+0.000 | 0.105 -0.023/+0.028 | 0.111 | 0.667/0.667 |

## Figures

- `weiwwqeo_scaling/figures/lx_m500_linmix_exclude_bad.png`
- `weiwwqeo_scaling/figures/lx_m500_linmix_exclude_bad.pdf`
- `weiwwqeo_scaling/figures/tx_m500_linmix_exclude_bad.png`
- `weiwwqeo_scaling/figures/tx_m500_linmix_exclude_bad.pdf`
- `weiwwqeo_scaling/figures/m500_tx_literature_style_exclude_bad.png`
- `weiwwqeo_scaling/figures/m500_tx_literature_style_exclude_bad.pdf`

## Literature Context

### Lx-M500
- Mantz et al. 2010: core-excised Lx-M500 slope = 1.33 +/- 0.08. wiki/papers/mantz_2010.md; ROSAT 0.1-2.4 keV, core-excised.
- Pratt et al. 2009: wiki/papers/pratt_2009.md; REXCESS bolometric Lx slopes are steeper than self-similar, mass is Yx-derived.

### Tx-M500
- Mantz et al. 2010: wiki/papers/mantz_2010.md; slope consistent with or slightly steeper than self-similar, 10-15% scatter.
- Maughan et al. 2012: wiki/papers/maughan_2012.md; core-excised relaxed Lx-T is close to self-similar, disturbed systems are steeper.

## Assumptions

- M500 errors are not present in the summary table; assumed 20% fractional 1-sigma.
- Lx errors are not present in the summary table; assumed 10% fractional 1-sigma.
- Excludes rows classified as bad: rstat >= 3, ACCEPT ratio < 0.5, ACCEPT ratio > 5, or missing Tx errors.
- Evolution exponent gamma is fixed to 2 for literature-style comparison.
- All logarithms are base 10.
- Rows with status != done or missing positive Y/M500 were excluded.
- Tx errors from Tx_err_lo/Tx_err_hi, symmetrized in log10.
- Evolution exponent gamma is fixed to 0.666667 for literature-style comparison.
