---
title: "Galaxy cluster X-ray luminosity scaling relations from a representative local sample (REXCESS)"
authors: [Pratt, G.W., Croston, J.H., Arnaud, M., Böhringer, H.]
year: 2009
journal: "A&A, 498, 361"
arxiv: "0809.3784"
keywords: [scaling-relations, luminosity, REXCESS, XMM-Newton, galaxy-clusters]
provenance: source-derived
claims:
  - text: "LX-TX slope α≈2.08 (BCES orthogonal, bolometric), steeper than self-similar"
    locator: "Table 2"
    type: empirical_result
  - text: "Intrinsic scatter σ_ln≈0.40 (raw), reduced >2x with core-excised"
    locator: "Table 2, sec.4.3"
    type: empirical_result
  - text: "Cool core and disturbed systems occupy different regions in residual space"
    locator: "sec.4.3"
    type: physical_insight
  - text: "LX-YX slope steeper than self-similar (9/5)"
    locator: "sec.4.2"
    type: empirical_result
sample_size: 31
redshift_range: [0.02, 0.18]
mass_range: ["1e14", "1e15"]
---

# Pratt et al. (2009)

## One-line Summary
REXCESS 样本 31 个近邻团的 X 射线光度标度关系，发现 Lx 斜率显著陡于 self-similar，scatter 主导因素是 cool core。

## Sample
31 个近邻星系团（z < 0.2），从 REFLEX 目录按 X 光光度选取，优化采样光度函数。温度范围 2-9 keV。无形态学偏置。XMM-Newton 统一观测。

## Key Results

### L_X - T_X
- Slope: $\alpha \approx 2.08$ (BCES orthogonal, bolometric, R<R500, Table 2)
- 显著陡于 self-similar 预期 ($\alpha_{SS} = 2$)
- Intrinsic scatter: $\sigma_{\ln} \approx 0.40$ (raw)

### L_X - Y_X
- Slope: 陡于 self-similar 预期 ($\alpha_{SS} = 9/5$)
- Intrinsic scatter: $\sigma_{\ln} \approx 0.40$

### L_X - M_500
- From YX→M proxy (Malmquist bias corrected, Appendix B)
- Intrinsic scatter 同 L-YX（M 由 YX 导出）

### Core-excised (r > 0.15R500)
- Scatter 降低 > 2 倍
- Cool core 和 disturbed 系统在残差空间占据不同区域

## Key Equations
$$h(z)^n L = C (A/A_0)^\alpha$$
where $n=-1$ for T, $n=-9/5$ for $Y_X$, $n=-7/3$ for M. Fitted with BCES (Y|X) and BCES orthogonal.

## Methods
- Instrument: XMM-Newton
- Energy band: bolometric (0.01–100 keV)，从 [0.3–2] keV 表面亮度 + 光谱模型转换
- R500: iterative from M500-YX (Arnaud+07)
- Fitting: BCES (Akritas & Bershady 1996)
- No core-excised temperature (focus on luminosity scaling)

## Relations to Other Work
- [[arnaud_2007]] — YX-M500 校准用于估计 R500
- [[arnaud_2005]] — 同一团队早期 M-T 工作
- [[mantz_2010]] — 对比 Lx-M scatter（Mantz 发现 ce scatter <10%）
- [[maughan_2008]] — 115 Chandra 团对比
