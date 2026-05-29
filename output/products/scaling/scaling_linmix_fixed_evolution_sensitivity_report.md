# Leave-One-Out Sensitivity Fits

Input: `output/products/spectral/spectral_summary.csv`

Base sample is `exclude_bad`. Each row removes one retained high/suspect cluster and refits the same fixed-evolution linmix model.

| Left-out cluster | Relation | N | beta | delta beta | intrinsic scatter (dex) | delta scatter |
|---|---|---:|---:|---:|---:|---:|
| Abell_0068 | Lx-M500 | 17 | 1.056 -0.499/+0.514 | -0.029 | 0.177 -0.040/+0.061 | +0.008 |
| Abell_0068 | Tx-M500 | 17 | 0.549 -0.248/+0.264 | +0.071 | 0.108 -0.025/+0.031 | -0.008 |
| Abell_0068 | Lx-Tx | 17 | 0.864 -0.445/+0.429 | +0.104 | 0.226 -0.042/+0.054 | -0.000 |
| Abell_0611 | Lx-M500 | 17 | 1.059 -0.471/+0.419 | -0.025 | 0.171 -0.042/+0.054 | +0.002 |
| Abell_0611 | Tx-M500 | 17 | 0.451 -0.232/+0.234 | -0.027 | 0.112 -0.025/+0.030 | -0.005 |
| Abell_0611 | Lx-Tx | 17 | 0.993 -0.429/+0.475 | +0.234 | 0.218 -0.038/+0.055 | -0.009 |
| MACSJ0647.7+7015 | Lx-M500 | 17 | 1.105 -0.501/+0.460 | +0.021 | 0.170 -0.044/+0.056 | +0.000 |
| MACSJ0647.7+7015 | Tx-M500 | 17 | 0.456 -0.234/+0.268 | -0.022 | 0.109 -0.025/+0.031 | -0.008 |
| MACSJ0647.7+7015 | Lx-Tx | 17 | 0.833 -0.539/+0.531 | +0.074 | 0.235 -0.042/+0.056 | +0.008 |
| MACSJ1206.2-0847 | Lx-M500 | 17 | 0.980 -0.559/+0.513 | -0.105 | 0.175 -0.045/+0.054 | +0.006 |
| MACSJ1206.2-0847 | Tx-M500 | 17 | 0.447 -0.283/+0.299 | -0.031 | 0.122 -0.027/+0.033 | +0.006 |
| MACSJ1206.2-0847 | Lx-Tx | 17 | 0.690 -0.439/+0.458 | -0.069 | 0.225 -0.036/+0.053 | -0.002 |

## Notes

- Positive delta beta/scatter means the leave-one-out fit is higher than the base exclude_bad fit.
- Clusters absent from the base exclude_bad relation are skipped.
