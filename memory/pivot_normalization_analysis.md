# Pivot / Normalization Point Analysis

Date: 2026-05-29

Context: after the first report update, a later `git pull --ff-only` fast-forwarded the repository from `4418b91` to `c470ef9`. The pulled server products backfilled native Sherpa core-excised `Tx` confidence intervals and refreshed the scaling outputs/figures. This note was rechecked against the updated products.

## Question

Do the `good_only` plots indicate that the fitting normalization point should be changed?

## Evidence from current products

The scaling script uses:

- `M500` pivot = `3e14 Msun` for `Lx-M500` and `Tx-M500`
- `Tx` pivot = `5 keV` for `Lx-Tx`

Current sample centers are substantially above those pivots:

| Branch/sample | N | geometric mean M500 | current M pivot | geometric mean Tx | current Tx pivot |
|---|---:|---:|---:|---:|---:|
| full `exclude_bad` | 18 | `8.37e14 Msun` | `3e14 Msun` | `8.69 keV` | `5 keV` |
| full `good_only` | 11 | `8.61e14 Msun` | `3e14 Msun` | `7.97 keV` | `5 keV` |
| core `exclude_bad` | 18 | `8.37e14 Msun` | `3e14 Msun` | `10.3 keV` | `5 keV` |
| core `good_only` | 6 | `9.92e14 Msun` | `3e14 Msun` | `8.70 keV` | `5 keV` |

The current `M500` pivot is therefore below the retained sample range: the full `exclude_bad` sample has `M500=4.17--15.65e14 Msun`, and the core `good_only` sample has `M500=6.85--12.45e14 Msun`.

The updated workflow notes also quantify the degeneracy for the `good_only` Lx-M500 fits:

- full-R500 `good_only` Lx-M500: posterior `corr(alpha, beta) = -0.975`
- core-excised `good_only` Lx-M500: posterior `corr(alpha, beta) = -0.997`

This is exactly the behavior expected when the intercept is evaluated far below the data cloud.

## Interpretation

Changing the pivot does not change the underlying fitted physical relation if the model is transformed consistently. In

`log10(Y / E(z)^gamma) = alpha + beta log10(X / X_pivot)`,

a different `X_pivot` mainly changes the reported intercept/normalization `alpha`. The slope `beta`, intrinsic scatter, residuals, and plotted line in physical units should remain equivalent apart from MCMC noise.

The `good_only` plots are therefore not evidence that the headline slopes need to change. They are evidence that the current normalization parameter is evaluated below the center of the data, especially for `M500` relations. This can make the intercept less intuitive and more correlated with slope, and it can visually make the fit feel anchored away from the data cloud.

After the server refresh, the numerical `good_only` slopes remain broad and sensitivity-oriented rather than headline results. The full-R500 `good_only` Lx-M500 slope is `0.55 -0.68/+0.68`; the core-excised `good_only` Lx-M500 slope is `2.58 -5.47/+8.48`. The very large core-excised uncertainty comes mostly from the six-cluster subsample size and the alpha-beta degeneracy, not from evidence that the physical normalization point must be changed for the baseline fit.

## Recommendation

For the current final report:

- Keep the existing `3e14 Msun` and `5 keV` pivots because the submitted products and figures are already generated consistently with them and the report emphasizes slopes/scatter rather than absolute normalization.
- State explicitly that the current normalization is a literature-style parameterization, not a physical claim about a cluster at the sample center.
- Do not reinterpret the `good_only` plots as requiring a new scientific conclusion.

For a future publication-style rerun on the server:

- Add an optional sample-centered pivot run, e.g. `M500_pivot = 8e14 Msun` or `1e15 Msun`, and `Tx_pivot = 8 keV`.
- Report the transformed normalization at the sample-centered pivot if normalization is scientifically discussed.
- Keep the original pivot results for comparison with existing products.
- Verify that slopes and scatter remain consistent within MCMC noise; if they do not, investigate sampling/convergence rather than the pivot itself.
