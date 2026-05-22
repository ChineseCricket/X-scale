---
title: "Chandra Cluster Cosmology Project III: Cosmological Parameter Constraints"
authors: [Vikhlinin, A., Kravtsov, A., Burenin, R.A., Ebeling, H., Forman, W.R., Hornstrup, A., Jones, C., Murray, S.S., Nagai, D., Quintana, H., Voevodkin, A.]
year: 2009
journal: "ApJ, 692, 1060"
arxiv: "0812.2720"
keywords: [scaling-relations, cosmology, Chandra, CCCP, mass-function]
provenance: source-derived
claims:
  - text: "Cosmological constraints: w0=-1.14±0.21, ΩM=0.255±0.043"
    locator: "sec.5"
    type: empirical_result
  - text: "LX-M slope ~1.61±0.14 (bolometric, CCCP Paper II)"
    locator: "Paper II"
    type: empirical_result
  - text: "TX-M slope ~1.5–1.6"
    locator: "Paper II"
    type: empirical_result
  - text: "LX-M slope uncertainty is dominant systematic for ΩM"
    locator: "sec.6"
    type: physical_insight
sample_size: 86
redshift_range: [0.0, 0.9]
mass_range: ["~3e14", "~2e15"]
---

# Vikhlinin et al. (2009) — CCCP III

## One-line Summary
Chandra Cluster Cosmology Project: 利用 86 个团的质量函数演化限制暗能量。Lx-M relation 是主要系统误差来源。

## Sample
86 个团：49 个低 z (z≈0.05, BCS) + 37 个高 z (z≈0.55, 400d survey)。Chandra 观测。

## Key Results

### Cosmological constraints
- $w_0 = -1.14 \pm 0.21$ (cluster only)
- $\Omega_M = 0.255 \pm 0.043$
- $\sigma_8(\Omega_M/0.25)^{0.47} = 0.813 \pm 0.013 \pm 0.024$

### Scaling relations (detailed in Paper II, ApJ 692, 1033)
- Lx-M slope ~1.61 ± 0.14 (bolometric)
- Tx-M slope ~1.5–1.6
- Evolution consistent with self-similar
- Lx-M slope uncertainty is dominant systematic for $\Omega_M$

## Key Equations
$$L \propto M^{B_{LM}} E(z)^{2/3+\gamma}$$
Self-similar: $B_{LM} = 4/3$, $\gamma = 0$.

## Methods
- Instrument: Chandra
- Mass: HSE from Chandra X-ray observations (Paper II)
- Fitting: BCES regression + MCMC for cosmology
- Energy band: bolometric

## Relations to Other Work
- [[mantz_2010]] — 类似方法（ROSAT survey + Chandra follow-up）
- [[mantz_2016]] — WL mass 校准版本
- [[pratt_2009]] — REXCESS Lx scaling 对比
