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

## Phase 3: 光谱分析批量处理（基本完成，需冻结最终输入表）

### 3a. 旧方案测试（local annulus WSTAT + beta-model 修正）✅ (2026-05-21)

4 个团测试结果：MACSJ0429 好结果 (T_X=7.56, ACCEPT=6.76, +12%)，但低红移大团
（Abell_0068 T_X=33.4, Abell_0209 T_X=21.0）因 local annulus 被 ICM 污染而严重偏高。
结论：local annulus 对 R500>300" 的团不可用。

### 3b. Blank-sky XRB 方法（当前方案，2026-05-27--2026-05-28）

**方法**：blank-sky + 9.5-12 keV AREASCAL 重归一化 + XRB fixed_shape 模型 + 0.7-7 keV
**代码**：`src/02_spectral/fit_spectral_xrb.py`（合并自 Wei 的 3 个关键函数）

#### 当前结论 (23/23 已有结果)

CALDB 失败团已补齐并拟合完成；最新逐团状态以 `memory/pipeline_status.csv` 为准。
旧 `spectral_twostep_summary.csv` 中仍保留部分早期/partial ObsID 结果，不应再作为 status source。

**主样本可用**：18/23（排除 5 个 bad/suspect）。

**主样本排除**：
- Abell_0697：全 2/2 ObsIDs 重跑失败，ObsID 532 驱动差拟合；旧 4217-only 结果只能作为备选敏感性测试。
- Abell_0750：rstat=3.02，早期数据拟合差。
- MS2137-2353：4974+5250-only 仍失败，T_X~55 keV，rstat~15。
- RXJ1347.5-1145：全 7/7 ObsIDs 拟合变差，rstat=1.63；旧 single-ObsID 结果只能作为敏感性测试。
- ZwCl_0857.9+2107：T_X/ACCEPT=0.39；ACCEPT 参考疑似孔径/质量标记不一致。

**高但保留**：Abell_0068、Abell_0611、MACSJ0647.7+7015、MACSJ1206.2-0847 等需在图中标注，作为 sensitivity/outlier 检查。

**注意**：`output/products/spectral/spectral_twostep_summary.csv` 当前落后于最新 rerun 记录；Phase 4 前必须先从最新 JSON 和 `memory/pipeline_status.csv` 重新生成 canonical spectral table。

### 3c. Phase 3 待完成项

1. **冻结最终 full-R500 输入表**：重建 `output/products/spectral/spectral_summary.csv` 或等价 canonical CSV，确保 Abell_0068/MACSJ0647/MACSJ1206 使用最新 rerun，Abell_0697/RXJ1347/MS2137/Abell_0750/ZwCl 标记为 excluded。
2. **保留 rescue/sensitivity 路径**：Abell_0697 4217-only、RXJ1347 single-ObsID、MS2137 flexible/free-abundance 只作为 sensitivity，不阻塞主 scaling。
3. **Core-excised 拟合**（0.15-1 R500）：当前主结果仍是 full R500；core-excised 是最终论文式对比的下一轮科学改进。

---

## Phase 4: 标度关系拟合（已有 raw try，下一步是正式化）

### 4a. 数据准备（需重做 canonical table）

原始尝试目录：`weiwwqeo_scaling/`。已提交的 raw try 使用：
- 输入：`output/products/spectral/spectral_twostep_summary.csv`
- 模型：`log10(Y / E(z)^gamma_fixed) = alpha + beta log10(M500c / 3e14 Msun)`
- Lx-M500：固定 gamma=2
- Tx-M500：固定 gamma=2/3
- 默认误差：M500 20%，Lx 10%，Tx 使用表中误差

Raw try 的 `exclude_bad` 样本排除了 Abell_0750、MS2137-2353、ZwCl_0857.9+2107，得到：
- Lx-M500: beta=0.96 +/- ~0.32，intrinsic scatter~0.19 dex
- Tx-M500: beta=0.59 +/- ~0.17，intrinsic scatter~0.11 dex

但该 raw try 基于旧 summary，未反映最新 Abell_0697、RXJ1347 全 ObsID 失败和 MACSJ1206/Abell_0068/MACSJ0647 rerun。因此它只能作为代码/方法草稿，不作为最终科学结果。

正式 Phase 4 输入表必须包含：
- M500 (Msun, h70), R500 (arcsec, Mpc)
- T_X (keV) + 误差, L_X (bol + soft, 10^44 erg/s)
- 流量 (10^-12 erg/s/cm^2)
- nH, z, 拟合质量 (rstat, qval)
- ACCEPT 参考值
- quality/exclude flag（主样本排除 bad；保留 high/suspect 标记）

### 4b. linmix 拟合（正式化待执行）

安装：`pip install linmix`（CIAO conda env 内）。注意：raw README 中的 `/opt/miniconda3/bin/conda` 路径在当前机器不可用，正式运行前需确认实际 CIAO Python 环境。

正式化步骤：
1. 将 `weiwwqeo_scaling/src/fit_scaling_relations.py` 的可复用逻辑迁入正式 `src/` 位置（建议 `src/03_scaling/fit_scaling_relations.py`），输出改到 `output/products/scaling/` 和 `output/figures/scaling/`。
2. 默认输入改为最新 canonical spectral table，而不是旧 `spectral_twostep_summary.csv`。
3. 默认主样本排除 `quality=bad`：Abell_0697、Abell_0750、MS2137-2353、RXJ1347.5-1145、ZwCl_0857.9+2107。
4. 输出 all / exclude_bad / sensitivity 三套结果；论文主结论使用 exclude_bad。
5. 先做 full-R500 的 Lx-M500 和 Tx-M500；Lx-Tx 与 core-excised 作为后续扩展。

与文献对比：
- Pratt et al. (2009) REXCESS: T_X-M500 β=0.33±0.07
- Mantz et al. (2016) WtG: L_X-M500 β=1.65±0.10
- Maughan et al. (2012): L_X-T_X β=2.96±0.15

### 4c. Scatter 分析

- 计算 scatter in log Y at fixed M500
- 与 self-similar 预言对比
- 检查 high/suspect 团对拟合的影响（尤其 Abell_0068、Abell_0611、MACSJ0647、MACSJ1206）

---

## Phase 5: 最终可视化与报告

- 使用 `src/04_visualization/` 绘制 scaling relation 图
- 与文献结果叠加对比
- 更新 README.md 加入最终结果
- 完整参数表
