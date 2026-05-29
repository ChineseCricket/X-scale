---
name: scaling-fitting
description: 标度关系拟合方法：linmix, BCES, Bayesian
provenance: llm-derived
---

# Scaling Relation Fitting Methods

## 标度关系形式

$$\ln Y = \ln A + B \ln(X/X_0) + C \ln E(z) + \epsilon$$

where $\epsilon \sim N(0, \sigma^2_{\text{int}} + \sigma^2_Y)$.

## 方法对比

### BCES (Akritas & Bershady 1996)
- 考虑双轴测量误差
- BCES(Y|X): 最小化 Y 方向残差
- BCES Orthogonal: 最小化正交残差
- 缺点: 不自然处理 intrinsic scatter 估计
- 使用者: [[pratt_2009]], [[maughan_2012]]

### linmix (Kelly 2007) — 本项目使用
- 贝叶斯方法，Gibbs sampler
- 同时估计斜率、截距、intrinsic scatter
- 处理双轴测量误差
- 比 BCES 更灵活: 可处理截断数据、非齐次误差
- 实现: `linmix` Python package
- 详见 [[kelly_2007]]

### Bayesian (full hierarchical)
- 同时拟合标度关系 + 选择函数 + 质量函数
- 最严格的方法
- 使用者: [[mantz_2010]], [[mantz_2016]], [[chiu_2022]]
- 本项目不使用（样本非 survey-selected）

## 本项目选择
- **linmix** (Kelly 2007): 适合小样本、有测量误差、需要 intrinsic scatter
- 样本 23 团，非 survey-selected，BCES 或 linmix 均可
- linmix 更好地处理 intrinsic scatter 估计

## 本项目实现

正式脚本为 `src/03_scaling/fit_scaling_relations.py`。拟合形式为：

`log10(Y / E(z)^gamma_fixed) = alpha + beta log10(X / X_pivot)`

- Lx-M500: `E(z)^-2 Lx_bol = A (M500 / 3e14 Msun)^beta`
- Tx-M500: `E(z)^(-2/3) Tx = A (M500 / 3e14 Msun)^beta`
- Lx-Tx: `E(z)^-1 Lx_bol = A (Tx / 5 keV)^beta`
- M500 使用弱透镜质量；M500 误差来自 `configs/m500_reference.csv`。
- R500 误差只作为 aperture provenance，由 M500 误差传播，不作为独立 linmix 误差。

主结果使用 `exclude_bad` 样本 N=18。Full-R500 是 canonical baseline；core-excised (`0.15-1.0 R500`) 是 literature-style comparison branch。

| Branch | Relation | beta | intrinsic scatter |
|---|---|---:|---:|
| full-R500 | Lx-M500 | 1.09 -0.48/+0.45 | 0.169 dex |
| full-R500 | Tx-M500 | 0.50 -0.27/+0.29 | 0.117 dex |
| full-R500 | Lx-Tx | 0.77 -0.44/+0.47 | 0.227 dex |
| core-excised | Lx-M500 | 1.15 -0.51/+0.54 | 0.186 dex |
| core-excised | Tx-M500 | 0.55 -0.34/+0.36 | 0.157 dex |
| core-excised | Lx-Tx | 0.69 -0.41/+0.40 | 0.245 dex |

Core-excised Tx confidence intervals are currently missing from the JSON products, so Tx-M500 and Lx-Tx use the documented 10% Tx fallback. This is acceptable for the current comparison because full-R500 and core-excised slopes agree within statistical uncertainty, but it must be stated in final methods.

## 相关概念
- [[scaling_relations]] — 观测结果对比
- [[spectral_fitting]] — T_X 和 L_X 的测量方法
- [[self_similar_model]] — self-similar 预言
