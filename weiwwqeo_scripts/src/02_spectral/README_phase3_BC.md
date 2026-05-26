# Phase 3 B+C Spectral Fitting

## English

This folder implements the source+annulus fitting plan:

- `beta_model_profile.py`: extracts a radial surface-brightness profile from the merged flux image, fits a beta model, and estimates `R_EM`, the predicted ICM emission ratio between the annulus and source aperture.
- `fit_spectral_joint.py`: generates blank-sky backgrounds, extracts per-ObsID source and annulus spectra, and runs a two-stage Sherpa fit.
- `batch_spectral_joint.py`: batch wrapper for multiple cluster keys.

The spectral model is:

```text
annulus: lhb + phabs * (halo + cxb + icm_ann)
source:  lhb + phabs * (halo + cxb + icm_src)
```

Important implementation details:

- Spectra are extracted from individual ObsID event files only.
- Merged products are used only for imaging, point-source masks, and beta-profile fitting.
- Source and annulus spectra both use CIAO `blanksky` event files as WSTAT background PHAs.
- The code first does a rough source-only ICM fit to estimate `icm_src.norm`.
- The annulus ICM normalization is frozen to `R_EM * icm_src_prefit.norm` during the annulus XRB fit.
- Annulus-derived XRB normalizations are then frozen and area-scaled into the final source fit.

Run Abell 383 from the project root:

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python src/02_spectral/fit_spectral_joint.py --no-run-repro
```

Fast rerun after spectra exist:

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python src/02_spectral/fit_spectral_joint.py \
  --no-run-repro --no-run-imaging --no-run-blanksky --no-run-specextract
```

Current Abell 383 test output:

```text
chandra_data/Abell_383/processed_joint_bxc/results/Abell_383_phase3_BC_summary.json
chandra_data/Abell_383/processed_joint_bxc/fits/phase3_BC/Abell_383_phase3_BC_fit_results.json
chandra_data/Abell_383/processed_joint_bxc/fits/phase3_BC/Abell_383_phase3_BC_fit_plot.png
chandra_data/Abell_383/processed_joint_bxc/figures/Abell_383_beta_profile.png
chandra_data/Abell_383/processed_joint_bxc/figures/Abell_383_phase3_source_aperture.png
```

Current QA note: Abell 383 gives a finite source temperature, but the annulus XRB fit is formally poor and is flagged with `annulus_xrb_fit_rstat_gt_2`. This means the method is implemented and runnable, but the annulus/XRB model still needs refinement before treating it as final science.

## 中文说明

本目录实现 Phase 3 的 B+C 方案：

- `beta_model_profile.py`：从 merged flux image 提取径向表面亮度 profile，拟合 beta model，并计算 annulus/source 的 ICM 发射比 `R_EM`。
- `fit_spectral_joint.py`：生成 blank-sky 背景，分别提取每个 ObsID 的 source 和 annulus spectra，并运行 Sherpa 两步拟合。
- `batch_spectral_joint.py`：多星系团批量运行脚本。

谱模型为：

```text
annulus: lhb + phabs * (halo + cxb + icm_ann)
source:  lhb + phabs * (halo + cxb + icm_src)
```

实现细节：

- 谱只从 individual ObsID event files 提取，不使用 merged spectra。
- merged products 只用于图像、点源 mask 和 beta-profile 拟合。
- source 和 annulus spectra 都使用 CIAO `blanksky` event files 作为 WSTAT background PHA。
- 代码先做一个粗略 source-only ICM 拟合，估计 `icm_src.norm`。
- 在 annulus XRB 拟合中，`icm_ann.norm` 被固定为 `R_EM * icm_src_prefit.norm`。
- 然后把 annulus 拟合得到的 XRB normalization 冻结，并按 source/annulus 面积比例缩放到最终 source 拟合中。

在项目根目录运行 Abell 383：

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python src/02_spectral/fit_spectral_joint.py --no-run-repro
```

如果 spectra 已经存在，快速重跑 Sherpa/summary：

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python src/02_spectral/fit_spectral_joint.py \
  --no-run-repro --no-run-imaging --no-run-blanksky --no-run-specextract
```

当前 Abell 383 输出：

```text
chandra_data/Abell_383/processed_joint_bxc/results/Abell_383_phase3_BC_summary.json
chandra_data/Abell_383/processed_joint_bxc/fits/phase3_BC/Abell_383_phase3_BC_fit_results.json
chandra_data/Abell_383/processed_joint_bxc/fits/phase3_BC/Abell_383_phase3_BC_fit_plot.png
chandra_data/Abell_383/processed_joint_bxc/figures/Abell_383_beta_profile.png
chandra_data/Abell_383/processed_joint_bxc/figures/Abell_383_phase3_source_aperture.png
```

当前 QA 提醒：Abell 383 的 source 温度是有限的，但 annulus XRB 拟合形式上不好，并被标记为 `annulus_xrb_fit_rstat_gt_2`。也就是说代码路径已经实现并能跑通，但 annulus/XRB 模型还需要进一步调优，不能直接当最终 science result。

## XRB Policy Comparison / XRB 参数自由化对比

The script now supports:

```bash
--xrb-policy fixed_shape
--xrb-policy flexible
```

`fixed_shape` freezes the literature XRB shapes and fits mainly the annulus normalizations. `flexible` frees the LHB, halo, and CXB shape/normalization parameters within conservative bounds:

- `lhb.kT`: `0.07-0.15 keV`, `lhb.norm` free
- `halo.kT`: `0.15-0.35 keV`, `halo.norm` free
- `cxb.PhoIndex`: `1.1-1.7`, `cxb.norm` free

For WSTAT, do not select models by reduced chi-square intuition alone. The JSON records WSTAT, AIC, and BIC; lower AIC/BIC is preferred when comparing these variants.

Current Abell 383 comparison:

| Policy | T_X | Source WSTAT | Source AIC | Source BIC | Annulus WSTAT | Annulus AIC | Annulus BIC | Annulus rstat |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `fixed_shape` | 9.81 keV | 2844.73 | 2848.73 | 2859.10 | 6196.66 | 6202.66 | 6218.22 | 4.70 |
| `flexible` | 9.42 keV | 2835.77 | 2839.77 | 2850.14 | 5807.06 | 5821.06 | 5857.36 | 4.42 |

Interpretation: freeing XRB shape parameters improves WSTAT/AIC/BIC and lowers the fitted temperature, so the fixed-shape assumption was indeed biasing the model. However, the annulus fit remains poor and the flexible solution pushes some parameters to bounds (`cxb.PhoIndex ~ 1.1`, `halo.kT ~ 0.15 keV`), so this is not yet a fully satisfactory background model.

Blank-sky is still used in this implementation. It removes the particle/instrumental background through the CIAO blank-sky PHA and WSTAT machinery. The explicit XRB model then accounts for sky-background mismatch left after blank-sky subtraction/modeling. If blank-sky normalization is wrong, it can still worsen the fit; the next diagnostic should compare high-energy 9.5-12 keV data/blank-sky rates per ObsID and possibly add an extra unvignetted particle-background residual component.

## High-Energy Blank-Sky Renormalization Update

### English

The script now supports a CIAO-style validation/correction for blank-sky particle background normalization:

```bash
--renormalize-blanksky-pha
```

When enabled, the pipeline compares the observed source/annulus PHA and its blank-sky background PHA in the particle-dominated `9.5-12.0 keV` band. It then writes copied spectra under `processed_joint_bxc/spectra_high_energy_renorm/` and adjusts only the copied background PHA `AREASCAL`, so the original `specextract` products are preserved.

Recommended Abell 383 rerun after spectra already exist:

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python src/02_spectral/fit_spectral_joint.py \
  --no-run-repro --no-run-imaging --no-run-blanksky --no-run-specextract \
  --xrb-policy fixed_shape \
  --renormalize-blanksky-pha \
  --fit-min-kev 0.7 --fit-max-kev 7.0
```

Current Abell 383 validated result with this option:

| Variant | T_X | Source WSTAT | Source AIC | Source BIC | Source rstat | L_X bolometric |
|---|---:|---:|---:|---:|---:|---:|
| `fixed_shape`, HE-renorm, `0.7-7 keV` | `4.93 +/- 0.10 keV` | `1664.03` | `1668.03` | `1678.40` | `1.283` | `9.72e44 erg/s` |

This is preferred over the earlier unrenormalized blank-sky fits (`T_X ~ 9-10 keV`) because the hard-band mismatch was driving an artificial hard continuum and therefore an artificially high APEC temperature. The summary JSON records `blanksky_renorm_diagnostics`, including the source counts, predicted blank-sky counts, and renormalization factor for each ObsID/aperture.

### 中文

脚本现在加入了一个更接近 CIAO blank-sky 使用习惯的高能端归一化检查/修正：

```bash
--renormalize-blanksky-pha
```

开启后，pipeline 会在粒子背景主导的 `9.5-12.0 keV` 能段比较观测 PHA 和 blank-sky background PHA。然后它会把 spectra 复制到 `processed_joint_bxc/spectra_high_energy_renorm/`，只修改复制出来的 background PHA 的 `AREASCAL`，不会破坏原始 `specextract` 产物。

Abell 383 spectra 已经存在时，推荐这样重跑：

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python src/02_spectral/fit_spectral_joint.py \
  --no-run-repro --no-run-imaging --no-run-blanksky --no-run-specextract \
  --xrb-policy fixed_shape \
  --renormalize-blanksky-pha \
  --fit-min-kev 0.7 --fit-max-kev 7.0
```

当前 Abell 383 的验证结果：

| Variant | T_X | Source WSTAT | Source AIC | Source BIC | Source rstat | L_X bolometric |
|---|---:|---:|---:|---:|---:|---:|
| `fixed_shape`, 高能端归一化, `0.7-7 keV` | `4.93 +/- 0.10 keV` | `1664.03` | `1668.03` | `1678.40` | `1.283` | `9.72e44 erg/s` |

这比之前未做 blank-sky 高能端归一化时的 `T_X ~ 9-10 keV` 更可信。之前的高温主要来自 hard-band 粒子背景没有被正确归一化，导致谱中出现假的硬连续谱，APEC 温度被推高。summary JSON 中会保存 `blanksky_renorm_diagnostics`，包括每个 ObsID/aperture 的观测计数、blank-sky 预测计数和归一化因子。
