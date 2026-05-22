---
title: "Some Aspects of Measurement Error in Linear Regression of Astronomical Data"
authors: [Kelly, B.C.]
year: 2007
journal: "ApJ, 665, 1489"
arxiv: "0711.2455"
keywords: [methods, linmix, linear-regression, measurement-error, Bayesian]
provenance: source-derived
claims:
  - text: "Bayesian method (linmix) for fitting linear relations with measurement errors"
    locator: "sec.2"
    type: method_claim
  - text: "Simultaneously estimates slope, intercept, and intrinsic scatter"
    locator: "sec.2"
    type: method_claim
  - text: "More flexible than BCES (Akritas & Bershady 1996)"
    locator: "sec.3"
    type: method_claim
sample_size: null
redshift_range: null
mass_range: null
---

# Kelly (2007)

## One-line Summary
**linmix 方法原文。** 贝叶斯线性回归方法，处理天文数据中的测量误差和 intrinsic scatter。本项目使用 linmix 拟合标度关系。

## Key Results
- 提出贝叶斯方法拟合含测量误差的线性关系
- 同时估计斜率、截距、intrinsic scatter
- 比 BCES (Akritas & Bershady 1996) 更灵活
- 使用 Gibbs sampler / MCMC

## Key Equations
$$y_i = \alpha + \beta x_i + \epsilon_i$$
where $\epsilon_i \sim N(0, \sigma^2_{\text{int}} + \sigma^2_{y,i})$, and $x_i$ has measurement error $\sigma_{x,i}$.

## Methods
- Bayesian hierarchical model
- MCMC (Gibbs sampler)
- Accounts for: measurement errors on both axes, intrinsic scatter, censored data

## Relations to Other Work
- [[pratt_2009]] — BCES 方法对比
- [[mantz_2010]] — Bayesian 标度关系拟合
