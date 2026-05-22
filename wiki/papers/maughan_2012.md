---
title: "Self-similar scaling and evolution in the galaxy cluster X-ray Luminosity-Temperature relation"
authors: [Maughan, B.J., Giles, P.A., Randall, S.W., Jones, C., Forman, W.R.]
year: 2012
journal: "MNRAS, 421, 1583"
arxiv: "1108.1200"
keywords: [scaling-relations, Lx-T, Chandra, self-similar, evolution, galaxy-clusters]
provenance: source-derived
claims:
  - text: "Relaxed + core-excised LX-T slope consistent with self-similar (α≈2)"
    locator: "sec.4"
    type: empirical_result
  - text: "Disturbed/non-cool-core LX-T slope significantly steeper than self-similar"
    locator: "sec.4"
    type: empirical_result
  - text: "Self-similar behavior breaks down below ~3.5 keV"
    locator: "sec.5"
    type: physical_insight
  - text: "Cool core fraction decreases at z>0.5"
    locator: "sec.5"
    type: empirical_result
sample_size: 114
redshift_range: [0.1, 1.3]
mass_range: ["~5e13", "~1e15"]
---

# Maughan et al. (2012)

## One-line Summary
114 个 Chandra 团的 Lx-T 关系。Relaxed 团 core-excised 后斜率符合 self-similar；disturbed 团斜率显著更陡。

## Sample
114 个 Chandra 观测团 (0.1 < z < 1.3)，同 Maughan+08 样本。按形态/cool core 分子样本。

## Key Results

### L_X - T_X
- Relaxed + core-excised: slope consistent with self-similar ($\alpha \approx 2$)
- Disturbed / non-cool-core: slope significantly steeper than self-similar
- 与 REXCESS 对比：self-similar 行为在 ~3.5 keV 以下 break down
- Gas density profiles: relaxed 团在核外 self-similar

### Evolution
- 数据表面不符合 self-similar evolution
- 但可被 selection bias 解释 → 不排除 self-similar evolution
- Cool core fraction 在 z > 0.5 减少

## Methods
- Instrument: Chandra
- Core-excised: r > 0.15R500
- Fitting: BCES
- 子样本: relaxed vs disturbed; cool core vs non-cool-core

## Relations to Other Work
- [[maughan_2008]] — 同一样本的结构性质
- [[pratt_2009]] — REXCESS 低质量端对比
- [[mantz_2010]] — 大样本 ce-Lx-M
