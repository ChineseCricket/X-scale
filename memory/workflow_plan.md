# 工作流程计划

本文档是项目的分阶段工作计划。新 session 启动时先读 `memory/pipeline_status.csv` 了解当前进度，再读本文件确定下一步。

---

## Phase 1: 文献准备与分析（在数据处理之前完成）

### 1a. 补充参考文献 ✅ (2026-05-14 完成)

`wiki/raw/` 共 23 篇 PDF（原 14 + 新增 9）。新增：

| 论文 | 文件名 | 理由 |
|------|--------|------|
| Maughan et al. (2008) | 0703156v2.pdf | Chandra 115 团 archive scaling |
| Maughan et al. (2012) | 1108.1200v1.pdf | Lx-T 演化, 114 Chandra 团 |
| Mantz et al. (2016) | 1606.03407v1.pdf | WtG V, WL-calibrated scaling |
| Arnaud et al. (2005) | 0502210v2.pdf | self-similar 理论框架 |
| Arnaud et al. (2007) | 0709.1561v1.pdf | REXCESS M500-Yx 校准 |
| Kelly (2007) | 0711.2455v1.pdf | linmix 方法原文 |
| Okabe et al. (2016) | 1507.04493v2.pdf | LoCuSS M500 弱透镜来源 |
| Vikhlinin et al. (2009) | 0812.2720v2.pdf | CCCP III 经典 Lx-T-M |
| Sun et al. (2009) | 0805.2320v2.pdf | 43 groups Chandra gas properties |

### 1b. 摄入 wiki 文献笔记 ✅ (2026-05-14 完成)

已完成：
- wiki/concepts/scaling_relations.md 对比表已填充（T_X-M500 和 L_X-M500 两张表）
- wiki/index.md 文献索引已创建（22 篇 PDF 按类别索引）
- 部分具体斜率数值标注为"~"近似值，后续可精读补全

### 1c. 审查 project_plan.pdf 和分析步骤 ✅ (2026-05-14 完成)

审查结论：分析步骤与文献最佳实践基本一致，无需大调整。

**一致项**：样本>20团 ✓ | WL M500 ✓ | core-excised 0.15R500 ✓ | linmix ✓
**优于计划**：WSTAT 背景建模 ✓ | per-ObsID 联合拟合 ✓ | model-derived Lx ✓
**注意事项**：
1. E(z) 修正需与 M500 来源使用统一宇宙学参数
2. Lx 能段需明确（bolometric vs soft band）并在结果中注明
3. R500 反算需确保 ρc(z) 一致
4. Dropped 7 团因形态不规则（已记录到 memory/dropped_clusters_reason.md）

---

## Phase 2: CIAO Pipeline 批量处理 ✅ (2026-05-21 全部完成)

- 所有 23 团 `chandra_repro → merge_obs → wavdetect → 点源剔除 → flux image` 已完成
- 6 个大团跳过 csmooth（不影响谱分析）
- Pipeline 产物在各团 `processed/` 子目录

---

## Phase 3: 光谱分析批量处理（进行中）

### 3a. 旧方案测试（local annulus WSTAT + beta-model 修正）✅ (2026-05-21)

4 个团测试结果：MACSJ0429 好结果 (T_X=7.56, ACCEPT=6.76, +12%)，但低红移大团
（Abell_0068 T_X=33.4, Abell_0209 T_X=21.0）因 local annulus 被 ICM 污染而严重偏高。
结论：local annulus 对 R500>300" 的团不可用。

### 3b. Blank-sky XRB 方法（当前方案，2026-05-27）

**方法**：blank-sky + 9.5-12 keV AREASCAL 重归一化 + XRB fixed_shape 模型 + 0.7-7 keV
**代码**：`src/02_spectral/fit_spectral_xrb.py`（合并自 Wei 的 3 个关键函数）

#### 批量结果 (16/23 done)

| Cluster | T_X (keV) | ACCEPT | ratio | rstat | Nspec | 评价 |
|---------|-----------|--------|-------|-------|-------|------|
| Abell_0209 | 8.05 | 8.28 | 0.97 | 0.93 | 1 | Good |
| Abell_2261 | 8.35 | 7.58 | 1.10 | 1.08 | 1 | Good |
| MACSJ0329 | 7.19 | 6.85 | 1.05 | 1.12 | 3 | Good |
| MACSJ0429 | 6.43 | 6.76 | 0.95 | 0.97 | 1 | Excellent |
| MACSJ0744 | 10.15 | 11.29 | 0.90 | 1.06 | 3 | Good |
| MACSJ1115 | 8.92 | 9.26 | 0.96 | 0.98 | 1 | Good |
| MACSJ1931 | 7.39 | 7.50 | 0.99 | 1.11 | 1 | Excellent |
| RXJ1532 | 5.86 | 5.44 | 1.08 | 0.97 | 1 | Good |
| RXJ2248 | 12.15 | 11.10 | 1.09 | 1.06 | 1 | Good |
| Abell_0267 | 8.90 | 6.79 | 1.31 | 0.95 | 1 | Moderate |
| MACSJ1720 | 7.32 | 5.65 | 1.30 | 1.11 | 1 | Moderate |
| Abell_0068 | 12.02 | 7.99 | 1.50 | 1.12 | 1 | High (single ObsID) |
| Abell_0697 | 14.26 | 9.06 | 1.57 | 0.90 | 1 | High (partial ObsID) |
| MACSJ0647 | 16.94 | 9.07 | 1.87 | 1.15 | 2 | Very high |
| MACSJ1206 | 12.89 | 7.88 | 1.64 | 1.06 | 1 | High (partial ObsID) |
| RXJ1347 | 16.39 | 10.88 | 1.51 | 1.25 | 1 | High (partial ObsID) |

**CALDB 失败 (7 团)**：
Abell_0383, Abell_0586, Abell_0611, Abell_0750, MS2137-2353, RXJ2129.7+0005, ZwCl_0857.9+2107

**统计数据**：Good (0.7-1.3x) 10/16 | Acceptable (0.5-1.5x) 11/16

**汇总表**：`output/products/spectral/spectral_twostep_summary.csv`（23 团全部参数，含 M500/R500/Tx/Lx/flux/errors）

### 3c. Phase 3 待完成项

1. **解决 7 个 CALDB 失败团**（更新 CALDB 或回退 local annulus）
2. **排查高 T_X 离群值**（partial ObsID 覆盖、尝试 flexible XRB）
3. **Core-excised 拟合**（0.15-1 R500）：当前只有 full R500 结果

---

## Phase 4: 标度关系拟合（下一步）

### 4a. 数据准备 ✅ (已完成)

汇总表 `output/products/spectral/spectral_twostep_summary.csv` 已包含所有参数：
- M500 (Msun, h70), R500 (arcsec, Mpc)
- T_X (keV) + 误差, L_X (bol + soft, 10^44 erg/s)
- 流量 (10^-12 erg/s/cm^2)
- nH, z, 拟合质量 (rstat, qval)
- ACCEPT 参考值

### 4b. linmix 拟合（待执行）

安装：`pip install linmix`（CIAO conda env 内）

需要拟合的标度关系：
1. **T_X-M500**: `log(Tx) = α + β × log(M500/3×10^14) + γ × log(E(z))`
2. **L_X-M500**: `log(Lx) = α + β × log(M500/3×10^14) + γ × log(E(z))`
3. **L_X-T_X**: `log(Lx) = α + β × log(Tx)`
4. 对 full R500 和 core-excised 分别做
5. M500 来自弱引力透镜（独立于 X-ray）

与文献对比：
- Pratt et al. (2009) REXCESS: T_X-M500 β=0.33±0.07
- Mantz et al. (2016) WtG: L_X-M500 β=1.65±0.10
- Maughan et al. (2012): L_X-T_X β=2.96±0.15

### 4c. Scatter 分析

- 计算 scatter in log Y at fixed M500
- 与 self-similar 预言对比
- 检查 outlier 对拟合的影响

---

## Phase 5: 最终可视化与报告

- 使用 `src/04_visualization/` 绘制 scaling relation 图
- 与文献结果叠加对比
- 更新 README.md 加入最终结果
- 完整参数表
