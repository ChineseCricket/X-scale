---
title: "Weighing the Giants V: Galaxy Cluster Scaling Relations"
authors: [Mantz, A.B., Allen, S.W., Morris, R.G., von der Linden, A., Applegate, D.E., Kelly, P.L., Burke, D.L., Donovan, D., Ebeling, H.]
year: 2016
journal: "MNRAS, 463, 3582"
arxiv: "1606.03407"
keywords: [scaling-relations, Lx-M, Tx-M, weak-lensing, Chandra, Weighing-the-Giants]
provenance: source-derived
claims:
  - text: "Core-excised LX-M scatter ~10%, consistent with Mantz+10"
    locator: "sec.5"
    type: empirical_result
  - text: "LX and TX intrinsic scatter positively correlated, related to dynamical state"
    locator: "sec.5.3"
    type: physical_insight
  - text: "LX scatter decreases with redshift (cool core evolution)"
    locator: "sec.5.2"
    type: empirical_result
  - text: "Planck Y-M relation inconsistent with lensing inference"
    locator: "sec.6"
    type: empirical_result
sample_size: 224
redshift_range: [0.0, 0.5]
mass_range: ["~2e14", "~2e15"]
---

# Mantz et al. (2016) — WtG V

## One-line Summary
首个同时考虑选择效应 + 弱透镜质量校准的 scaling relation 分析。Lx 和 Tx 的 intrinsic scatter 在固定质量下正相关，与团簇动力学状态有关。

## Sample
224 个团（139 有 Chandra 跟踪），来自 BCS/REFLEX/MACS。弱透镜质量来自 WtG I-III (CFHTLenS/HSC)。z~0–0.5。

## Key Results

### L_X - M_500
- Core-excised (0.15r500–r500) Lx-M scatter: ~10%
- Slope consistent with Mantz+10 (~1.3)
- Evolution consistent with self-similar
- Lx scatter 随红移减小（cool core 发展）

### T_X - M_500
- Scatter: ~10–15%
- T scatter 随红移增加（merger rate 变化）
- Slope consistent with previous studies

### Key new findings
- Lx 和 Tx 的 intrinsic scatter 正相关 → 与动力学状态相关
- Core-excised Lx 仍是最低 scatter 代理之一
- Planck Y-M relation 与 lensing 推断不一致

## Methods
- Instruments: Chandra (X-ray) + CFHTLenS/HSC (weak lensing)
- Mass: weak lensing (WtG I-III) — first direct lensing calibration of scaling relations with selection
- Fitting: Bayesian, simultaneously fitting scaling relations + mass function + lensing data
- Core-excised: 0.15r500–r500 for T, L in 0.1–2.4 keV
- Energy band: 0.1–2.4 keV

## Relations to Other Work
- [[mantz_2010]] — 前作（HSE mass）
- [[pratt_2009]] — REXCESS 对比
- [[vikhlinin_2009]] — CCCP 对比
- [[chiu_2022]] — eFEDS 弱透镜校准
