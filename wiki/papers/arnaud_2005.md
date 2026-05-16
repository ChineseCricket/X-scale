---
title: "The structural and scaling properties of nearby galaxy clusters II. The M-T relation"
authors: [Arnaud, M., Pointecouteau, E., Pratt, G.W.]
year: 2005
journal: "A&A, 441, 893"
arxiv: "astro-ph/0502210"
keywords: [scaling-relations, M-T, REXCESS-precursor, XMM-Newton, galaxy-clusters]
sample_size: 10
redshift_range: [0.02, 0.15]
mass_range: ["~2e14", "~1e15"]
---

# Arnaud et al. (2005)

## One-line Summary
10 个 relaxed 近邻团的 M-T 关系，hot 团 (kT>3.5keV) 斜率符合 self-similar (1.5)，但归一化偏低 ~30%。

## Sample
10 个近邻 relaxed 团 (z < 0.15)，温度 2–9 keV。XMM-Newton 精确测量。NFW 拟合质量轮廓（HSE 假设）。

## Key Results

### M_500 - T_X
- Hot subsample (kT > 3.5 keV): $\alpha = 1.49 \pm 0.15$ — consistent with self-similar ($3/2$)
- All sample: $\alpha = 1.71 \pm 0.09$ — steeper than self-similar
- 斜率在所有密度对比度 (δ=2500,1000,500,200) 相同（反映质量轮廓 self-similarity）
- Normalization: 比纯引力模型预言低 ~30%，与含 radiative cooling + feedback 的模型更一致

## Key Equations
$$M_\delta = C_\delta \left(\frac{T}{5 \text{ keV}}\right)^\alpha$$
Fitted in log-log space.

## Methods
- Instrument: XMM-Newton
- Mass: NFW fit to HSE mass profiles, measured down to δ ≥ 1000
- T: isothermal fit in [0.1–0.5]R200 aperture
- Fitting: BCES (or similar regression with errors)

## Relations to Other Work
- [[arnaud_2007]] — 同团队后续 M500-YX 工作
- [[pratt_2009]] — 同一样本扩展到 Lx scaling
- [[mantz_2010]] — 大样本验证
