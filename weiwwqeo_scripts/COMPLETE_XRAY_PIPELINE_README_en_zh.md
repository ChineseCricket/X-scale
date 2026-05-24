# Complete Chandra/CIAO Pipeline for `T_X` and `L_X` in R500

## English

### Goal

This pipeline turns raw Chandra observations for one cluster into products for the final scaling-relation project:

- `T_X` from joint Sherpa spectral fitting.
- `L_X` in rest-frame `0.5-2.0 keV` and bolometric `0.01-100 keV` bands.
- Full-R500 and core-excised temperature/luminosity products.
- X-ray image, aperture overlay, spectrum/model/residual plots, and JSON summaries.

The current tested target is `Abell_383`.

### Required Inputs

The main paths are set near the top of `/Users/weiwwqeo/Documents/Observationer/materials/Advanced_obs_astro/final_project/complete_xray_pipeline.py`:

```python
DEFAULT_CLUSTER_KEY = "Abell_383"
DEFAULT_CLUSTER_DIR = PROJECT_DIR / "chandra_data" / "Abell_383"
DEFAULT_CLUSTER_TABLE = PROJECT_DIR / "cluster_center_table.csv"
DEFAULT_OUTPUT_DIRNAME = "processed_pipeline"
```

For Abell 383 the expected input layout is:

```text
chandra_data/Abell_383/raw/524/
chandra_data/Abell_383/raw/2320/
chandra_data/Abell_383/raw/2321/
cluster_center_table.csv
```

The table must provide the cluster center, redshift, `M500c`, and ObsID list. The script computes `R500` from `M500c` and then searches for the X-ray peak near the table/lensing center.

### How To Run

Full run:

```bash
cd /Users/weiwwqeo/Documents/Observationer/materials/Advanced_obs_astro/final_project
/opt/miniconda3/bin/conda run -n ciao-4.18 python complete_xray_pipeline.py
```

Fast resume after event files, images, blank-sky files, and spectra already exist:

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python complete_xray_pipeline.py --no-run-repro --no-run-imaging --no-run-blanksky --no-run-specextract
```

Useful optional overrides:

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python complete_xray_pipeline.py \
  --cluster-key Abell_383 \
  --cluster-dir /absolute/path/to/chandra_data/Abell_383 \
  --cluster-table /absolute/path/to/cluster_center_table.csv
```

### CIAO/Sherpa Workflow

1. `chandra_repro` is run independently for each ObsID. This creates calibrated individual `*_repro_evt2.fits` files.

2. `merge_obs` creates merged imaging products. These merged products are used only for visualization, X-ray peak finding, and point-source detection. They are not used for spectral fitting.

3. `wavdetect` detects compact sources on the merged image. The resulting masks are applied to the spectral apertures, while the central cluster emission is protected from being masked as a point source.

4. `R500` is computed from table `M500c`. The default fitting center is the X-ray peak found near the table/lensing center.

5. Spectra are extracted from individual ObsID event files with `specextract`; each ObsID keeps its own ARF and RMF. This follows the CIAO approach and avoids invalid merged-spectrum responses.

6. Background uses the current `paper_hybrid` mode:

- ACIS-I observations use a same-observation source-free field region, excluding the cluster to `1.2 R500` and excluding detected point sources.
- ACIS-S observations use CIAO `blanksky`, which selects CALDB blank-sky backgrounds, reprojects them to the observation, and applies particle-background weighting.
- Sherpa uses `wstat` with loaded background PHA files. The script does not call `subtract()`; the background is modeled statistically inside the WSTAT likelihood.

7. Sherpa jointly fits all individual spectra with:

```text
xsphabs * xsapec
```

Fixed parameters:

- `nH = 0.0412 x 10^22 cm^-2` by default.
- Redshift from `cluster_center_table.csv`.
- Abundance fixed to `0.3 solar`.

Free parameters:

- ICM temperature `kT`.
- APEC normalization.

Default fit band: observed `0.7-7.0 keV`.

### Apertures

The script currently extracts three apertures:

- `full_r500`: `0-1.0 R500`, used for full-aperture luminosity and comparison.
- `core_excised_0p15_0p5r500`: `0.15-0.5 R500`, currently the adopted no-core Chandra-safe temperature aperture for Abell 383.
- `core_excised_0p15_1r500`: `0.15-1.0 R500`, retained as a diagnostic; for the current Abell 383 data it is background-dominated and should not be adopted.

### Main Outputs

Summary JSON:

```text
chandra_data/Abell_383/processed_pipeline/results/Abell_383_pipeline_summary.json
```

Fit result JSON and plots:

```text
chandra_data/Abell_383/processed_pipeline/fits/full_r500/Abell_383_full_r500_fit_results.json
chandra_data/Abell_383/processed_pipeline/fits/full_r500/Abell_383_full_r500_fit_plot.png
chandra_data/Abell_383/processed_pipeline/fits/core_excised_0p15_0p5r500/Abell_383_core_excised_0p15_0p5r500_fit_results.json
chandra_data/Abell_383/processed_pipeline/fits/core_excised_0p15_0p5r500/Abell_383_core_excised_0p15_0p5r500_fit_plot.png
```

Aperture overlays on the smoothed merged flux image:

```text
chandra_data/Abell_383/processed_pipeline/figures/Abell_383_full_r500_aperture_overlay.png
chandra_data/Abell_383/processed_pipeline/figures/Abell_383_core_excised_0p15_0p5r500_aperture_overlay.png
chandra_data/Abell_383/processed_pipeline/figures/Abell_383_core_excised_0p15_1r500_aperture_overlay.png
```

Per-ObsID spectra used for fitting:

```text
chandra_data/Abell_383/processed_pipeline/spectra/full_r500/Abell_383_obs*_full_r500.pi
chandra_data/Abell_383/processed_pipeline/spectra/core_excised_0p15_0p5r500/Abell_383_obs*_core_excised_0p15_0p5r500.pi
chandra_data/Abell_383/processed_pipeline/spectra/core_excised_0p15_1r500/Abell_383_obs*_core_excised_0p15_1r500.pi
```

The summary JSON also records the exact individual event files, merged image files, source catalog, blank-sky files, per-ObsID background type, and region files.

### Current Abell 383 Test Result

The pipeline was rerun on 2026-05-24 using ObsIDs `524`, `2320`, and `2321`.

Full R500:

- `T_X = 8.06 keV`, 1-sigma `-0.19/+0.24 keV`.
- `L_X(0.5-2 keV, unabsorbed) = 3.59e44 erg/s`.
- `L_bol(unabsorbed) = 1.25e45 erg/s`.
- `rstat = 1.87`; q-value is very low, so formal fit quality is not yet excellent.

Adopted no-core aperture, `0.15-0.5 R500`:

- `T_X = 8.73 keV`, 1-sigma `-0.32/+0.32 keV`.
- `L_X(0.5-2 keV, unabsorbed) = 1.69e44 erg/s`.
- `L_bol(unabsorbed) = 6.10e44 erg/s`.
- `rstat = 1.28`; q-value remains low, but the result is finite and not pegged.

Diagnostic no-core aperture, `0.15-1.0 R500`:

- `T_X = 64 keV`, pegged at the XSAPEC upper bound.
- This aperture is background-dominated for the present data and should not be used as the adopted `T_X`.

These numbers are physically much more plausible than the earlier pure blank-sky full-R500 result, but they are not final publication-quality values. The low q-values mean we should still test background normalization, flare filtering, abundance/NH assumptions, ACIS-I-only fits, radial binning, and possible multi-temperature structure.

### References Followed

- CIAO `chandra_repro`: https://cxc.cfa.harvard.edu/ciao/ahelp/chandra_repro.html
- CIAO `merge_obs`: https://cxc.cfa.harvard.edu/ciao/ahelp/merge_obs.html
- CIAO `wavdetect`: https://cxc.cfa.harvard.edu/ciao/ahelp/wavdetect.html
- CIAO `blanksky`: https://cxc.cfa.harvard.edu/ciao/ahelp/blanksky.html
- CIAO `specextract`: https://cxc.cfa.harvard.edu/ciao/ahelp/specextract.html
- Sherpa manual source/background fitting thread: https://cxc.cfa.harvard.edu/sherpa/threads/manual_source/index.html#brsp
- Sherpa WStat: https://sherpa.readthedocs.io/en/latest/statistics/api/sherpa.stats.WStat.html

---

## 中文说明

### 目标

这个流程把一个星系团的 Chandra 原始观测处理成标度关系需要的物理量：

- 通过 Sherpa 联合谱拟合得到 `T_X`。
- 得到静止系 `0.5-2.0 keV` 和 bolometric `0.01-100 keV` 的 `L_X`。
- 输出完整 R500 和去核 aperture 的结果。
- 输出 X-ray 图像、aperture 叠加图、谱拟合/残差图和 JSON summary。

当前已经测试的目标是 `Abell_383`。

### 必要输入

主要路径写在 `/Users/weiwwqeo/Documents/Observationer/materials/Advanced_obs_astro/final_project/complete_xray_pipeline.py` 开头：

```python
DEFAULT_CLUSTER_KEY = "Abell_383"
DEFAULT_CLUSTER_DIR = PROJECT_DIR / "chandra_data" / "Abell_383"
DEFAULT_CLUSTER_TABLE = PROJECT_DIR / "cluster_center_table.csv"
DEFAULT_OUTPUT_DIRNAME = "processed_pipeline"
```

Abell 383 的输入目录应类似：

```text
chandra_data/Abell_383/raw/524/
chandra_data/Abell_383/raw/2320/
chandra_data/Abell_383/raw/2321/
cluster_center_table.csv
```

表格需要包含星系团中心、红移、`M500c` 和 ObsID 列表。脚本会由 `M500c` 计算 `R500`，并在表格/lensing center 附近寻找 X-ray peak 作为默认谱提取中心。

### 运行方式

完整运行：

```bash
cd /Users/weiwwqeo/Documents/Observationer/materials/Advanced_obs_astro/final_project
/opt/miniconda3/bin/conda run -n ciao-4.18 python complete_xray_pipeline.py
```

如果 event files、图像、blank-sky 和 spectra 已经存在，可以快速续跑拟合和 JSON：

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python complete_xray_pipeline.py --no-run-repro --no-run-imaging --no-run-blanksky --no-run-specextract
```

也可以显式指定输入路径：

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python complete_xray_pipeline.py \
  --cluster-key Abell_383 \
  --cluster-dir /absolute/path/to/chandra_data/Abell_383 \
  --cluster-table /absolute/path/to/cluster_center_table.csv
```

### CIAO/Sherpa 流程

1. 对每个 ObsID 分别运行 `chandra_repro`，生成校准后的 individual `*_repro_evt2.fits`。

2. 用 `merge_obs` 生成合并图像。合并图像只用于显示、找 X-ray peak 和点源探测，不用于谱拟合。

3. 用 `wavdetect` 找紧致源，并在谱提取 aperture 中 mask 掉这些点源。星系团中心区域会被保护，避免把 ICM 核心误删。

4. 根据表格中的 `M500c` 计算 `R500`。默认谱中心为 lensing/table center 附近的 X-ray peak。

5. 对每个 ObsID 的 individual event file 用 `specextract` 分别提谱，每个 ObsID 保留自己的 ARF/RMF。这样符合 CIAO 谱分析流程，也避免 merged spectrum 没有正确单一响应矩阵的问题。

6. 当前背景模式为 `paper_hybrid`：

- ACIS-I 观测使用同一观测中的 source-free field，排除星系团到 `1.2 R500`，并排除点源。
- ACIS-S 观测使用 CIAO `blanksky`，从 CALDB 选 blank-sky 背景，投影到观测坐标，并进行粒子背景归一化。
- Sherpa 使用 `wstat` 并加载 background PHA。脚本不调用 `subtract()`，也就是说背景不是先从谱里硬减掉，而是在 WSTAT 的 Poisson likelihood 中处理。

7. Sherpa 对所有 individual spectra 做联合拟合：

```text
xsphabs * xsapec
```

固定参数：

- Galactic absorption 默认 `nH = 0.0412 x 10^22 cm^-2`。
- 红移来自 `cluster_center_table.csv`。
- 金属丰度固定为 `0.3 solar`。

自由参数：

- ICM 温度 `kT`。
- APEC normalization。

默认拟合能段：观测系 `0.7-7.0 keV`。

### Aperture 设置

脚本目前提取三个 aperture：

- `full_r500`：`0-1.0 R500`，用于完整 aperture 的光度和对比。
- `core_excised_0p15_0p5r500`：`0.15-0.5 R500`，当前作为 Abell 383 的 adopted no-core / Chandra-safe 温度 aperture。
- `core_excised_0p15_1r500`：`0.15-1.0 R500`，只保留为诊断；在当前 Abell 383 数据里受背景主导，不应采用。

### 主要输出

总 summary JSON：

```text
chandra_data/Abell_383/processed_pipeline/results/Abell_383_pipeline_summary.json
```

拟合结果 JSON 和图：

```text
chandra_data/Abell_383/processed_pipeline/fits/full_r500/Abell_383_full_r500_fit_results.json
chandra_data/Abell_383/processed_pipeline/fits/full_r500/Abell_383_full_r500_fit_plot.png
chandra_data/Abell_383/processed_pipeline/fits/core_excised_0p15_0p5r500/Abell_383_core_excised_0p15_0p5r500_fit_results.json
chandra_data/Abell_383/processed_pipeline/fits/core_excised_0p15_0p5r500/Abell_383_core_excised_0p15_0p5r500_fit_plot.png
```

Aperture 叠加图：

```text
chandra_data/Abell_383/processed_pipeline/figures/Abell_383_full_r500_aperture_overlay.png
chandra_data/Abell_383/processed_pipeline/figures/Abell_383_core_excised_0p15_0p5r500_aperture_overlay.png
chandra_data/Abell_383/processed_pipeline/figures/Abell_383_core_excised_0p15_1r500_aperture_overlay.png
```

用于拟合的每个 ObsID spectra：

```text
chandra_data/Abell_383/processed_pipeline/spectra/full_r500/Abell_383_obs*_full_r500.pi
chandra_data/Abell_383/processed_pipeline/spectra/core_excised_0p15_0p5r500/Abell_383_obs*_core_excised_0p15_0p5r500.pi
chandra_data/Abell_383/processed_pipeline/spectra/core_excised_0p15_1r500/Abell_383_obs*_core_excised_0p15_1r500.pi
```

summary JSON 还会记录实际使用的 individual event files、merged image files、source catalog、blank-sky files、每个 ObsID 的背景类型和 region files。

### 当前 Abell 383 测试结果

流程在 2026-05-24 重新跑通，使用 ObsID `524`, `2320`, `2321`。

完整 R500：

- `T_X = 8.06 keV`，1-sigma `-0.19/+0.24 keV`。
- `L_X(0.5-2 keV, unabsorbed) = 3.59e44 erg/s`。
- `L_bol(unabsorbed) = 1.25e45 erg/s`。
- `rstat = 1.87`；q-value 很低，所以形式上的拟合质量还不够理想。

采用的去核 aperture，`0.15-0.5 R500`：

- `T_X = 8.73 keV`，1-sigma `-0.32/+0.32 keV`。
- `L_X(0.5-2 keV, unabsorbed) = 1.69e44 erg/s`。
- `L_bol(unabsorbed) = 6.10e44 erg/s`。
- `rstat = 1.28`；q-value 仍低，但结果是有限的，没有顶到模型上限。

诊断去核 aperture，`0.15-1.0 R500`：

- `T_X = 64 keV`，顶到 XSAPEC 上限。
- 这个 aperture 在当前数据中被背景主导，不应作为 adopted `T_X`。

这些结果比之前纯 blank-sky 背景下的 full-R500 异常高温更合理，但仍不是最终发表级 science value。低 q-value 提醒我们还要继续检查背景归一化、flare filtering、abundance/NH 假设、只用 ACIS-I 的拟合、径向分 bin，以及多温结构。

### 参考文档

- CIAO `chandra_repro`: https://cxc.cfa.harvard.edu/ciao/ahelp/chandra_repro.html
- CIAO `merge_obs`: https://cxc.cfa.harvard.edu/ciao/ahelp/merge_obs.html
- CIAO `wavdetect`: https://cxc.cfa.harvard.edu/ciao/ahelp/wavdetect.html
- CIAO `blanksky`: https://cxc.cfa.harvard.edu/ciao/ahelp/blanksky.html
- CIAO `specextract`: https://cxc.cfa.harvard.edu/ciao/ahelp/specextract.html
- Sherpa manual source/background fitting thread: https://cxc.cfa.harvard.edu/sherpa/threads/manual_source/index.html#brsp
- Sherpa WStat: https://sherpa.readthedocs.io/en/latest/statistics/api/sherpa.stats.WStat.html
