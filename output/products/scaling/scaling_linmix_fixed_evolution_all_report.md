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
| all | Lx-M500 | 23 | good:11, acceptable:4, high:3, bad:5 | 0.732 -0.170/+0.160 | 1.203 -0.332/+0.352 | 2.000 -0.000/+0.000 | 0.173 -0.036/+0.041 | 0.217 | 1.333/2.000 |
| all | Tx-M500 | 23 | good:11, acceptable:4, high:3, bad:5 | 0.691 -0.204/+0.209 | 0.583 -0.426/+0.436 | 0.667 -0.000/+0.000 | 0.289 -0.047/+0.056 | 0.260 | 0.667/0.667 |
| all | Lx-Tx | 23 | good:11, acceptable:4, high:3, bad:5 | 1.190 -0.076/+0.083 | 0.520 -0.174/+0.190 | 1.000 -0.000/+0.000 | 0.245 -0.035/+0.046 | 0.219 | 2.000/1.000 |

## Figures

- `output/figures/scaling/lx_m500_linmix_all.png`
- `output/figures/scaling/lx_m500_linmix_all.pdf`
- `output/figures/scaling/tx_m500_linmix_all.png`
- `output/figures/scaling/tx_m500_linmix_all.pdf`
- `output/figures/scaling/lx_tx_linmix_all.png`
- `output/figures/scaling/lx_tx_linmix_all.pdf`
- `output/figures/scaling/m500_tx_literature_style_all.png`
- `output/figures/scaling/m500_tx_literature_style_all.pdf`

## Uncertainty Provenance

- M500 errors come from `M500_err_lo/M500_err_hi` in the canonical spectral table.
- Tx errors come from `Tx_err_lo/Tx_err_hi` and are used as Y errors for Tx-M500 or X errors for Lx-Tx.
- R500 errors are propagated from M500 and documented as aperture provenance; they are not included as independent linmix errors.
- Lx errors come from `Lx_bol_err_lo/Lx_bol_err_hi`; missing values fall back only where reported below.
- all Lx-M500: X fallback=none; Y fallback=Abell_0697, Abell_0750, MS2137-2353, RXJ1347.5-1145.
- all Tx-M500: X fallback=none; Y fallback=Abell_0750, MS2137-2353.
- all Lx-Tx: X fallback=Abell_0750, MS2137-2353; Y fallback=Abell_0697, Abell_0750, MS2137-2353, RXJ1347.5-1145.

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
- All rows with status=done and positive M500/Y.
- Lx-M500 Y fallback 10% fractional 1-sigma used for: Abell_0697, Abell_0750, MS2137-2353, RXJ1347.5-1145.
- Evolution exponent gamma is fixed to 2 for literature-style comparison.
- All logarithms are base 10.
- Rows with status != done or missing positive Y/M500 were excluded.
- Tx errors from Tx_err_lo/Tx_err_hi; fallbacks are reported cluster-by-cluster.
- Tx-M500 Y fallback 10% fractional 1-sigma used for: Abell_0750, MS2137-2353.
- Evolution exponent gamma is fixed to 0.666667 for literature-style comparison.
- Tx errors from Tx_err_lo/Tx_err_hi.
- Lx-Tx X fallback 10% fractional 1-sigma used for: Abell_0750, MS2137-2353.
- Lx-Tx Y fallback 10% fractional 1-sigma used for: Abell_0697, Abell_0750, MS2137-2353, RXJ1347.5-1145.
- Evolution exponent gamma is fixed to 1 for literature-style comparison.
