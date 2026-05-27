---
note: 将此文件内容直接粘贴到新 session 作为初始 prompt，然后删除本文件。
---

继续 Phase 3 → Phase 4：标度关系拟合。先读 memory/pipeline_status.csv 了解当前进度。

## 当前状态

- Phase 3 谱拟合已完成 16/23 团（blank-sky XRB 方法）
- 7 团因 CALDB 缺失空白天空背景文件而失败
- 汇总表已生成：`output/products/spectral/spectral_twostep_summary.csv`
- 所有代码已提交推送

## 拟合结果概要 (16 done)

**Good (ratio 0.9-1.1x, 8 团):**
MACSJ0429 (0.95), MACSJ1931 (0.99), Abell_0209 (0.97), MACSJ1115 (0.96),
MACSJ0744 (0.90), RXJ1532 (1.08), RXJ2248 (1.09), MACSJ0329 (1.05)

**Acceptable (ratio 1.1-1.5x, 3 团):**
Abell_2261 (1.10), Abell_0267 (1.31), MACSJ1720 (1.30)

**High (ratio >1.5x, 5 团):**
Abell_0068 (1.50), Abell_0697 (1.57), MACSJ0647 (1.87),
MACSJ1206 (1.64), RXJ1347 (1.51)

**CALDB 失败 (7 团):**
Abell_0383, Abell_0586, Abell_0611, Abell_0750, MS2137-2353,
RXJ2129.7+0005, ZwCl_0857.9+2107

## 你的任务（按优先级排列）

### 任务 1：解决 7 个 CALDB 失败团

CALDB 4.12.4 缺少部分 ACIS 配置的空白天空背景文件。错误：
`dmmerge ERROR: Couldn't open file (acis*bkgrnd*.fits)`

方案（按可行性尝试）：
1. 检查 CALDB 是否有更新版本可安装
2. 查看哪些 ObsID 失败，尝试用 `blanksky bkgparams=` 指定替代背景文件
3. 如果 CALDB 无法解决，对这些团回退到 **local annulus WSTAT + beta-model 修正**
   （已有代码：`src/02_spectral/fit_spectral_joint.py`）

### 任务 2：排查高 T_X 离群值

5 个团的 T_X/ACCEPT > 1.5x，主要原因是 partial ObsID 覆盖：
- MACSJ1206: 6 个 ObsID 只用了 1 个（CALDB 问题）
- RXJ1347: 7 个 ObsID 只用了 1 个
- MACSJ0647: 2 个 ObsID 都有 blank-sky 但仍偏高 → 尝试 `--xrb-policy flexible`
- Abell_0068: 单 ObsID 数据质量限制
- Abell_0697: 2 个 ObsID 只用了 1 个

对这些团：
1. 检查是否可以用更多 ObsID（修复 CALDB）
2. 对已有全部 ObsID 的团尝试 flexible XRB policy
3. 检查 blank-sky HE renorm diagnostics（是否 factor 异常）

### 任务 3：标度关系拟合（linmix）

即使只有 16 个团也可以先做初步拟合。使用汇总表：
`output/products/spectral/spectral_twostep_summary.csv`

需要的拟合：
1. **Lx-M500**: `log(Lx_bol) = α + β × log(M500/3e14) + γ × log(1+z)`（Evolution 形式）
2. **Tx-M500**: `log(Tx) = α + β × log(M500/3e14) + γ × log(1+z)`
3. 注意 M500 来自弱引力透镜（独立于 X-ray），这是自洽的
4. 使用 `linmix` (Kelly 2007) 做 Bayesian 线性回归，考虑测量误差
5. 与文献对比：[[pratt_2009]], [[mantz_2010]], [[maughan_2012]]

### 任务 4：Core-excised 拟合

当前只有 full R500 (0-1 R500) 的结果。文献通常还报告 core-excised (0.15-1 R500) 温度：
- 修改 `fit_spectral_xrb.py` 支持 `--source-inner-r500 0.15`
- 对所有 23 团跑 core-excised 拟合
- 生成第二个汇总表

## 关键文件

### 代码
- 主拟合脚本：`src/02_spectral/fit_spectral_xrb.py`
- 批量 blanksky：`src/02_spectral/batch_blanksky_gen.py`
- 批量拟合：`src/02_spectral/batch_spectral_xrb.py`
- 旧 beta-model 修正版：`src/02_spectral/fit_spectral_joint.py`
- β-model：`src/02_spectral/beta_model_profile.py`

### 数据
- 汇总表：`output/products/spectral/spectral_twostep_summary.csv`（23 团全部参数）
- 单团结果 JSON：`output/products/spectral/<cluster>_results.json`
- 拟合图：`output/figures/spectral/<cluster>_fit.png`
- ACCEPT 参考：`configs/accept_reference.csv`
- 团簇配置：`configs/cluster_table.csv`
- 进度：`memory/pipeline_status.csv`

### Wiki 文献
- `wiki/papers/pratt_2009.md` — REXCESS 标度关系
- `wiki/papers/mantz_2010.md` — Mantz 方法
- `wiki/concepts/scaling_relations.md` — 标度关系汇总

## 技术要点

- CIAO: `source /data/jyz/Applications/ciao-4.18/ciao-4.18/bin/ciao.sh`
- linmix 未安装：`pip install linmix`（在 CIAO conda env 内）
- 标度关系标准形式：`Y = Y₀ × (M500/3×10¹⁴ M☉)^β × E(z)^γ × (1+z)^ζ`
- M500 已 h⁻¹ 修正为 h=0.70 物理单位
- Lx 需确认是吸收修正后的还是观测波段（当前 Lx_bol 是吸收修正后的 bolometric）
