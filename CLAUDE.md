# X_scale — Galaxy Cluster X-ray Scaling Relation

## 上下文管理（重要）

**模型上下文窗口上限 128k tokens。** 遵守以下规则：

- 回复精简，一句话说完的不要用一段话
- 优先用 grep/find 定位，不要 Read 整个大文件
- 命令输出过长时用 head/tail/wc -l 截取
- 复杂任务拆成多个独立小任务
- 同一 session 内不重复读取同一文件
- **上下文长度自检**：当检测到本次对话已产生大量工具调用或长输出时，主动估算上下文占用；接近 128k 上限（~100k tokens）时，立即提醒用户"上下文即将耗尽，建议开新 session 继续"，并简要总结当前进度以便无缝衔接

## 项目目标

用 Chandra X-ray 数据复现 Galaxy Cluster 的 **Lx-M500** 和 **Tx-M500** 标度关系。
样本：23 个星系团（CLASH 16 + LoCuSS 14，dropped 7 个），M500 来自弱引力透镜测量。

## 关键决策

- T_X: full R500 + core-excised (0.15R500--R500) 都做
- L_X: model-derived（从 Sherpa APEC normalization 反算）
- Scaling relation 拟合: linmix (Kelly 2007)
- 光谱拟合: absorbed APEC + WSTAT，逐 ObsID specextract + Sherpa 联合拟合

## 数据路径

- 原始数据: `chandra_data_evt/<cluster_key>/raw/<obsid>/primary+secondary`
- repro 后: `chandra_data_evt/<cluster_key>/raw/<obsid>/repro/`
- pipeline 输出: `chandra_data_evt/<cluster_key>/processed/`
- `data/raw` → symlink 到 `../chandra_data_evt`

## 代码位置（全部在 src/ 下）

- `src/00_download/` — 数据下载
- `src/01_reduction/run_ciao_pipeline.py` — CIAO pipeline（repro→merge→wavdetect→flux）
- `src/02_spectral/postproces_cluster.py` — 光谱分析（R500→specextract→Sherpa），配套文档在同目录下
- `src/04_visualization/` — 可视化

## 配置文件

- `configs/cluster_table.csv` — 33 个团的 RA/Dec/z/M500/ObsIDs（CLASH + LoCuSS）
- `configs/dropped.list` — 7 个排除的团
- **`memory/pipeline_status.csv`** — 每个团的处理进度（session 恢复时先读这个）

## 环境

- CIAO 4.18: `source /data/jyz/Applications/ciao-4.18/ciao-4.18/bin/ciao.sh`
- 必须先 source ciao.sh 才能用 CIAO Python / sherpa
- 依赖: sherpa, astropy 7.2, numpy 2.3, scipy 1.17, matplotlib 3.10
- 待装: linmix

## Pipeline 依赖链

```
chandra_repro → merge_obs → wavdetect → 点源剔除 → flux image
  → specextract (per ObsID) → Sherpa joint fit → T_X, L_X
```

## 工作流程

**新 session 启动时：先读 `memory/pipeline_status.csv` 了解进度，再读 `memory/workflow_plan.md` 确定下一步。**

## 踩坑记录

- CIAO Python 不能直接运行，必须先 source ciao.sh
- astropy/numpy 需额外安装在 CIAO miniconda3 环境中（已装）
- `postproces_cluster.py` 名字有 typo（少一个 s），保持原样避免破坏兼容性
- source ciao.sh 后用管道（`|`）接 python 会导致 PATH 不传播，必须用 `source ciao.sh && python ...`
- Phase 2 输出在 `processed/` 子目录，Phase 3 脚本默认路径已修正（DEFAULT_* 常量加 `processed/` 前缀）
- Sherpa `ignore_bad()` 在 PHA 无 quality flags 时会报错，已加 try/except 保护
- WSTAT 模式下 `group_counts(1)` 做 minimal grouping；chi2gehrels 模式用 `group_counts(25)`
- T_X 异常高（>20 keV）通常是数据限制（单 ObsID、local annulus 背景），非代码 bug
- blank-sky background 是文献标准做法（Vikhlinin+2006, Donahue+2014），当前未实现，是已知系统误差
- Blank-sky 对单 ObsID 团效果不如 local annulus + WSTAT（soft X-ray background 不匹配导致 T_X 更高），local annulus + WSTAT 是当前最优方案

## 输出目录约定（重要）

`output/` 目录集中存放 pipeline 和分析结果，按阶段分子目录：

```
output/
  logs/
    pipeline/       — pipeline 批次日志 (batch_N.log)
    spectral/       — 光谱分析日志
  products/
    pipeline/       — batch_N_summary.csv (由 batch_summary.py 生成)
    spectral/       — 光谱分析汇总结果
    scaling/        — scaling relation 拟合结果
  figures/
    pipeline/       — pipeline 中间结果图 (flux maps, aperture overlays)
    spectral/       — 光谱拟合图 (fit plots)
    scaling/        — 最终 scaling relation 图
```

**每批 pipeline 完成后必须执行：**

1. 保存日志到 `output/logs/pipeline/batch_N.log`
2. 运行 `python src/01_reduction/batch_summary.py --batch N --clusters <list>` 生成汇总到 `output/products/pipeline/`
3. 更新 `memory/pipeline_status.csv`
4. 更新 `README.md` 的「当前状态」表格，保持人工可追踪

### 关键步骤记录规范

**每步必更（agent 自动执行，无需提醒）：**
- `memory/pipeline_status.csv` — 更新该团的状态和 notes
- `output/logs/<phase>/` — 保存本次操作的完整日志（参数、结果、遇到的问题）
- `CLAUDE.md` 踩坑记录 — 发现新问题时追加

**阶段性更新（batch/phase 完成时）：**
- `README.md` "当前状态"表 — 更新 phase 级进度
- `wiki/methods/` 相关方法页 — 更新方法对比表和参数
- `wiki/log.md` — 追加操作日志
- `src/` 下对应的 `*_documentation_bilingual.md` — 更新双语使用文档

**项目结束时：**
- `README.md` — 重写，加入最终结果、scaling relation 总结、完整参数表

## Wiki 约定（重要）

项目维护一个 LLM Wiki（`wiki/`），用于文献管理和知识组织。涉及 wiki 操作时遵守以下规则：

### 目录结构
- `wiki/raw/` — PDF 原文（只读，不修改）
- `wiki/papers/` — 每篇论文一个页面 `<author>_<year>.md`
- `wiki/concepts/` — 概念页面（如 scaling_relations.md）
- `wiki/methods/` — 方法页面（如 spectral_fitting.md）
- `wiki/data_sources/` — 数据来源页面（如 clash_survey.md）
- `wiki/index.md` — 索引（使用 `[[wikilink]]` 链接所有页面）
- `wiki/log.md` — 操作日志

### 摄入新论文（wiki-ingest）
1. 读 PDF（Read 工具或 pdftotext）
2. 创建 `wiki/papers/<author>_<year>.md`，必须包含 frontmatter：title, authors, year, journal, arxiv, keywords
3. 页面结构：One-line Summary → Sample → Key Results → Key Equations → Methods → Relations to Other Work
4. 更新 `wiki/concepts/scaling_relations.md` 对比表
5. 更新 `wiki/index.md`（用 `[[wikilink]]` 格式）
6. 追加 `wiki/log.md`
7. 数值必须注明来自原文的哪个 Table/Figure

### 跨页面引用
- 使用 `[[author_year]]` 格式（如 `[[pratt_2009]]`、`[[mantz_2010]]`）
- 概念/方法/数据源页面用 `[[page_name]]`（如 `[[spectral_fitting]]`）

### Wiki 健康检查（wiki-check）
定期运行：检查断链、索引完整性、frontmatter 完整性、孤儿页面。

详细规范见 `.claude/skills/wiki-ingest.md` 和 `.claude/skills/wiki-check.md`。
