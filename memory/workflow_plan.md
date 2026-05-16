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

## Phase 2: CIAO Pipeline 批量处理

- 运行 `src/01_reduction/run_ciao_pipeline.py` 对剩余 ~21 个团执行：
  chandra_repro → merge_obs → wavdetect → 点源剔除 → flux image
- 每批处理几个团，更新 `configs/pipeline_status.csv`
- 处理失败的团记录原因

---

## Phase 3: 光谱分析批量处理

- 对每个完成 pipeline 的团运行 `src/02_spectral/postproces_cluster.py`：
  - full R500 光谱提取 + Sherpa 拟合
  - core-excised (0.15R500--R500) 光谱提取 + Sherpa 拟合
- 收集 T_X 和 L_X（model-derived）
- 更新 `configs/pipeline_status.csv`

---

## Phase 4: 结果汇总

- 汇总所有团的 T_X、L_X、M500 到一个 CSV
- 质量筛选：排除拟合质量差的团
- 检查异常值

---

## Phase 5: Scaling Relation 拟合

- 安装 linmix
- 拟合 T_X - M_500 和 L_X - M_500（full + core-excised）
- 与文献结果对比斜率、归一化、scatter

---

## Phase 6: 最终可视化

- 使用 `src/04_visualization/plot_results.py` 绘制 scaling relation 图
- 与文献对比图
- 最终结果报告
