---
name: scaling-fitting
description: 标度关系拟合方法：linmix, BCES, Bayesian
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

## 相关概念
- [[scaling_relations]] — 观测结果对比
- [[spectral_fitting]] — T_X 和 L_X 的测量方法
- [[self_similar_model]] — self-similar 预言
