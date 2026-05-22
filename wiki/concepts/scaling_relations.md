---
name: scaling-relations
description: Galaxy Cluster 标度关系理论综述 + 各文献结果对比
provenance: llm-derived
---

# Galaxy Cluster X-ray Scaling Relations

## Self-similar Model 预言

在 self-similar model 假设下（Kaiser 1986），引力主导的星系团遵循简单标度关系：

### T_X - M_500
$$E(z)^{2/3} \left(\frac{kT}{\text{keV}}\right) = A_{TM} \left(\frac{M_{500}}{5\times10^{14} M_\odot}\right)^{2/3}$$

- Self-similar 斜率: $\beta_{TM} = 2/3$（即 $T \propto M^{2/3}$ 或 $M \propto T^{3/2}$）
- Pivot mass $M_{\text{piv}} = 5 \times 10^{14} M_\odot$

### L_X - M_500
$$E(z)^{-7/3} \left(\frac{L_X}{10^{44}\text{erg/s}}\right) = A_{LM} \left(\frac{M_{500}}{M_{\text{piv}}}\right)^{4/3}$$

- Self-similar 斜率: $\beta_{LM} = 4/3$（即 $L \propto M^{4/3}$）
- 实际观测斜率通常更陡，因为非引力过程（AGN feedback, radiative cooling）影响光度

## 各文献 T_X-M_500 结果对比

| 文献 | 样本 | 仪器 | 拟合方法 | $M_{500}$ 方法 | 斜率 $M \propto T^\alpha$ | Self-similar? | 备注 |
|------|------|------|----------|---------------|--------------------------|---------------|------|
| [[arnaud_2005]] | 10 relaxed, z<0.15 | XMM | BCES | HSE | $1.49\pm0.15$ (hot), $1.71\pm0.09$ (all) | hot: Y; all: steeper | δ=500; low-z relaxed |
| [[mantz_2010]] | 238, z~0-0.5 | Chandra | Bayesian | HSE (fgas) | ~1.5 (from Paper I) | ~consistent | focus on Lx-M |
| [[mantz_2016]] | 224, z~0-0.5 | Chandra | Bayesian | Weak lensing | ~1.5 | ~consistent | WL calibrated |
| [[vikhlinin_2009]] | 86, z~0-0.9 | Chandra | BCES | HSE | ~1.53 | ~consistent | CCCP Paper II |
| [[pratt_2009]] | 31, z<0.2 | XMM | BCES | YX proxy | — | — | focus on Lx |
| [[maughan_2012]] | 114, 0.1<z<1.3 | Chandra | BCES | — | — | — | Lx-T relation |

## 各文献 L_X-M_500 结果对比

| 文献 | 能段 | Core-excised? | 斜率 $\beta_{LM}$ | Scatter (ln) | 备注 |
|------|------|---------------|-------------------|--------------|------|
| [[pratt_2009]] | bolometric | No | ~2.08 (>>4/3) | ~0.40 raw, ~0.20 ce | YX→M proxy; steep due to fgas |
| [[mantz_2010]] | 0.1-2.4 keV | Yes (0.15r500) | 1.33±0.08 | <10% ce | remarkably low scatter |
| [[mantz_2016]] | 0.1-2.4 keV | Yes (0.15r500) | ~1.3 | ~10% ce | WL calibrated |
| [[vikhlinin_2009]] | bolometric | Yes | ~1.61 | ~20% | CCCP Paper II |
| [[maughan_2008]] | 0.5-2 keV | Both | — | — | 115 clusters Chandra archive |
| [[maughan_2012]] | 0.5-2 keV | Both | SS (relaxed+ce), steeper (disturbed) | — | Lx-T relation |
| [[sun_2009]] | 0.5-2 keV | — | — | — | 43 groups |
| [[arnaud_2007]] | — | — | — | — | M500-YX calibration |
| [[chiu_2022]] | soft | Yes | — | — | eFEDS+HSC WL |
| [[ramos_ceja_2025]] | 0.2-2.3 keV | No | — | — | eRASS1 3061 clusters |

**Note**: 部分论文具体斜率数值待精读补全（标注"~"的为近似值）。核心论文 (Pratt+09, Mantz+10, Arnaud+05) 数值已确认。

## 关键物理

- **E(z) 因子**: 宇宙学演化修正，$E(z) = H(z)/H_0 = \sqrt{\Omega_m(1+z)^3 + \Omega_\Lambda}$
- **Core-excised T_X**: 去除 0.15R_500 内的 cool-core 区域，减少非引力过程的影响（scatter 降低 2x+）
- **Intrinsic scatter**: T_X ~10-15%, L_X ~30-40% (raw), ~10-20% (core-excised)
- **Steep Lx-M slope**: 主因是 gas fraction 随质量变化，非结构差异

## 与本项目的关键对比

本项目方法 vs 文献最佳实践：
- **T_X**: full R500 + core-excised (0.15R500-R500) — 与 Mantz+10/16 方法一致
- **L_X**: model-derived (从 Sherpa APEC normalization) — 与 Mantz+10 方法类似
- **拟合**: linmix (Kelly 2007) — 与 BCES 同属考虑测量误差的方法
- **M500**: 弱透镜（CLASH: Umetsu+16, LoCuSS: Okabe+16）— 与 WtG 系列类似

## 相关概念
- [[self_similar_model]] — self-similar model 的详细推导
- [[spectral_fitting]] — 光谱拟合方法
- [[scaling_fitting]] — 标度关系拟合方法
- [[clash_survey]] — CLASH M500 来源
- [[locuss_survey]] — LoCuSS M500 来源
- [[kelly_2007]] — linmix 方法原文
