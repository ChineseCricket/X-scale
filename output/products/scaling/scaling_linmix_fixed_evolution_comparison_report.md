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
| all | Lx-M500 | 23 | good:11, acceptable:4, high:3, bad:5 | 0.721 -0.184/+0.160 | 1.213 -0.320/+0.366 | 2.000 -0.000/+0.000 | 0.172 -0.038/+0.046 | 0.219 | 1.333/2.000 |
| all | Tx-M500 | 23 | good:11, acceptable:4, high:3, bad:5 | 0.712 -0.241/+0.197 | 0.558 -0.420/+0.503 | 0.667 -0.000/+0.000 | 0.288 -0.042/+0.052 | 0.259 | 0.667/0.667 |
| all | Lx-Tx | 23 | good:11, acceptable:4, high:3, bad:5 | 1.192 -0.075/+0.079 | 0.533 -0.193/+0.186 | 1.000 -0.000/+0.000 | 0.245 -0.039/+0.046 | 0.219 | 2.000/1.000 |
| exclude_bad | Lx-M500 | 18 | good:11, acceptable:4, high:3 | 0.744 -0.226/+0.213 | 1.091 -0.451/+0.469 | 2.000 -0.000/+0.000 | 0.165 -0.035/+0.051 | 0.198 | 1.333/2.000 |
| exclude_bad | Tx-M500 | 18 | good:11, acceptable:4, high:3 | 0.654 -0.113/+0.116 | 0.505 -0.252/+0.236 | 0.667 -0.000/+0.000 | 0.116 -0.024/+0.031 | 0.113 | 0.667/0.667 |
| exclude_bad | Lx-Tx | 18 | good:11, acceptable:4, high:3 | 1.145 -0.112/+0.117 | 0.769 -0.433/+0.457 | 1.000 -0.000/+0.000 | 0.227 -0.040/+0.051 | 0.197 | 2.000/1.000 |
| good_only | Lx-M500 | 11 | good:11 | 1.055 -0.358/+0.294 | 0.506 -0.612/+0.714 | 2.000 -0.000/+0.000 | 0.227 -0.058/+0.082 | 0.187 | 1.333/2.000 |
| good_only | Tx-M500 | 11 | good:11 | 0.648 -0.110/+0.102 | 0.433 -0.207/+0.226 | 0.667 -0.000/+0.000 | 0.071 -0.026/+0.034 | 0.060 | 0.667/0.667 |
| good_only | Lx-Tx | 11 | good:11 | 1.141 -0.196/+0.195 | 1.166 -0.932/+0.895 | 1.000 -0.000/+0.000 | 0.231 -0.050/+0.090 | 0.178 | 2.000/1.000 |

## Figures

- `output/figures/scaling/lx_m500_linmix_all.png`
- `output/figures/scaling/lx_m500_linmix_all.pdf`
- `output/figures/scaling/tx_m500_linmix_all.png`
- `output/figures/scaling/tx_m500_linmix_all.pdf`
- `output/figures/scaling/lx_tx_linmix_all.png`
- `output/figures/scaling/lx_tx_linmix_all.pdf`
- `output/figures/scaling/m500_tx_literature_style_all.png`
- `output/figures/scaling/m500_tx_literature_style_all.pdf`
- `output/figures/scaling/lx_m500_linmix_exclude_bad.png`
- `output/figures/scaling/lx_m500_linmix_exclude_bad.pdf`
- `output/figures/scaling/tx_m500_linmix_exclude_bad.png`
- `output/figures/scaling/tx_m500_linmix_exclude_bad.pdf`
- `output/figures/scaling/lx_tx_linmix_exclude_bad.png`
- `output/figures/scaling/lx_tx_linmix_exclude_bad.pdf`
- `output/figures/scaling/m500_tx_literature_style_exclude_bad.png`
- `output/figures/scaling/m500_tx_literature_style_exclude_bad.pdf`
- `output/figures/scaling/lx_m500_linmix_good_only.png`
- `output/figures/scaling/lx_m500_linmix_good_only.pdf`
- `output/figures/scaling/tx_m500_linmix_good_only.png`
- `output/figures/scaling/tx_m500_linmix_good_only.pdf`
- `output/figures/scaling/lx_tx_linmix_good_only.png`
- `output/figures/scaling/lx_tx_linmix_good_only.pdf`
- `output/figures/scaling/m500_tx_literature_style_good_only.png`
- `output/figures/scaling/m500_tx_literature_style_good_only.pdf`

## Uncertainty Provenance

- M500 errors come from `M500_err_lo/M500_err_hi` in the canonical spectral table.
- Tx errors come from `Tx_err_lo/Tx_err_hi` and are used as Y errors for Tx-M500 or X errors for Lx-Tx.
- R500 errors are propagated from M500 and documented as aperture provenance; they are not included as independent linmix errors.
- Lx errors come from `Lx_bol_err_lo/Lx_bol_err_hi`; missing values fall back only where reported below.
- all Lx-M500: X fallback=none; Y fallback=Abell_0068, Abell_0697, Abell_0750, MACSJ0647.7+7015, MS2137-2353, RXJ1347.5-1145.
- all Tx-M500: X fallback=none; Y fallback=Abell_0750, MS2137-2353.
- all Lx-Tx: X fallback=Abell_0750, MS2137-2353; Y fallback=Abell_0068, Abell_0697, Abell_0750, MACSJ0647.7+7015, MS2137-2353, RXJ1347.5-1145.
- exclude_bad Lx-M500: X fallback=none; Y fallback=Abell_0068, MACSJ0647.7+7015.
- exclude_bad Lx-Tx: X fallback=none; Y fallback=Abell_0068, MACSJ0647.7+7015.

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

### Lx-M500
- Mantz et al. 2010: core-excised Lx-M500 slope = 1.33 +/- 0.08. wiki/papers/mantz_2010.md; ROSAT 0.1-2.4 keV, core-excised.
- Pratt et al. 2009: wiki/papers/pratt_2009.md; REXCESS bolometric Lx slopes are steeper than self-similar, mass is Yx-derived.

### Tx-M500
- Mantz et al. 2010: wiki/papers/mantz_2010.md; slope consistent with or slightly steeper than self-similar, 10-15% scatter.
- Maughan et al. 2012: wiki/papers/maughan_2012.md; core-excised relaxed Lx-T is close to self-similar, disturbed systems are steeper.

### Lx-Tx
- Maughan et al. 2012: Lx-Tx slope = 2.96 +/- 0.15. wiki/papers/maughan_2012.md; Chandra sample, used here as literature context.
- Self-similar: bolometric Lx-Tx slope = 2.00. Bolometric self-similar expectation is Lx ∝ E(z) Tx^2.

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
- All rows with status=done and positive M500/Y.
- Lx-M500 Y fallback 10% fractional 1-sigma used for: Abell_0068, Abell_0697, Abell_0750, MACSJ0647.7+7015, MS2137-2353, RXJ1347.5-1145.
- Evolution exponent gamma is fixed to 2 for literature-style comparison.
- All logarithms are base 10.
- Rows with status != done or missing positive Y/M500 were excluded.
- Tx errors from Tx_err_lo/Tx_err_hi; fallbacks are reported cluster-by-cluster.
- Tx-M500 Y fallback 10% fractional 1-sigma used for: Abell_0750, MS2137-2353.
- Evolution exponent gamma is fixed to 0.666667 for literature-style comparison.
- Tx errors from Tx_err_lo/Tx_err_hi.
- Lx-Tx X fallback 10% fractional 1-sigma used for: Abell_0750, MS2137-2353.
- Lx-Tx Y fallback 10% fractional 1-sigma used for: Abell_0068, Abell_0697, Abell_0750, MACSJ0647.7+7015, MS2137-2353, RXJ1347.5-1145.
- Evolution exponent gamma is fixed to 1 for literature-style comparison.
- Excludes rows with exclude_from_main_scaling=True in the canonical spectral table.
- Lx-M500 Y fallback 10% fractional 1-sigma used for: Abell_0068, MACSJ0647.7+7015.
- Lx-Tx Y fallback 10% fractional 1-sigma used for: Abell_0068, MACSJ0647.7+7015.
- Includes only rows with quality=good in the canonical spectral table.
