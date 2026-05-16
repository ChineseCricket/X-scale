---
name: clash-survey
description: CLASH 巡天及本项目使用的 M500 来源 (Umetsu+16)
---

# CLASH Survey

## 概述
Cluster Lensing And Supernova survey with Hubble (CLASH)。HST 多色成像 + 强弱透镜分析。

## 本项目 CLASH 样本
- 16 个团 (部分与 LoCuSS 重叠)
- z 范围: 0.19–0.69
- M500 来源: [[umetsu_2016]] Table 3
- M500 单位: $M_\odot$ (物理质量)
- 在 `configs/cluster_table.csv` 中标注为 "Umetsu et al. CLASH lensing M500c Table 3"

## 数据来源详情
- Umetsu+16: 联合 strong + weak lensing shear + magnification
- M500c: NFW 拟合到 δ=500 的质量
- 精度: ~10–20% per cluster

## 参考
- [[umetsu_2016]] — M500 直接来源
- [[donahue_2014]] — CLASH-X lensing vs X-ray 对比
