# Leave-One-Out Sensitivity Fits

Input: `output/products/spectral/spectral_summary.csv`

Base sample is `exclude_bad`. Each row removes one retained high/suspect cluster and refits the same fixed-evolution linmix model.

| Left-out cluster | Relation | N | beta | delta beta | intrinsic scatter (dex) | delta scatter |
|---|---|---:|---:|---:|---:|---:|
| Abell_0068 | Lx-M500 | 17 | 1.001 -0.495/+0.530 | -0.089 | 0.186 -0.046/+0.050 | +0.021 |
| Abell_0068 | Tx-M500 | 17 | 0.525 -0.253/+0.263 | +0.020 | 0.110 -0.023/+0.034 | -0.006 |
| Abell_0068 | Lx-Tx | 17 | 0.903 -0.494/+0.439 | +0.134 | 0.228 -0.038/+0.058 | +0.001 |
| Abell_0611 | Lx-M500 | 17 | 1.046 -0.440/+0.444 | -0.044 | 0.173 -0.045/+0.054 | +0.008 |
| Abell_0611 | Tx-M500 | 17 | 0.452 -0.235/+0.254 | -0.053 | 0.112 -0.024/+0.034 | -0.004 |
| Abell_0611 | Lx-Tx | 17 | 0.950 -0.471/+0.454 | +0.181 | 0.215 -0.038/+0.056 | -0.011 |
| MACSJ0647.7+7015 | Lx-M500 | 17 | 1.005 -0.420/+0.463 | -0.085 | 0.181 -0.044/+0.055 | +0.016 |
| MACSJ0647.7+7015 | Tx-M500 | 17 | 0.452 -0.238/+0.249 | -0.053 | 0.107 -0.023/+0.032 | -0.008 |
| MACSJ0647.7+7015 | Lx-Tx | 17 | 0.845 -0.494/+0.490 | +0.076 | 0.234 -0.042/+0.052 | +0.007 |
| MACSJ1206.2-0847 | Lx-M500 | 17 | 0.964 -0.446/+0.507 | -0.126 | 0.175 -0.041/+0.049 | +0.010 |
| MACSJ1206.2-0847 | Tx-M500 | 17 | 0.456 -0.317/+0.297 | -0.049 | 0.122 -0.026/+0.033 | +0.007 |
| MACSJ1206.2-0847 | Lx-Tx | 17 | 0.685 -0.479/+0.426 | -0.084 | 0.230 -0.041/+0.051 | +0.003 |

## Notes

- Positive delta beta/scatter means the leave-one-out fit is higher than the base exclude_bad fit.
- Clusters absent from the base exclude_bad relation are skipped.
