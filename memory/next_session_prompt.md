---
note: 将此文件内容直接粘贴到新 session 作为初始 prompt，然后删除本文件。
---

继续 Phase 3 谱拟合。先读 memory/pipeline_status.csv 和 memory/phase3_2026-05-26_progress.md 了解当前进展。

## 当前状态

- 批量 pipeline 后台运行中（已完成部分团的 specextract + β-model + 拟合）
- 已确认根本问题：**粒子背景扣除不足**导致 T_X 严重偏高
- Wei 的方案（`weiwwqeo_scripts/`）已成功将 Abell_383 的 T_X 从 8.54 → 4.93 keV（ACCEPT=3.93）

## 你的任务

1. **合并 Wei 的 `fit_spectral_joint.py` 到我们的 `src/02_spectral/`**
   - 参考源：`weiwwqeo_scripts/src/02_spectral/fit_spectral_joint.py`
   - 关键功能：`--renormalize-blanksky-pha`（9.5-12 keV AREASCAL 重归一化）、`--xrb-policy fixed_shape`、`--fit-min-kev 0.7`
   - 直接从 Wei 的文件复制需保留的三个函数：`_pha_high_energy_renorm_factor()`、`renormalize_blanksky_background_phas()`、`write_joint_sherpa_script()`

2. **在 Abell_0068 上测试**（当前最差情况：T_X=21.6 keV vs ACCEPT=7.99）
   - 先用 local annulus + 新版 Sherpa 脚本测试
   - 再用 blank-sky + 重归一化 + XRB 模型测试
   - 对比两种方案

3. **在 MACSJ0429 上验证**（之前已得到 7.56 keV 的好结果，确认新方法不破坏现有好结果）

4. **对全部 23 团批量运行**
   - 优先用 blank-sky + 重归一化方案
   - 如果某团 blank-sky 生成失败（CALDB 问题），回退到 local annulus

5. **生成最终汇总表 + 更新 pipeline_status.csv**

## 关键文件

- Wei 的脚本：`weiwwqeo_scripts/src/02_spectral/fit_spectral_joint.py`
- Wei 的 README：`weiwwqeo_scripts/src/02_spectral/README_phase3_BC.md`
- Wei 的结果示例：`weiwwqeo_scripts/results/Abell_383/phase3_BC_heRenorm_0p7_7keV/`
- 我们的脚本：`src/02_spectral/fit_spectral_joint.py`
- β-model 脚本：`src/02_spectral/beta_model_profile.py`
- 批量脚本：`src/02_spectral/batch_spectral_joint.py`

## 技术要点

- 必须 `source /data/jyz/Applications/ciao-4.18/ciao-4.18/bin/ciao.sh`
- specextract 使用 `weight=no correctpsf=no bkgresp=no` 避免大区域 ARF 超时
- XRB 模型：`lhb + phabs*(halo + cxb + icm)`，fixed_shape 模式下冻结 kT/Γ 只拟合 norm
- 空白天空 AREASCAL 重归一化原理：比较 9.5-12 keV 源计数 vs 预测背景 → 修正 AREASCAL
- Abell 383 成功参数：`--xrb-policy fixed_shape --renormalize-blanksky-pha --fit-min-kev 0.7`
