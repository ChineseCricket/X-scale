---
title: "The observed growth of massive galaxy clusters – II. X-ray scaling relations"
authors: [Mantz, A., Allen, S.W., Ebeling, H., Rapetti, D., Drlica-Wagner, A.]
year: 2010
journal: "MNRAS, 406, 1773"
arxiv: "0909.3099"
keywords: [scaling-relations, Lx-M, Tx-M, Chandra, core-excised, low-scatter]
sample_size: 238
redshift_range: [0.0, 0.5]
mass_range: ["~3e14", "~2e15"]
---

# Mantz et al. (2010)

## One-line Summary
238 个大质量团的 X 射线标度关系。Centre-excised Lx-M scatter <10%，是最低 scatter 质量代理之一。核心加热限于 r<0.15r500。

## Sample
238 个 X 射线流量限制选取的大质量团，来自 BCS (78), REFLEX (126), bright-MACS (34)。z~0–0.5。Chandra 跟踪观测。

## Key Results

### L_X - M_500 (core-excised, 0.15r500–r500)
- Slope: $B_{LM} = 1.33 \pm 0.08$ (Table 7/8)
- Intrinsic scatter: **<10%** (centre-excised) — remarkably low
- 能段: 0.1–2.4 keV (ROSAT band)
- Evolution: consistent with self-similar

### L_X - M_500 (core-included)
- Scatter 显著更大（cool core 影响）
- Slope 更陡

### T_X - M_500
- Intrinsic scatter: 10–15%
- Slope: consistent with or slightly steeper than self-similar

### Y_X - M_500
- Scatter: ~10–15%

### Key finding
- 非引力加热（AGN feedback）主要影响核心 (r < 0.15r500)
- Core-excised Lx 是比 TX 或 YX scatter 更低的质量代理

## Key Equations
$$E(z)^\gamma L = A \left(\frac{M_{500}}{M_{\text{piv}}}\right)^B$$
Power-law with self-similar evolution ($\gamma = -7/3$ for Lx-M).

## Methods
- Instrument: Chandra (follow-up) + ROSAT (survey)
- Spectra: 0.15–1 r500 annulus for T_X, ce; 0.1–2.4 keV for L
- Mass: f_gas method (HSE), cross-calibrated ROSAT/Chandra
- Fitting: Bayesian, simultaneously accounting for selection + mass function
- Core-excised: 0.15r500–r500

## Relations to Other Work
- [[mantz_2016]] — WtG V 弱透镜校准更新
- [[pratt_2009]] — REXCESS 对比
- [[vikhlinin_2009]] — CCCP 对比
