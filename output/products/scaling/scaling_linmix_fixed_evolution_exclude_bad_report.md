# Preliminary Scaling Relation Fits

Input: `output/products/spectral/spectral_summary.csv`

Model:

`log10(Y / E(z)^gamma_fixed) = alpha + beta log10(X / X_pivot)`

M500c is the weak-lensing mass for the mass-scaling relations. The redshift exponent is fixed to the literature comparison value rather than fit freely.

- Lx-M500c: `E(z)^-2 Lx_bol = A (M500c / 3e14 Msun)^beta`
- Tx-M500c: `E(z)^(-2/3) Tx = A (M500c / 3e14 Msun)^beta`
- Lx-Tx: `E(z)^-1 Lx_bol = A (Tx / 5 keV)^beta`

## Results

| Sample | Relation | N | quality counts | alpha | beta | fixed gamma | intrinsic scatter (dex) | observed RMS (dex) | self-similar beta/gamma |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| exclude_bad | Lx-M500 | 18 | good:11, acceptable:4, high:3 | 0.752 -0.243/+0.232 | 1.084 -0.490/+0.531 | 2.000 -0.000/+0.000 | 0.169 -0.042/+0.054 | 0.197 | 1.333/2.000 |
| exclude_bad | Tx-M500 | 18 | good:11, acceptable:4, high:3 | 0.670 -0.119/+0.112 | 0.478 -0.246/+0.262 | 0.667 -0.000/+0.000 | 0.117 -0.027/+0.031 | 0.112 | 0.667/0.667 |
| exclude_bad | Lx-Tx | 18 | good:11, acceptable:4, high:3 | 1.154 -0.114/+0.107 | 0.759 -0.415/+0.427 | 1.000 -0.000/+0.000 | 0.227 -0.039/+0.045 | 0.197 | 2.000/1.000 |

## Figures

- `output/figures/scaling/lx_m500_linmix_exclude_bad.png`
- `output/figures/scaling/lx_m500_linmix_exclude_bad.pdf`
- `output/figures/scaling/tx_m500_linmix_exclude_bad.png`
- `output/figures/scaling/tx_m500_linmix_exclude_bad.pdf`
- `output/figures/scaling/lx_tx_linmix_exclude_bad.png`
- `output/figures/scaling/lx_tx_linmix_exclude_bad.pdf`
- `output/figures/scaling/m500_tx_literature_style_exclude_bad.png`
- `output/figures/scaling/m500_tx_literature_style_exclude_bad.pdf`

## Uncertainty Provenance

- M500 errors come from `M500_err_lo/M500_err_hi` in the canonical spectral table.
- Tx errors come from `Tx_err_lo/Tx_err_hi` and are used as Y errors for Tx-M500 or X errors for Lx-Tx.
- R500 errors are propagated from M500 and documented as aperture provenance; they are not included as independent linmix errors.
- Lx errors come from `Lx_bol_err_lo/Lx_bol_err_hi`; missing values fall back only where reported below.

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
- Excludes rows with exclude_from_main_scaling=True in the canonical spectral table.
- Evolution exponent gamma is fixed to 2 for literature-style comparison.
- All logarithms are base 10.
- Rows with status != done or missing positive Y/M500 were excluded.
- Tx errors from Tx_err_lo/Tx_err_hi; fallbacks are reported cluster-by-cluster.
- Evolution exponent gamma is fixed to 0.666667 for literature-style comparison.
- Tx errors from Tx_err_lo/Tx_err_hi.
- Evolution exponent gamma is fixed to 1 for literature-style comparison.
