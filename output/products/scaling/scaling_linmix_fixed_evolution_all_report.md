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
| all | Lx-M500 | 23 | good:11, acceptable:4, high:3, bad:5 | 0.828 -0.152/+0.147 | 0.984 -0.308/+0.316 | 2.000 -0.000/+0.000 | 0.198 -0.037/+0.042 | 0.200 | 1.333/2.000 |
| all | Tx-M500 | 23 | good:11, acceptable:4, high:3, bad:5 | 0.556 -0.186/+0.171 | 0.852 -0.353/+0.396 | 0.667 -0.000/+0.000 | 0.255 -0.040/+0.049 | 0.239 | 0.667/0.667 |

## Figures

- `output/figures/scaling/lx_m500_linmix_all.png`
- `output/figures/scaling/lx_m500_linmix_all.pdf`
- `output/figures/scaling/tx_m500_linmix_all.png`
- `output/figures/scaling/tx_m500_linmix_all.pdf`
- `output/figures/scaling/m500_tx_literature_style_all.png`
- `output/figures/scaling/m500_tx_literature_style_all.pdf`

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
- All rows with status=done and positive M500/Y.
- Evolution exponent gamma is fixed to 2 for literature-style comparison.
- All logarithms are base 10.
- Rows with status != done or missing positive Y/M500 were excluded.
- Tx errors from Tx_err_lo/Tx_err_hi when present; otherwise assumed 10% fractional 1-sigma.
- Evolution exponent gamma is fixed to 0.666667 for literature-style comparison.
