---
note: 将此文件内容直接粘贴到新 session 作为初始 prompt，然后删除本文件。
---

# Phase 3 Session B：重新拟合 + Flexible XRB

先读 `memory/pipeline_status.csv` 和 `memory/workflow_plan.md` 了解当前进度。

## 当前状态 (Session A 完成)

**23/23 团全部有拟合结果**（7 个 CALDB 失败团已修复）。CALDB 4.12.4 已补全 134 个 ACIS 背景文件。

### Session A 新完成 7 团结果

| 团 | T_X | ACCEPT | ratio | rstat | ObsIDs | 评价 |
|---|---|---|---|---|---|---|
| Abell_0383 | 4.72 | 3.93 | 1.20 | 1.19 | 3/3 | 好 |
| Abell_0586 | 8.10 | 8.70 | 0.93 | 1.04 | 2/9 | 很好 |
| Abell_0611 | 12.87 | 6.69 | 1.92 | 1.04 | 1/1 | 高 (ACIS-S) |
| Abell_0750 | 6.52 | — | — | 3.02 | 2/2 | 拟合差 |
| MS2137 | 63.24 | 6.30 | 10.04 | 14.0 | 3/3 | **失败** (1999 数据) |
| RXJ2129 | 6.84 | 6.10 | 1.12 | 1.15 | 2/2 | 好 |
| ZwCl_0857 | 4.68 | 12.10 | 0.39 | 1.13 | 2/2 | 异常低 |

### 全部 23 团统计

**Good (ratio 0.8-1.2, 10 团):** Abell_0383, Abell_0586, Abell_0209, MACSJ0429, MACSJ0744, MACSJ1115, MACSJ1931, RXJ1532, RXJ2248, RXJ2129

**Acceptable (0.5-1.5, 8 团):** Abell_2261, MACSJ0329, MACSJ1720, Abell_0267, Abell_0068, Abell_0697, RXJ1347, MACSJ1206

**High (>1.5, 2 团):** Abell_0611 (1.92), MACSJ0647 (1.87)

**Failed/Bad (3 团):** MS2137 (fit failed), Abell_0750 (rstat=3), ZwCl_0857 (ratio=0.39 异常)

## 你的任务（按优先级排列）

### 任务 1：MACSJ1206、RXJ1347、Abell_0697 全 ObsIDs 重新拟合

这 3 团之前只有部分 ObsIDs（CALDB 问题）。现在 CALDB 已修复：
- **MACSJ1206**: 当前 1/6 ObsIDs。清除旧 blanksky 后重新跑
- **RXJ1347**: 当前 1/7 ObsIDs
- **Abell_0697**: 当前 1/2 ObsIDs

步骤：
```bash
# 对每个团
rm -rf chandra_data_evt/<cluster>/processed_joint_bxc/blanksky/
rm -rf chandra_data_evt/<cluster>/processed_joint_bxc/spectra*
rm -rf chandra_data_evt/<cluster>/processed_joint_bxc/spectra_high_energy_renorm/
python3 src/02_spectral/fit_spectral_xrb.py --cluster <cluster>
```

### 任务 2：MACSJ0647 和 Abell_0068 尝试 flexible XRB

```bash
python3 src/02_spectral/fit_spectral_xrb.py --cluster MACSJ0647.7+7015 --xrb-policy flexible
python3 src/02_spectral/fit_spectral_xrb.py --cluster Abell_0068 --xrb-policy flexible
```

### 任务 3：修复 MS2137-2353

拟合失败（T_X=63 keV, rstat=14）。ObsID 928 来自 1999-11 数据质量差。
- 尝试只用 ObsID 4974+5250（2003 年），手动编辑 blanksky 目录只保留这两个
- 或用 `--no-run-blanksky` + local annulus WSTAT

### 任务 4：排查 ZwCl_0857 异常低 T_X

T_X=4.68 vs ACCEPT=12.10 (ratio=0.39)。检查 ACCEPT 参考值是否来自不同孔径。

### 任务 5：Abell_0586 用更多 ObsIDs

当前 2/9 ObsIDs。2016-2017 ObsIDs 需要 ACIS-01235 配置的更新 CALDB 文件。检查 blanksky 能否为这些 ObsIDs 运行。

## 关键文件

- 主拟合脚本：`src/02_spectral/fit_spectral_xrb.py`
- 批量拟合：`src/02_spectral/batch_spectral_xrb.py`
- 汇总表：`output/products/spectral/spectral_twostep_summary.csv`（已更新 23 团）
- 单团结果 JSON：`output/products/spectral/<cluster>_results.json`
- 拟合图：`output/figures/spectral/<cluster>_fit.png`
- ACCEPT 参考：`configs/accept_reference.csv`
- 团簇配置：`configs/cluster_table.csv`
- 进度：`memory/pipeline_status.csv`

## 技术要点

- CIAO: `source /data/jyz/Applications/ciao-4.18/ciao-4.18/bin/ciao.sh`
- CALDB 已更新：134 个 ACIS 背景文件（Groups B-G 全部安装）
- linmix 未安装：`pip install linmix`（在 CIAO conda env 内）
