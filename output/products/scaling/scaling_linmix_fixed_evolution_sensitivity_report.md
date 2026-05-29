# Leave-One-Out Sensitivity Fits

Input: `output/products/spectral/spectral_summary.csv`

Base sample is `exclude_bad`. Each row removes one retained high/suspect cluster and refits the same fixed-evolution linmix model.

| Left-out cluster | Relation | N | beta | delta beta | intrinsic scatter (dex) | delta scatter |
|---|---|---:|---:|---:|---:|---:|
| Abell_0068 | Lx-M500 | 17 | 1.002 -0.441/+0.467 | -0.079 | 0.181 -0.044/+0.055 | +0.011 |
| Abell_0068 | Tx-M500 | 17 | 0.557 -0.237/+0.281 | +0.061 | 0.108 -0.025/+0.032 | -0.009 |
| Abell_0068 | Lx-Tx | 17 | 0.855 -0.444/+0.442 | +0.089 | 0.224 -0.038/+0.052 | -0.003 |
| Abell_0611 | Lx-M500 | 17 | 1.017 -0.402/+0.526 | -0.064 | 0.177 -0.048/+0.051 | +0.007 |
| Abell_0611 | Tx-M500 | 17 | 0.461 -0.242/+0.268 | -0.036 | 0.116 -0.026/+0.031 | -0.002 |
| Abell_0611 | Lx-Tx | 17 | 0.980 -0.456/+0.475 | +0.214 | 0.213 -0.038/+0.054 | -0.014 |
| MACSJ0647.7+7015 | Lx-M500 | 17 | 1.018 -0.435/+0.482 | -0.063 | 0.179 -0.042/+0.056 | +0.009 |
| MACSJ0647.7+7015 | Tx-M500 | 17 | 0.450 -0.249/+0.256 | -0.046 | 0.109 -0.022/+0.030 | -0.008 |
| MACSJ0647.7+7015 | Lx-Tx | 17 | 0.839 -0.556/+0.516 | +0.073 | 0.236 -0.041/+0.055 | +0.009 |
| MACSJ1206.2-0847 | Lx-M500 | 17 | 0.969 -0.444/+0.490 | -0.112 | 0.173 -0.044/+0.054 | +0.003 |
| MACSJ1206.2-0847 | Tx-M500 | 17 | 0.431 -0.275/+0.311 | -0.066 | 0.122 -0.026/+0.033 | +0.004 |
| MACSJ1206.2-0847 | Lx-Tx | 17 | 0.616 -0.441/+0.488 | -0.150 | 0.229 -0.040/+0.057 | +0.002 |

## Notes

- Positive delta beta/scatter means the leave-one-out fit is higher than the base exclude_bad fit.
- Clusters absent from the base exclude_bad relation are skipped.
