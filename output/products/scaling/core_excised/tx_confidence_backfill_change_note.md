# Core-Excised Tx Confidence Backfill Change Note

Date: 2026-05-29

The 18 included core-excised clusters now use Sherpa `conf()` intervals for `icm_src.kT` instead of the documented 10% Tx fallback. The per-cluster best-fit `Tx_keV` values in `spectral_summary_core_excised.csv` are unchanged relative to the pre-backfill snapshot.

Exclude-bad comparison:

| Relation | Tx error treatment | Tx fallback count | alpha | beta | intrinsic scatter dex | observed RMS dex |
|---|---:|---:|---:|---:|---:|---:|
| Tx-M500 | 10% fallback | 18 Y | 0.714 -0.172/+0.155 | 0.550 -0.338/+0.359 | 0.157 -0.033/+0.043 | 0.146 |
| Tx-M500 | Sherpa `conf()` | 0 Y | 0.702 -0.142/+0.142 | 0.564 -0.306/+0.295 | 0.134 -0.030/+0.039 | 0.146 |
| Lx-Tx | 10% fallback | 18 X | 0.781 -0.138/+0.133 | 0.689 -0.411/+0.395 | 0.245 -0.041/+0.060 | 0.210 |
| Lx-Tx | Sherpa `conf()` | 0 X | 0.709 -0.139/+0.148 | 0.903 -0.427/+0.459 | 0.230 -0.038/+0.057 | 0.214 |

Interpretation: replacing the temporary 10% Tx fallback has a modest effect on Tx-M500 and a larger slope shift for Lx-Tx, but both remain broad-uncertainty core-excised fits. The main operational change is that the Tx uncertainty provenance is now native Sherpa confidence intervals for all 18 included clusters.
