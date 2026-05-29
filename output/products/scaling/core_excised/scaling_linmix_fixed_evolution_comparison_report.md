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
| all | Lx-M500 | 14 | good:4, acceptable:4, high:6 | 0.305 -0.260/+0.228 | 1.227 -0.485/+0.532 | 2.000 -0.000/+0.000 | 0.164 -0.047/+0.058 | 0.154 | 1.333/2.000 |
| all | Tx-M500 | 14 | good:4, acceptable:4, high:6 | 0.763 -0.213/+0.232 | 0.503 -0.480/+0.440 | 0.667 -0.000/+0.000 | 0.168 -0.036/+0.052 | 0.146 | 0.667/0.667 |
| all | Lx-Tx | 14 | good:4, acceptable:4, high:6 | 0.688 -0.155/+0.149 | 0.779 -0.394/+0.403 | 1.000 -0.000/+0.000 | 0.221 -0.044/+0.067 | 0.183 | 2.000/1.000 |
| exclude_bad | Lx-M500 | 14 | good:4, acceptable:4, high:6 | 0.322 -0.240/+0.227 | 1.203 -0.467/+0.509 | 2.000 -0.000/+0.000 | 0.165 -0.046/+0.058 | 0.153 | 1.333/2.000 |
| exclude_bad | Tx-M500 | 14 | good:4, acceptable:4, high:6 | 0.770 -0.225/+0.232 | 0.485 -0.512/+0.453 | 0.667 -0.000/+0.000 | 0.169 -0.040/+0.052 | 0.145 | 0.667/0.667 |
| exclude_bad | Lx-Tx | 14 | good:4, acceptable:4, high:6 | 0.688 -0.148/+0.142 | 0.782 -0.369/+0.405 | 1.000 -0.000/+0.000 | 0.225 -0.045/+0.062 | 0.183 | 2.000/1.000 |

## Figures

- `output/figures/scaling/core_excised/lx_m500_linmix_all.png`
- `output/figures/scaling/core_excised/lx_m500_linmix_all.pdf`
- `output/figures/scaling/core_excised/tx_m500_linmix_all.png`
- `output/figures/scaling/core_excised/tx_m500_linmix_all.pdf`
- `output/figures/scaling/core_excised/lx_tx_linmix_all.png`
- `output/figures/scaling/core_excised/lx_tx_linmix_all.pdf`
- `output/figures/scaling/core_excised/m500_tx_literature_style_all.png`
- `output/figures/scaling/core_excised/m500_tx_literature_style_all.pdf`
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
- all Tx-M500: X fallback=none; Y fallback=Abell_0209, Abell_0068, Abell_0267, Abell_0383, Abell_0586, Abell_0611, Abell_2261, MACSJ0329.7-0211, MACSJ0429.6-0253, MACSJ0647.7+7015, MACSJ0744.9+3927, MACSJ1115.9+0129, MACSJ1206.2-0847, MACSJ1720.3+3536.
- all Lx-Tx: X fallback=Abell_0209, Abell_0068, Abell_0267, Abell_0383, Abell_0586, Abell_0611, Abell_2261, MACSJ0329.7-0211, MACSJ0429.6-0253, MACSJ0647.7+7015, MACSJ0744.9+3927, MACSJ1115.9+0129, MACSJ1206.2-0847, MACSJ1720.3+3536; Y fallback=none.
- exclude_bad Tx-M500: X fallback=none; Y fallback=Abell_0209, Abell_0068, Abell_0267, Abell_0383, Abell_0586, Abell_0611, Abell_2261, MACSJ0329.7-0211, MACSJ0429.6-0253, MACSJ0647.7+7015, MACSJ0744.9+3927, MACSJ1115.9+0129, MACSJ1206.2-0847, MACSJ1720.3+3536.
- exclude_bad Lx-Tx: X fallback=Abell_0209, Abell_0068, Abell_0267, Abell_0383, Abell_0586, Abell_0611, Abell_2261, MACSJ0329.7-0211, MACSJ0429.6-0253, MACSJ0647.7+7015, MACSJ0744.9+3927, MACSJ1115.9+0129, MACSJ1206.2-0847, MACSJ1720.3+3536; Y fallback=none.

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

## Assumptions

- M500 errors use per-cluster literature columns M500_err_lo/M500_err_hi.
- Lx errors from Lx_bol_err_lo/Lx_bol_err_hi; fallbacks are reported cluster-by-cluster.
- R500 uncertainties are propagated from M500 for aperture provenance only and are not added as independent linmix errors.
- All rows with status=done and positive M500/Y.
- Evolution exponent gamma is fixed to 2 for literature-style comparison.
- All logarithms are base 10.
- Rows with status != done or missing positive Y/M500 were excluded.
- Tx errors from Tx_err_lo/Tx_err_hi; fallbacks are reported cluster-by-cluster.
- Tx-M500 Y fallback 10% fractional 1-sigma used for: Abell_0209, Abell_0068, Abell_0267, Abell_0383, Abell_0586, Abell_0611, Abell_2261, MACSJ0329.7-0211, MACSJ0429.6-0253, MACSJ0647.7+7015, MACSJ0744.9+3927, MACSJ1115.9+0129, MACSJ1206.2-0847, MACSJ1720.3+3536.
- Evolution exponent gamma is fixed to 0.666667 for literature-style comparison.
- Tx errors from Tx_err_lo/Tx_err_hi.
- Lx-Tx X fallback 10% fractional 1-sigma used for: Abell_0209, Abell_0068, Abell_0267, Abell_0383, Abell_0586, Abell_0611, Abell_2261, MACSJ0329.7-0211, MACSJ0429.6-0253, MACSJ0647.7+7015, MACSJ0744.9+3927, MACSJ1115.9+0129, MACSJ1206.2-0847, MACSJ1720.3+3536.
- Evolution exponent gamma is fixed to 1 for literature-style comparison.
- Excludes rows with exclude_from_main_scaling=True in the canonical spectral table.
