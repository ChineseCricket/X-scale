---
name: locuss-survey
description: LoCuSS 巡天及本项目使用的 M500 来源 (Okabe+16)
provenance: llm-derived
---

# LoCuSS Survey

## 概述
Local Cluster Substructure Survey (LoCuSS)。Subaru/Suprime-Cam 弱透镜巡天。

## 本项目 LoCuSS 样本
- 14 个团 (去除 7 个 dropped 后; 原始 ~21)
- z 范围: 0.15–0.3
- M500 来源: [[okabe_2016]]
- M500 原始单位: $h^{-1} M_\odot$ → 已转换为 $M_\odot$ (h=0.7)
- 在 `configs/cluster_table.csv` 中标注为 "LoCuSS notes in clusters_Xray.md for lensing M500"

## 数据来源详情
- Okabe & Smith 2016: 50 团 Subaru 弱透镜
- M500: NFW 拟合
- 精度: ~15–25% per cluster
- 注意: 需确认 h 转换因子 (cluster_table.csv 中 m500_unit = "h^-1 Msun", m500_physical_msun_h70 列已转换)

## 参考
- [[okabe_2016]] — M500 直接来源
- [[umetsu_2016]] — CLASH 弱透镜对比
