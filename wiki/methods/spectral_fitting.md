---
name: spectral-fitting
description: X-ray 光谱拟合方法：APEC + WSTAT + Sherpa
---

# Spectral Fitting Methods

## 本项目方法

### 模型: absorbed APEC + WSTAT
- **APEC**: Astrophysical Plasma Emission Code，描述热等离子体发射谱
  - 参数: kT (温度), Abundance (金属丰度), Redshift, Normalization
  - Normalization: $\text{norm} = \frac{10^{-14}}{4\pi [D_A(1+z)]^2} \int n_e n_H dV$
- **WSTAT** (Wstat / CSTAT): Poisson likelihood-based background modeling
  - 不需要单独拟合背景谱
  - 直接建模源+背景的 Poisson 统计
  - 适合低计数光谱
- **Absorption**: phabs (Galactic NH, fixed from config)

### 流程
1. `specextract` (CIAO) 逐 ObsID 提取光谱 + ARF + RMF
2. Sherpa 联合拟合多 ObsID 光谱
3. Full R500 aperture + core-excised (0.15R500–R500) 分别提取

### 能段与 Grouping
- 能段: 0.5–7.0 keV (匹配 Vikhlinin+2006 的 0.6–8.0 keV 范围)
- Grouping: WSTAT 模式用 `group_counts(1)` (minimal), chi2gehrels 模式用 `group_counts(25)`
- `ignore_bad()` 过滤 quality flags（部分 PHA 无 flags，已加 try/except 保护）

### 初始参数
- kT: 从 M500 自相似关系估算 kT ≈ 5 × (M500/3e14)^{2/3} keV
- Abundance: 固定 0.3 solar
- nH: 固定，从 cluster_table.csv 配置

### 可选参数
- `--fit-soft-bg`: 添加 0.5 keV 软背景热分量（Donahue+2014 方法），多数情况不推荐
- `--fit-method`: levmar (default) / neldermead / moncar

### 已知局限
- **背景**: 使用 local annulus + WSTAT，非文献标准的 blank-sky background
  - Vikhlinin+2006, Donahue+2014 均用 blank-sky + 10-12 keV 归一化
  - 实测发现 blank-sky 对单 ObsID 团效果更差（soft X-ray background 天区不匹配）
  - Local annulus + WSTAT 是当前最优方案（Abell_0068 实测 T_X=33.4 vs blank-sky T_X=63 keV）

## 文献方法对比

| 文献 | 模型 | 背景 | 能段 | Core-excised | Grouping |
|------|------|------|------|-------------|----------|
| [[vikhlinin_2009]] (CCCP) | phabs*apec | blank-sky (10-12 keV norm) | 0.6–8.0 keV | yes | ~30 cts/bin (chi2) |
| [[donahue_2014]] (CLASH-X) | phabs*apec + soft bg | blank-sky (deep bg files) | 0.5–11.0 keV | annular profiles | ≥1500 cts/bin |
| [[mantz_2010]] | phabs*apec | blank-sky | 0.1–2.4 keV | 0.15r500 | — |
| [[pratt_2009]] (REXCESS) | XMM-Newton | standard | bolometric | no (Lx study) | — |
| [[maughan_2008]] | phabs*apec | blank-sky | — | — | ≥20 cts/bin |
| **本项目** | phabs*apec + WSTAT | local annulus + WSTAT | 0.5–7 keV | 0.15R500 | group_counts(1) |

## L_X 计算方式
- **Model-derived** (本项目): 从 APEC normalization 反算 $L_X$
  - $\text{norm} \propto L_X / [D_A^2 (1+z)^2]$
  - 优势: 无需 aperture correction，直接从拟合结果计算
- **Image-derived**: 从暴露校正图像在 aperture 内积分 flux
  - 需要 aperture correction 和 count-to-flux 转换

## 相关概念
- [[scaling_relations]] — T_X 和 L_X 用于标度关系
- [[scaling_fitting]] — 标度关系拟合方法
