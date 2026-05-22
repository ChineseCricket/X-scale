---
title: "CIAO: Chandra's Data Analysis System for X-Ray Astronomy and Beyond"
authors: [Fruscione, A., McDowell, J., Burke, D., Cresitello-Dittmar, M., Evans, I.N., Evans, J.D., Glotfelty, K., Günther, H.M., Huenemoerder, D., Joye, W., Lee, N.P., McLaughlin, W., Miller, J.B., Nynka, M., Principe, D.A., Siemiginowska, A.]
year: 2026
journal: "ApJ (submitted)"
arxiv: "2605.14144"
keywords: [CIAO, Chandra, software, Sherpa, spectral-fitting, data-reduction, X-ray]
provenance: source-derived
sample_size: null
redshift_range: null
mass_range: null
claims:
  - text: "CIAO 4.18 provides tools for calibration, spectral, imaging, and timing analysis in a unified framework"
    locator: "Abstract, sec.3"
    type: method_claim
  - text: "CIAO transitioned from S-Lang to Python in CIAO 4.0 (2008), integrating NumPy and Matplotlib"
    locator: "sec.2"
    type: "empirical_result"
  - text: "Sherpa supports forward-fitting with Bayesian inference via MCMC for Poisson-distributed X-ray data"
    locator: "sec.5"
    type: "method_claim"
  - text: "Sherpa incorporates XSPEC spectral models and supports 2D image modeling"
    locator: "sec.5"
    type: "method_claim"
  - text: "CIAO averages a few hundred papers per year citing it since 1999"
    locator: "sec.2, Figures 2-3"
    type: "empirical_result"
---

# Fruscione et al. (2026)

## One-line Summary
CIAO 4.18 的全面综述：25 年来 Chandra 数据分析系统的设计、演进和核心能力，包括 Sherpa 建模拟合、高级脚本、可视化和模拟工具。

## Sample
不适用（软件综述论文）。

## Key Results

### CIAO 架构
- 模块化设计：独立工具组合（事件筛选、光谱提取、源检测）
- 统一数据模型（data model + virtual file system），支持空间/光谱/时间维度的无缝切换
- 1999 年 CIAO 1.0 约 30 个工具 → 现在 100+ 工具 + 高级脚本

### Sherpa 建模与拟合 (sec.5)
- 开源 Python 建模拟合应用
- Forward-fitting + Bayesian inference（MCMC）
- 支持 XSPEC 光谱模型、2D 图像建模、时间序列分析
- 同时作为 CIAO 一部分和独立 Python 包发布

### 高级脚本 (sec.4)
- `chandra_repro`: 自动化数据重处理
- `specextract`: 光谱提取
- `srcflux`: 源光通量计算（复杂多步骤流程封装）
- `merge_obs`: 多观测合并

### 可视化 (sec.6)
- SAOImageDS9 集成
- ChIPS → Matplotlib 过渡

### 模拟工具 (sec.7)
- ChaRT (Chandra Ray Tracer)
- MARX (MIT Array of Residual X-rays)

## Key Equations
（软件综述，无标度关系公式）

## Methods
- 软件设计与开发方法论综述
- 版本历史：CIAO 1.0 (1999) → 4.0 (2008, Python) → 4.18 (2026, conda)
- Science Acceptance Testing：单元测试 + 回归测试 + 发布测试

## Relations to Other Work
- [[spectral_fitting]] — Sherpa 是本项目光谱拟合使用的工具
- [[kelly_2007]] — linmix 方法在 Sherpa/Python 生态中使用
