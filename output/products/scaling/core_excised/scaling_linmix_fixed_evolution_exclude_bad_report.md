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
| exclude_bad | Lx-M500 | 18 | good:6, acceptable:6, high:6 | 0.385 -0.244/+0.247 | 1.154 -0.508/+0.538 | 2.000 -0.000/+0.000 | 0.186 -0.045/+0.056 | 0.204 | 1.333/2.000 |
| exclude_bad | Tx-M500 | 18 | good:6, acceptable:6, high:6 | 0.714 -0.172/+0.155 | 0.550 -0.338/+0.359 | 0.667 -0.000/+0.000 | 0.157 -0.033/+0.043 | 0.146 | 0.667/0.667 |
| exclude_bad | Lx-Tx | 18 | good:6, acceptable:6, high:6 | 0.781 -0.138/+0.133 | 0.689 -0.411/+0.395 | 1.000 -0.000/+0.000 | 0.245 -0.041/+0.060 | 0.210 | 2.000/1.000 |

## Figures

- `output/figures/scaling/core_excised/lx_m500_linmix_exclude_bad.png`
- `output/figures/scaling/core_excised/lx_m500_linmix_exclude_bad.pdf`
- `output/figures/scaling/core_excised/tx_m500_linmix_exclude_bad.png`
- `output/figures/scaling/core_excised/tx_m500_linmix_exclude_bad.pdf`
- `output/figures/scaling/core_excised/lx_tx_linmix_exclude_bad.png`
- `output/figures/scaling/core_excised/lx_tx_linmix_exclude_bad.pdf`
- `output/figures/scaling/core_excised/m500_tx_literature_style_exclude_bad.png`
- `output/figures/scaling/core_excised/m500_tx_literature_style_exclude_bad.pdf`

## Uncertainty Provenance

- M500 errors come from `M500_err_lo/M500_err_hi` in the canonical spectral table.
- Tx errors come from `Tx_err_lo/Tx_err_hi` and are used as Y errors for Tx-M500 or X errors for Lx-Tx.
- R500 errors are propagated from M500 and documented as aperture provenance; they are not included as independent linmix errors.
- Lx errors come from `Lx_bol_err_lo/Lx_bol_err_hi`; missing values fall back only where reported below.
- exclude_bad Tx-M500: X fallback=none; Y fallback=Abell_0209, Abell_0068, Abell_0267, Abell_0383, Abell_0586, Abell_0611, Abell_2261, MACSJ0329.7-0211, MACSJ0429.6-0253, MACSJ0647.7+7015, MACSJ0744.9+3927, MACSJ1115.9+0129, MACSJ1206.2-0847, MACSJ1720.3+3536, MACSJ1931.8-2635, RXJ1532.9+3021, RXJ2129.7+0005, RXJ2248.7-4431.
- exclude_bad Lx-Tx: X fallback=Abell_0209, Abell_0068, Abell_0267, Abell_0383, Abell_0586, Abell_0611, Abell_2261, MACSJ0329.7-0211, MACSJ0429.6-0253, MACSJ0647.7+7015, MACSJ0744.9+3927, MACSJ1115.9+0129, MACSJ1206.2-0847, MACSJ1720.3+3536, MACSJ1931.8-2635, RXJ1532.9+3021, RXJ2129.7+0005, RXJ2248.7-4431; Y fallback=none.

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
- Tx-M500 Y fallback 10% fractional 1-sigma used for: Abell_0209, Abell_0068, Abell_0267, Abell_0383, Abell_0586, Abell_0611, Abell_2261, MACSJ0329.7-0211, MACSJ0429.6-0253, MACSJ0647.7+7015, MACSJ0744.9+3927, MACSJ1115.9+0129, MACSJ1206.2-0847, MACSJ1720.3+3536, MACSJ1931.8-2635, RXJ1532.9+3021, RXJ2129.7+0005, RXJ2248.7-4431.
- Evolution exponent gamma is fixed to 0.666667 for literature-style comparison.
- Tx errors from Tx_err_lo/Tx_err_hi.
- Lx-Tx X fallback 10% fractional 1-sigma used for: Abell_0209, Abell_0068, Abell_0267, Abell_0383, Abell_0586, Abell_0611, Abell_2261, MACSJ0329.7-0211, MACSJ0429.6-0253, MACSJ0647.7+7015, MACSJ0744.9+3927, MACSJ1115.9+0129, MACSJ1206.2-0847, MACSJ1720.3+3536, MACSJ1931.8-2635, RXJ1532.9+3021, RXJ2129.7+0005, RXJ2248.7-4431.
- Evolution exponent gamma is fixed to 1 for literature-style comparison.
