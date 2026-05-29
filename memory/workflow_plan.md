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

### 3d. 光谱拟合图 QA 更新 ✅ (2026-05-29)

已修正 `output/figures/spectral/*_fit.png` 的显示口径。旧图直接把 Sherpa/WSTAT 的 raw source PHA data plot 与 folded source model 画在一起；blank-sky particle/background 贡献仍在 raw source counts 中，因此很多好拟合会视觉上表现为 model 系统性低于 data。

当前图由 `src/02_spectral/fit_spectral_xrb.py` 和 `src/02_spectral/regenerate_spectral_fit_plots.py` 生成：
- 顶部面板：raw source data 与 scaled blank-sky/background，显示旧图 offset 来源。
- 中部面板：background-subtracted/net source data vs folded total source-region model，并用 dashed/dotted 线显示 ICM、LHB、Galactic halo、CXB 的 response-folded 贡献。
- 残差面板：`(net-total)/sigma` 或 net-total。

这次只改 QA 可视化和 JSON 中的 `plot_caveat`/`fit_plot_png`/`residual_summaries`，不改变 WSTAT 拟合、谱参数、Lx/Tx 或 scaling products。验证例：Abell_0209、MACSJ1206.2-0847 的 net-data/model 不再有系统 offset；Abell_0697 仍保留明显差残差，说明真实 bad fit 没被掩盖。
实现注意：Sherpa plot objects 会在后续 `set_source()` 后被复用/更新，因此 component diagnostic 必须立即 snapshot `x/y/yerr` arrays；否则 total model curve 可能被后续 component curve 覆盖。

---

## Phase 4: 标度关系拟合（full-R500 初版已正式化）

### 4a. 数据准备 ✅ (2026-05-28 完成)

原始尝试目录：`weiwwqeo_scaling/`。已提交的 raw try 使用：
- 输入：`output/products/spectral/spectral_twostep_summary.csv`
- 模型：`log10(Y / E(z)^gamma_fixed) = alpha + beta log10(M500c / 3e14 Msun)`
- Lx-M500：固定 gamma=2
- Tx-M500：固定 gamma=2/3
- 默认误差：M500 20%，Lx 10%，Tx 使用表中误差

Raw try 的 `exclude_bad` 样本排除了 Abell_0750、MS2137-2353、ZwCl_0857.9+2107，得到：
- Lx-M500: beta=0.96 +/- ~0.32，intrinsic scatter~0.19 dex
- Tx-M500: beta=0.59 +/- ~0.17，intrinsic scatter~0.11 dex

该 raw try 基于旧 summary，未反映最新 Abell_0697、RXJ1347 全 ObsID 失败和 MACSJ1206/Abell_0068/MACSJ0647 rerun。因此它只能作为代码/方法草稿，不作为最终科学结果。

正式 Phase 4 输入表已生成并升级不确定度：`output/products/spectral/spectral_summary.csv`。
主样本 18/23，排除 Abell_0697、Abell_0750、MS2137-2353、RXJ1347.5-1145、ZwCl_0857.9+2107。

正式 Phase 4 输入表包含：
- M500 (Msun, h70) + 文献误差/provenance；R500 (arcsec, Mpc) + 由 M500 误差传播的 aperture provenance
- T_X (keV) + 误差, L_X (bol + soft, 10^44 erg/s) + Lx 不确定度/provenance
- 流量 (10^-12 erg/s/cm^2)
- nH, z, 拟合质量 (rstat, qval)
- ACCEPT 参考值
- quality/exclude flag（主样本排除 bad；保留 high/suspect 标记）
- `configs/m500_reference.csv` 是 M500 中心值和误差来源表：CLASH 用 Umetsu+16 Table 3；LoCuSS 用 Okabe+16 Table 2（Table 3 是 c-M 关系，不是 individual M500）。
- 已修正 3 个 LoCuSS config 质量列错误：Abell_0697 和 ZwCl_0857.9+2107 之前误用了 M180m，Abell_0750 之前误用了 M1000；三者都在 exclude_bad 样本外。
- full-R500 重点缺失项已补齐：Abell_0068 和 MACSJ0647.7+7015 已 rerun 并写入 Sherpa `sample_energy_flux` 原生 Lx 区间；exclude_bad 主样本中这两团不再使用 Lx fallback。若干 bad/excluded 团仍有 Lx fallback 或缺失，但不影响主样本。

### 4b. linmix 拟合 ✅ (2026-05-29 full-R500 uncertainty + sensitivity upgrade)

`linmix` 已安装到 CIAO Python：`/data/jyz/Applications/ciao-4.18/ciao-4.18/binexe/python3.12`。

正式脚本：`src/03_scaling/fit_scaling_relations.py`。
输出位置：`output/products/scaling/` 和 `output/figures/scaling/`。

主结果（exclude_bad, N=18）：
- Lx-M500: beta=1.09 -0.45/+0.47, intrinsic scatter=0.165 dex
- Tx-M500: beta=0.51 -0.25/+0.24, intrinsic scatter=0.116 dex
- Lx-Tx: beta=0.77 -0.43/+0.46, intrinsic scatter=0.227 dex (fixed self-similar bolometric evolution gamma=1)

已输出 all / exclude_bad / good_only / comparison 结果，并加入 Lx-Tx 图和表。论文主结论暂用 exclude_bad，good_only 作为严格质量敏感性样本 (N=11)。
good_only 结果：
- Lx-M500: beta=0.51 -0.61/+0.71, intrinsic scatter=0.227 dex
- Tx-M500: beta=0.43 -0.21/+0.23, intrinsic scatter=0.071 dex
- Lx-Tx: beta=1.17 -0.93/+0.90, intrinsic scatter=0.231 dex

新增 leave-one-out sensitivity 输出：`output/products/scaling/scaling_linmix_fixed_evolution_sensitivity_summary.csv` / `.json` / `.md`。默认逐个移除 Abell_0068、Abell_0611、MACSJ0647.7+7015、MACSJ1206.2-0847，并对 Lx-M500、Tx-M500、Lx-Tx 都重拟合。结果显示这些单点移除对 M500 关系 beta 的影响均小于当前统计误差；Lx-Tx 对 Abell_0611 和 MACSJ1206.2-0847 更敏感但仍误差很大。

与文献对比：
- Pratt et al. (2009) REXCESS: T_X-M500 β=0.33±0.07
- Mantz et al. (2016) WtG: L_X-M500 β=1.65±0.10
- Maughan et al. (2012): L_X-T_X β=2.96±0.15

### 4c. Scatter 分析

- 计算 scatter in log Y at fixed M500
- 与 self-similar 预言对比
- high/suspect leave-one-out 已完成（尤其 Abell_0068、Abell_0611、MACSJ0647、MACSJ1206）
- 下一步：如论文需要，可补 bootstrap/jackknife 稳健性表；full-R500 主线已经可进入最终整理。

### 4d. Core-excised blank-sky XRB 分支（进行中，2026-05-29）

已在 `src/02_spectral/fit_spectral_xrb.py` 加入正式 core-excised aperture 支持：
- `--excise-core/--no-excise-core`
- `--core-inner-r500 0.15`
- source aperture = `0.15-1.0 R500`
- full-R500 输出保持在 `processed_joint_bxc/`、`output/products/spectral/`、`output/figures/spectral/`
- core-excised 输出独立放在 `processed_joint_bxc_coreexcised/`、`output/products/spectral/core_excised/`、`output/figures/spectral/core_excised/`

`src/03_scaling/build_spectral_summary.py` 已泛化为可指定 `--results-dir` 和 `--output`，用于生成：
- full-R500 canonical: `output/products/spectral/spectral_summary.csv`
- core-excised branch: `output/products/spectral/spectral_summary_core_excised.csv`

`src/03_scaling/fit_scaling_relations.py` 支持独立 `--summary/--outdir/--figdir`，并且当 partial batch 的某个 sample 小于 5 团时会跳过该 sample 而不是中止整个 run。

当前 core-excised 状态：
- 14/23 已完成 result JSON；14/18 exclude_bad included clusters 已完成。
- 已完成 included clusters: Abell_0209, Abell_0068, Abell_0267, Abell_0383, Abell_0586, Abell_0611, Abell_2261, MACSJ0329.7-0211, MACSJ0429.6-0253, MACSJ0647.7+7015, MACSJ0744.9+3927, MACSJ1115.9+0129, MACSJ1206.2-0847, MACSJ1720.3+3536.
- 尚未完成 included clusters: MACSJ1931.8-2635, RXJ1532.9+3021, RXJ2129.7+0005, RXJ2248.7-4431.
- Excluded bad clusters仍可选跑作 completeness，但不影响主 core-excised scaling。
- 当前 core-excised JSON 都有 native Sherpa `sample_energy_flux` Lx 区间；但 T_X confidence intervals 仍缺失，因此 scaling 中 Tx-M500 和 Lx-Tx 的 Tx errors 使用脚本记录的 10% fallback。

当前 core-excised exclude_bad N=14 初版结果：
- Lx-M500: beta=1.20 -0.47/+0.51, intrinsic scatter=0.165 dex
- Tx-M500: beta=0.49 -0.51/+0.45, intrinsic scatter=0.169 dex
- Lx-Tx: beta=0.78 -0.37/+0.41, intrinsic scatter=0.225 dex

Core-excised 下一步：
1. 跑完剩余 4 个 included clusters。
2. 重新生成 `spectral_summary_core_excised.csv` 和 `output/products/scaling/core_excised/`。
3. 判断是否需要为 core-excised T_X 增加/回填 confidence intervals；否则在论文中明确 Tx error fallback。
4. 若时间允许，再跑 5 个 excluded bad clusters 作完整性/附录，不纳入主样本。

---

## Phase 5: 最终可视化与报告

- 使用 `src/04_visualization/` 绘制 scaling relation 图
- 与文献结果叠加对比
- 更新 README.md 加入最终结果
- 完整参数表

当前判断（2026-05-29）：项目已经接近最终阶段。full-R500 主结果基本可以冻结；最后主要剩下 core-excised included batch 收尾、方法/README/wiki 文档整理、最终图表与论文式表格。
