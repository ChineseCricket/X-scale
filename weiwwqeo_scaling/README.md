# Weiwwqeo Scaling Fits

Literature-style fixed-evolution scaling-relation fits using the updated 23-cluster spectral summary:

```text
Lx-M500c: E(z)^-2 Lx_bol = A (M500c / 3e14 Msun)^beta
Tx-M500c: E(z)^(-2/3) Tx = A (M500c / 3e14 Msun)^beta
```

Two samples are fit:

- `all`: all 23 fitted clusters.
- `exclude_bad`: excludes Abell_0750, MS2137-2353, and ZwCl_0857.9+2107.

Main comparison table:

- `products/scaling_linmix_fixed_evolution_comparison_summary.csv`

Quality classification:

- `products/scaling_quality_classification.csv`

Re-run from the repository root:

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python weiwwqeo_scaling/src/fit_scaling_relations.py
```
