---
note: 将此文件内容直接粘贴到新 session 作为初始 prompt，然后删除本文件。
---

# Phase 4 Session：正式化 scaling relation（基于 weiwwqeo_scaling raw try）

先读 `memory/pipeline_status.csv` 和 `memory/workflow_plan.md` 了解当前进度。

## 当前状态

**23/23 团全部有拟合结果**。CALDB 4.12.4 已补全 134 个 ACIS 背景文件。

最新状态以 `memory/pipeline_status.csv` 为准。主 scaling 样本暂定排除 5 团：
- Abell_0697：全 2/2 ObsIDs 失败，ObsID 532 驱动差拟合；旧 4217-only 只能做 sensitivity。
- Abell_0750：rstat=3.02。
- MS2137-2353：4974+5250-only 仍失败，rstat~15。
- RXJ1347.5-1145：全 7/7 ObsIDs 拟合变差，rstat=1.63；旧 single-ObsID 只能做 sensitivity。
- ZwCl_0857.9+2107：T_X/ACCEPT=0.39，ACCEPT 参考疑似孔径/flag 不一致。

## weiwwqeo_scaling raw try

`weiwwqeo_scaling/` 已有 raw scaling 尝试：
- 脚本：`weiwwqeo_scaling/src/fit_scaling_relations.py`
- 输入：`output/products/spectral/spectral_twostep_summary.csv`
- 输出：`weiwwqeo_scaling/products/` 和 `weiwwqeo_scaling/figures/`
- 模型：固定演化 `log10(Y/E(z)^gamma)=alpha+beta log10(M500c/3e14 Msun)`
- exclude_bad raw 结果：Lx-M500 beta~0.96，Tx-M500 beta~0.59

重要：raw try 使用旧 `spectral_twostep_summary.csv`，未反映最新 Abell_0697/RXJ1347 bad 状态和部分 rerun 结果，不能直接作为最终科学结果。

## 下一步任务（按优先级）

### 任务 1：重建 canonical spectral table

不要直接用旧 `spectral_twostep_summary.csv` 做最终拟合。需要从最新 JSON/状态重建：
- output/products/spectral/spectral_summary.csv（或同等 canonical 文件）
- 包含 latest Tx/Lx/rstat/qval/ObsID count
- 加入 quality 和 exclude_from_main_scaling
- bad/excluded: Abell_0697, Abell_0750, MS2137-2353, RXJ1347.5-1145, ZwCl_0857.9+2107

### 任务 2：正式化 scaling 脚本

把 `weiwwqeo_scaling/src/fit_scaling_relations.py` 迁入正式源码位置，建议：
- `src/03_scaling/fit_scaling_relations.py`
- 默认输入 canonical spectral table
- 默认输出 `output/products/scaling/` 和 `output/figures/scaling/`
- 保留 all / exclude_bad / sensitivity 三种样本

### 任务 3：主 scaling 结果

先完成 full-R500：
- Lx-M500, fixed gamma=2
- Tx-M500, fixed gamma=2/3
- 主结果使用 exclude_bad
- high/suspect clusters 在图中标注并做 sensitivity

## 关键文件

- 主拟合脚本：`src/02_spectral/fit_spectral_xrb.py`
- 批量拟合：`src/02_spectral/batch_spectral_xrb.py`
- raw scaling：`weiwwqeo_scaling/src/fit_scaling_relations.py`
- 旧汇总表：`output/products/spectral/spectral_twostep_summary.csv`（已落后，只能参考）
- 单团结果 JSON：`output/products/spectral/<cluster>_results.json`
- 拟合图：`output/figures/spectral/<cluster>_fit.png`
- ACCEPT 参考：`configs/accept_reference.csv`
- 团簇配置：`configs/cluster_table.csv`
- 进度：`memory/pipeline_status.csv`

## 技术要点

- CIAO: `source /data/jyz/Applications/ciao-4.18/ciao-4.18/bin/ciao.sh`
- CALDB 已更新：134 个 ACIS 背景文件（Groups B-G 全部安装）
- linmix 需重新确认/安装：`pip install linmix`（在实际 CIAO conda env 内）；raw README 的 `/opt/miniconda3/bin/conda` 路径在当前机器不可用
