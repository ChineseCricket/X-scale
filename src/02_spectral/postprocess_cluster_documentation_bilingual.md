# Post-processing Chandra Cluster Spectra for Lx-M500 and Tx-M500

中文说明见下半部分。

## 1. Purpose

`postprocess_cluster.py` post-processes one already-reduced Chandra cluster directory and extracts the quantities needed for the cluster scaling-relation project:

- `R500` from an external `M500` and redshift.
- A quick-look observed-band X-ray luminosity from the exposure-corrected flux image.
- Per-exposure source and background spectra inside `R500`.
- A joint Sherpa spectral fit using an absorbed APEC thermal plasma model.
- A diagnostic data/model/residual plot for visual fit checking.
- JSON/CSV outputs for later scaling-relation analysis.

The key design choice is that the script does **not** fit a spectrum from the merged event file. Each ObsID keeps its own event file, background spectrum, ARF, and RMF.

## 2. Why Individual Exposures Are Used

A merged Chandra event file is useful for imaging and quick-look counts, but it does not have one physically meaningful response. Different observations can have different:

- aimpoints;
- roll angles;
- detector chips;
- bad-pixel maps;
- exposure maps;
- effective areas;
- redistribution matrices.

Therefore, spectral extraction is done separately for each individual exposure:

```text
cluster209/raw/3579/repro/acisf03579_repro_evt2.fits
cluster209/raw/522/repro/acisf00522_repro_evt2.fits
```

The joint Sherpa fit then loads both spectra simultaneously and applies one shared ICM model while preserving each ObsID's own ARF/RMF response.

## 3. Files Used By Default

For Abell 0209, the default script settings use:

```text
postprocess_cluster.py
cluster_center_table.csv
cluster209/merged_clean_evt.fits
cluster209/clean_fluxed/flux_clean.img
cluster209/clean_fluxed/flux_csmooth.img
cluster209/src.fits
cluster209/raw/*/repro/*_repro_evt2.fits
```

The cluster metadata are read from:

```text
cluster_center_table.csv
```

This table provides the cluster center, redshift, mass, and ObsIDs. The default target is set near the top of the script:

```python
DEFAULT_CLUSTER_KEY = "Abell_0209"
```

## 3.1 Required Input Files And Path Settings

For clarity, the important input paths are explicit settings near the top of `postprocess_cluster.py`. The script assumes you run it from the project directory:

```text
/Users/weiwwqeo/Documents/Observationer/materials/Advanced_obs_astro/final_project
```

The key path settings are:

```python
DEFAULT_CLUSTER_KEY = "Abell_0209"
DEFAULT_CLUSTER_DIR = Path("cluster209")
CLUSTER_TABLE_PATH = Path("cluster_center_table.csv")
DEFAULT_INDIVIDUAL_EVT_GLOB = "raw/*/repro/*_repro_evt2.fits"
DEFAULT_MERGED_EVT = "merged_clean_evt.fits"
DEFAULT_FLUX_IMAGE = "clean_fluxed/flux_clean.img"
DEFAULT_APERTURE_PLOT_IMAGE = "clean_fluxed/flux_csmooth.img"
DEFAULT_POINT_SOURCE_FILE = "src.fits"
```

Required inputs:

- `CLUSTER_TABLE_PATH`: the cluster table containing RA, Dec, redshift, `M500`, and ObsIDs.
- `DEFAULT_CLUSTER_DIR`: the processed cluster folder.
- `DEFAULT_INDIVIDUAL_EVT_GLOB`: the per-ObsID evt2 files used to create and fit spectra.
- `DEFAULT_MERGED_EVT`: the merged event file used only for image/count diagnostics. It is not used for spectral fitting.

Optional but recommended inputs:

- `DEFAULT_FLUX_IMAGE`: image used for quick-look aperture flux/luminosity.
- `DEFAULT_APERTURE_PLOT_IMAGE`: image used to draw the R500 aperture layout.
- `DEFAULT_POINT_SOURCE_FILE`: CIAO `wavdetect` source table used for point-source masking.

For the current Abell 0209 run, these resolve to:

```text
cluster table:        cluster_center_table.csv
cluster directory:    cluster209
individual evt2:      cluster209/raw/3579/repro/acisf03579_repro_evt2.fits
                      cluster209/raw/522/repro/acisf00522_repro_evt2.fits
merged evt:           cluster209/merged_clean_evt.fits
flux image:           cluster209/clean_fluxed/flux_clean.img
aperture image:       cluster209/clean_fluxed/flux_csmooth.img
point-source table:   cluster209/src.fits
output directory:     cluster209/postprocess_r500
```

You can override these paths on the command line if needed:

```bash
python postprocess_cluster.py /path/to/cluster_dir
python postprocess_cluster.py --flux-image /path/to/flux.img
python postprocess_cluster.py --aperture-plot-image /path/to/display.img
python postprocess_cluster.py --evt merged_clean_evt.fits
python postprocess_cluster.py --point-source-file src.fits
python postprocess_cluster.py --individual-evt-glob "raw/*/repro/*_repro_evt2.fits"
```

At the end of every run, the script prints a `Resolved path settings` block and a `Files used` block. Check those blocks first if you are unsure which files were used. You can still set `--individual-evt-glob AUTO` if you want the older multi-pattern auto-discovery fallback.

## 4. Main User Settings In The Script

The script is designed so normal choices can be edited directly near the top of `postprocess_cluster.py` instead of being typed on the command line.

Important settings include:

```python
DEFAULT_CLUSTER_KEY = "Abell_0209"
DEFAULT_CLUSTER_DIR = Path("cluster209")
CLUSTER_TABLE_PATH = Path("cluster_center_table.csv")
DEFAULT_INDIVIDUAL_EVT_GLOB = "raw/*/repro/*_repro_evt2.fits"
DEFAULT_MERGED_EVT = "merged_clean_evt.fits"
DEFAULT_FLUX_IMAGE = "clean_fluxed/flux_clean.img"
DEFAULT_APERTURE_PLOT_IMAGE = "clean_fluxed/flux_csmooth.img"
DEFAULT_POINT_SOURCE_FILE = "src.fits"
DEFAULT_RUN_SPECEXTRACT = False
DEFAULT_RUN_SHERPA = False
DEFAULT_SHERPA_BACKGROUND_MODE = "wstat"
DEFAULT_ENERGY_MIN_KEV = 0.5
DEFAULT_ENERGY_MAX_KEV = 7.0
DEFAULT_BKG_INNER_R500 = 1.2
DEFAULT_BKG_OUTER_R500 = 1.8
DEFAULT_EXCISE_CORE = False
DEFAULT_CORE_INNER_R500 = 0.15
DEFAULT_CENTER_MODE = "xray_peak"
DEFAULT_XRAY_PEAK_SEARCH_ARCSEC = 120.0
DEFAULT_MASK_POINT_SOURCES = True
DEFAULT_POINT_SOURCE_SIGMA_MIN = 5.0
DEFAULT_SPECEXTRACT_CORRECTPSF = "no"
DEFAULT_SPECEXTRACT_WEIGHT = "no"
DEFAULT_SPECEXTRACT_BKGRESP = "no"
```

`DEFAULT_SPECEXTRACT_WEIGHT = "no"` is currently the practical default because `weight=yes` can call `mkwarf` over the whole large `R500` aperture and become extremely slow. `weight=no` builds a single response at the aperture center, which is faster and works well for a first-pass project pipeline. For final publication-quality work, response weighting and aperture/systematic tests should be revisited.

`DEFAULT_EXCISE_CORE` controls whether the spectral source aperture includes the cluster center. If it is `False`, the source is a circle from `0-R500`. If it is `True`, the source is an annulus from `DEFAULT_CORE_INNER_R500 * R500` to `R500`. A common scaling-relation choice is to use a core-excised temperature, for example `0.15R500-R500`, because cool cores can bias the global temperature.

`DEFAULT_CENTER_MODE = "xray_peak"` means the script starts from the catalog/table center and then finds the local X-ray peak within `DEFAULT_XRAY_PEAK_SEARCH_ARCSEC`. Other allowed modes are `catalog` and `manual`. The chosen center, catalog center, and offset are written to the summary JSON/CSV. Products include the center mode in the filename, for example `r500_xray_peak`, so spectra from different center choices are not mixed.

`DEFAULT_MASK_POINT_SOURCES = True` makes the script read the CIAO `wavdetect` source table, usually `src.fits`, and exclude significant compact sources from both the source and background spectral regions. The default threshold is conservative, `SRC_SIGNIFICANCE >= 5`, because the wavdetect list can include weak detections and diffuse cluster substructure. The aperture overlay marks masked sources in red, and masked products include `psmask` in the filename.

`DEFAULT_SHERPA_BACKGROUND_MODE = "wstat"` is now the default Sherpa background treatment. In this mode the script does **not** call `subtract(i)`. Sherpa loads each source PHA and its matching background PHA, then fits with WSTAT, a Poisson source+background likelihood for PHA data. This is safer than subtracting a noisy or source-contaminated background spectrum, and it keeps the background treatment inside the fit statistic. The old comparison mode is still available with `--sherpa-background-mode subtract`.

## 5. How To Run

Activate or use the CIAO conda environment:

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python postprocess_cluster.py
```

The command above performs quick-look post-processing only, unless `DEFAULT_RUN_SPECEXTRACT` and `DEFAULT_RUN_SHERPA` are changed in the script.

To run the full extraction and fit explicitly:

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python postprocess_cluster.py --run-specextract --run-sherpa
```

To rerun only the Sherpa fit and plot using existing per-ObsID spectra:

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python postprocess_cluster.py --no-run-specextract --run-sherpa
```

To compare against the old background-subtracted fit:

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python postprocess_cluster.py --no-run-specextract --run-sherpa --sherpa-background-mode subtract
```

To run a core-excised extraction and fit:

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python postprocess_cluster.py --excise-core --core-inner-r500 0.15 --run-specextract --run-sherpa
```

Core-excised outputs use a separate filename tag, `r500_coreexcised`, so they do not overwrite the full-`R500` spectra and fit files.

To force the catalog/table center:

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python postprocess_cluster.py --center-mode catalog --run-specextract --run-sherpa
```

To use a manual center:

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python postprocess_cluster.py --center-mode manual --center-ra 22.9703 --center-dec -13.6147 --run-specextract --run-sherpa
```

To process another cluster, the usual workflow is:

1. Add or check the cluster row in `cluster_center_table.csv`.
2. Add a data-directory alias in `CLUSTER_DATA_DIRS` if the folder name does not match the cluster key.
3. Set `DEFAULT_CLUSTER_KEY` to the desired cluster key.
4. Run the script in the CIAO environment.

## 6. Step-by-step Workflow

### Step 1: Load Cluster Parameters

The script reads the chosen cluster from `cluster_center_table.csv`. It obtains:

- cluster name/key;
- center RA and Dec;
- redshift;
- input `M500`;
- whether `M500` is in `h^-1 Msun`;
- ObsIDs.

If the table says the mass is in `h^-1 Msun`, the script converts it to physical solar masses using the configured `H0`.

### Step 2: Compute R500

The script computes `R500` from:

```text
M500 = (4/3) pi R500^3 500 rho_crit(z)
```

where `rho_crit(z)` is the critical density at the cluster redshift. It then converts `R500` from Mpc to angular size in arcsec using the angular-diameter distance.

For the current Abell 0209 run, the output is approximately:

```text
R500 = 1.523 Mpc
R500 = 451.10 arcsec
```

### Step 3: Write Source And Background Regions

The source region is a circle centered on the cluster:

```text
radius = R500
```

The background region is a local annulus:

```text
inner radius = 1.2 R500
outer radius = 1.8 R500
```

The output DS9 region files are written to:

```text
cluster209/postprocess_r500/Abell_0209_r500_src.reg
cluster209/postprocess_r500/Abell_0209_r500_bkg.reg
```

If core masking is enabled, the source region becomes:

```text
cluster209/postprocess_r500/Abell_0209_r500_coreexcised_src.reg
```

and the source aperture is an annulus rather than a circle.

For spectral extraction, the script also computes the center separately in each ObsID's physical pixel coordinate system. This matters because different ObsIDs can have different WCS mappings.

The script also writes an aperture overlay plot on a cluster image:

```text
cluster209/postprocess_r500/Abell_0209_r500_aperture_overlay.png
cluster209/postprocess_r500/Abell_0209_r500_coreexcised_aperture_overlay.png
```

This figure shows the outer `R500` source boundary, the optional masked core, the background annulus, and the cluster center. It is meant as a quick visual check that the fitted aperture is actually where expected on the image.

If point-source masking is enabled, the same figure also marks excluded wavdetect sources with red circles. These are subtracted from the CIAO region expression passed to `specextract`, for both source and background spectra.

### Step 4: Quick-look Flux And Luminosity

The script sums the exposure-corrected flux image inside `R500` and estimates:

```text
L = 4 pi D_L^2 F
```

This is a quick-look observed-band luminosity. It is useful for sanity checks, but it is not yet a fully model-derived, rest-frame, k-corrected luminosity.

For the current Abell 0209 run:

```text
aperture_flux_erg_s_cm2 = 1.140e-11
aperture_luminosity_erg_s = 1.400e45
```

Important caveat: the current luminosity uses the flux image and an approximate conversion when the image is photon-flux-like. For final scaling-relation values, a model-based flux/luminosity from the spectral fit would be better.

### Step 5: Discover Individual Event Files

The script searches for per-exposure event files using patterns such as:

```text
raw/*/repro/*_repro_evt2.fits
```

For Abell 0209, it finds:

```text
cluster209/raw/3579/repro/acisf03579_repro_evt2.fits
cluster209/raw/522/repro/acisf00522_repro_evt2.fits
```

### Step 6: Extract Spectra With CIAO specextract

For each individual ObsID, the script calls CIAO `specextract` separately. Example structure:

```bash
specextract \
  infile=<evt2>[sky=circle(x,y,r)] \
  bkgfile=<evt2>[sky=annulus(x,y,rinner,router)] \
  outroot=<output_prefix> \
  correctpsf=no \
  weight=no \
  bkgresp=no \
  clobber=yes
```

The important part is that each ObsID gets its own spectrum and response files:

```text
Abell_0209_obs3579_r500.pi
Abell_0209_obs3579_r500_bkg.pi
Abell_0209_obs3579_r500.arf
Abell_0209_obs3579_r500.rmf

Abell_0209_obs522_r500.pi
Abell_0209_obs522_r500_bkg.pi
Abell_0209_obs522_r500.arf
Abell_0209_obs522_r500.rmf
```

### Step 7: Write And Run The Sherpa Joint Fit Script

The post-processing script writes a Sherpa script:

```text
cluster209/postprocess_r500/fit_Abell_0209_r500_sherpa.py
```

The Sherpa script loads all individual spectra and applies one shared model:

```text
xsphabs * xsapec
```

The current choices are:

- Galactic `NH` fixed;
- redshift fixed;
- abundance initially fixed at `0.3 Zsun`;
- temperature free;
- APEC normalization free;
- default fit statistic `wstat`;
- default background treatment: non-subtractive Sherpa source+background likelihood using the background PHA;
- fitting band `0.7-7.0 keV`.

The fit is joint: all spectra constrain the same cluster temperature, but each spectrum uses its own ARF/RMF.

With `DEFAULT_SHERPA_BACKGROUND_MODE = "wstat"`, the generated Sherpa script does not subtract the background. It keeps the source and background spectra as Poisson measurements and lets WSTAT handle the background likelihood. This is not the same as building a detailed physical background-component model with `set_full_model` and `set_bkg_full_model`; that more advanced route requires carefully response-folded background components, and usually `specextract bkgresp=yes` products. The current default is the robust CIAO/Sherpa first-pass choice for the data products already created here.

### Step 8: Make The Diagnostic Fit Plot

After fitting, the Sherpa script creates:

```text
cluster209/postprocess_r500/Abell_0209_r500_fit_plot.png
```

The plot has:

- top panel: data and model for each ObsID;
- bottom panel: residuals for each ObsID.

Use this plot like an X-ray version of an SED-fit diagnostic plot: the model should follow the observed spectral shape, and residuals should be randomly scattered around zero.

### Step 9: Write Results

Main result files are:

```text
cluster209/postprocess_r500/Abell_0209_r500_summary.json
cluster209/postprocess_r500/Abell_0209_r500_summary.csv
cluster209/postprocess_r500/Abell_0209_r500_fit_results.json
cluster209/postprocess_r500/Abell_0209_r500_fit_plot.png
cluster209/postprocess_r500/Abell_0209_r500_aperture_overlay.png
```

The summary JSON/CSV stores aperture information, quick-look luminosity, spectra used, and links to fit outputs. The fit-results JSON stores the spectral fit parameters and diagnostics.

The final terminal output also lists the aperture layout X-ray image explicitly as `aperture layout X-ray image`, so after each run you can immediately inspect the exact `R500` source aperture, optional core mask, point-source masks, and background annulus used for the spectral extraction.

It also prints a `Files used` block showing the merged event file used only for image/count diagnostics, the individual event files used for per-ObsID spectral products, and the individual spectra loaded by Sherpa.

For the default WSTAT mode, fit products include the `wstat` tag, for example:

```text
cluster209/postprocess_r500/Abell_0209_r500_xray_peak_psmask_wstat_fit_results.json
cluster209/postprocess_r500/Abell_0209_r500_xray_peak_psmask_wstat_fit_plot.png
```

For a core-excised run, corresponding files include the `r500_coreexcised` tag, for example:

```text
cluster209/postprocess_r500/Abell_0209_r500_coreexcised_summary.json
cluster209/postprocess_r500/Abell_0209_r500_coreexcised_fit_results.json
cluster209/postprocess_r500/Abell_0209_r500_coreexcised_fit_plot.png
cluster209/postprocess_r500/Abell_0209_r500_coreexcised_aperture_overlay.png
```

## 7. Current Fit Diagnostics In JSON

The fit-results JSON includes fields such as:

```json
{
  "temperature_keV": 20.263,
  "statname": "wstat",
  "sherpa_background_mode": "wstat",
  "rstat": 1.204,
  "q_value": 3.16e-05,
  "fit_quality_flag": "high_reduced_statistic_check_model_background_or_calibration",
  "confidence_intervals": {
    "icm.kT": {
      "best": 20.263,
      "lower_delta_1sigma": -1.518,
      "upper_delta_1sigma": 2.210
    }
  },
  "residual_summaries": [
    {
      "dataset_id": 1,
      "mean_residual": 0.0038,
      "rms_residual": 0.0369,
      "max_abs_residual": 0.1739
    }
  ]
}
```

These diagnostics are meant to make later batch processing easier. They do not replace visual inspection.

## 8. How To Evaluate The X-ray Fit

Check both statistics and physical behavior.

Good signs:

- data and model follow the same broad spectral shape;
- residuals scatter around zero;
- the two ObsIDs are mutually consistent;
- confidence intervals are finite;
- fitted temperature is plausible for the cluster mass.

Things to investigate:

- `reduced chi2` much larger than 1: possible poor model, background problem, calibration issue, or missing physics;
- `reduced chi2` much smaller than 1: possible conservative errors, over-grouping, or statistic choice;
- for WSTAT, use the reduced statistic and residual plot as diagnostics, but remember the fit is not a simple chi-square goodness-of-fit test;
- high-energy residual trends: possible background mismatch;
- residuals near the Fe-K complex: possible temperature, abundance, or calibration issue;
- large differences between ObsIDs: possible response, background, or extraction-region problem.

For Abell 0209, the current fit gives:

```text
T_X = 20.26 keV
1-sigma interval approximately -1.52 / +2.21 keV
WSTAT reduced statistic = 1.204
```

This is a successful non-subtractive fit, but the temperature is high for Abell 0209 and the statistic is slightly high, so the JSON flags it for checking the background, aperture, model assumptions, and possible cluster/background contamination.

## 9. Scientific Caveats

For a class project, this pipeline is a strong first-pass analysis. For more rigorous science, consider:

- point-source masking before spectral extraction;
- testing local vs blank-sky background;
- using `WSTAT`/Cash statistics for low-count or background-dominated spectra;
- extracting core-excised temperature, e.g. `0.15R500-R500`, for scaling-relation comparison;
- freeing abundance if the data quality supports it;
- computing model-derived rest-frame luminosity in a standard band;
- testing `specextract weight=yes` or weighted responses if runtime permits;
- checking chip gaps and background-region contamination.

---

# 用于 Lx-M500 和 Tx-M500 的 Chandra 星系团后处理流程

## 1. 目的

`postprocess_cluster.py` 用于对已经完成 CIAO 初步处理的 Chandra 星系团数据做后处理，并提取标度关系项目需要的量：

- 根据外部给定的 `M500` 和红移计算 `R500`。
- 从 exposure-corrected flux image 中估计一个快速检查用的 X 射线光度。
- 在 `R500` 内为每个 exposure 单独抽取源光谱和背景光谱。
- 使用 Sherpa 对多个 exposure 光谱做联合拟合。
- 生成 data/model/residual 诊断图，用于检查拟合好坏。
- 输出 JSON/CSV，方便后续做 `L_X-M500` 和 `T_X-M500` 标度关系。

最重要的设计原则是：脚本**不使用 merged event file 抽取的合并光谱来拟合温度**。每个 ObsID 都保留自己的 event file、background spectrum、ARF 和 RMF。

## 2. 为什么要使用单独的 exposure

合并后的 Chandra event file 对成像和快速计数很有用，但它没有一个唯一且物理正确的响应文件。不同观测可能有不同的：

- aimpoint；
- roll angle；
- 探测器芯片；
- bad-pixel map；
- exposure map；
- effective area；
- redistribution matrix。

因此，光谱必须从每个单独的 exposure 中分别抽取：

```text
cluster209/raw/3579/repro/acisf03579_repro_evt2.fits
cluster209/raw/522/repro/acisf00522_repro_evt2.fits
```

之后 Sherpa 会同时加载这些光谱，用同一个 ICM 物理模型进行联合拟合，但每个 ObsID 仍然使用自己的 ARF/RMF。

## 3. 默认使用的文件

对于 Abell 0209，当前默认设置使用：

```text
postprocess_cluster.py
cluster_center_table.csv
cluster209/merged_clean_evt.fits
cluster209/clean_fluxed/flux_clean.img
cluster209/clean_fluxed/flux_csmooth.img
cluster209/src.fits
cluster209/raw/*/repro/*_repro_evt2.fits
```

星系团参数来自：

```text
cluster_center_table.csv
```

这个表格给出星系团中心、红移、质量和 ObsID。默认目标在脚本开头设置：

```python
DEFAULT_CLUSTER_KEY = "Abell_0209"
```

## 3.1 需要哪些输入文件，以及路径如何设置？

为了更清楚，重要输入路径都放在 `postprocess_cluster.py` 开头作为显式设置。脚本假设你从项目目录运行：

```text
/Users/weiwwqeo/Documents/Observationer/materials/Advanced_obs_astro/final_project
```

关键路径设置为：

```python
DEFAULT_CLUSTER_KEY = "Abell_0209"
DEFAULT_CLUSTER_DIR = Path("cluster209")
CLUSTER_TABLE_PATH = Path("cluster_center_table.csv")
DEFAULT_INDIVIDUAL_EVT_GLOB = "raw/*/repro/*_repro_evt2.fits"
DEFAULT_MERGED_EVT = "merged_clean_evt.fits"
DEFAULT_FLUX_IMAGE = "clean_fluxed/flux_clean.img"
DEFAULT_APERTURE_PLOT_IMAGE = "clean_fluxed/flux_csmooth.img"
DEFAULT_POINT_SOURCE_FILE = "src.fits"
```

必需输入：

- `CLUSTER_TABLE_PATH`：星系团表格，包含 RA、Dec、红移、`M500` 和 ObsIDs。
- `DEFAULT_CLUSTER_DIR`：已经处理好的星系团数据目录。
- `DEFAULT_INDIVIDUAL_EVT_GLOB`：每个 ObsID 的 evt2 文件，用于抽取和拟合光谱。
- `DEFAULT_MERGED_EVT`：merged event file，只用于图像/计数诊断，不用于光谱拟合。

可选但推荐的输入：

- `DEFAULT_FLUX_IMAGE`：用于快速估计 aperture flux/luminosity 的图像。
- `DEFAULT_APERTURE_PLOT_IMAGE`：用于画 R500 aperture layout 的图像。
- `DEFAULT_POINT_SOURCE_FILE`：CIAO `wavdetect` source table，用于点源 mask。

当前 Abell 0209 运行中，这些路径会解析为：

```text
cluster table:        cluster_center_table.csv
cluster directory:    cluster209
individual evt2:      cluster209/raw/3579/repro/acisf03579_repro_evt2.fits
                      cluster209/raw/522/repro/acisf00522_repro_evt2.fits
merged evt:           cluster209/merged_clean_evt.fits
flux image:           cluster209/clean_fluxed/flux_clean.img
aperture image:       cluster209/clean_fluxed/flux_csmooth.img
point-source table:   cluster209/src.fits
output directory:     cluster209/postprocess_r500
```

如果需要，也可以用命令行覆盖这些路径：

```bash
python postprocess_cluster.py /path/to/cluster_dir
python postprocess_cluster.py --flux-image /path/to/flux.img
python postprocess_cluster.py --aperture-plot-image /path/to/display.img
python postprocess_cluster.py --evt merged_clean_evt.fits
python postprocess_cluster.py --point-source-file src.fits
python postprocess_cluster.py --individual-evt-glob "raw/*/repro/*_repro_evt2.fits"
```

每次运行结束时，脚本都会打印 `Resolved path settings` 和 `Files used` 两个区块。如果不确定用了哪些文件，优先看这两个区块。如果想使用旧的多模式自动寻找 individual evt2 文件，可以设置 `--individual-evt-glob AUTO`。

## 4. 脚本中的主要参数

日常使用时，可以直接修改 `postprocess_cluster.py` 开头附近的参数，而不必每次写很长的命令行。

重要参数包括：

```python
DEFAULT_CLUSTER_KEY = "Abell_0209"
DEFAULT_CLUSTER_DIR = Path("cluster209")
CLUSTER_TABLE_PATH = Path("cluster_center_table.csv")
DEFAULT_INDIVIDUAL_EVT_GLOB = "raw/*/repro/*_repro_evt2.fits"
DEFAULT_MERGED_EVT = "merged_clean_evt.fits"
DEFAULT_FLUX_IMAGE = "clean_fluxed/flux_clean.img"
DEFAULT_APERTURE_PLOT_IMAGE = "clean_fluxed/flux_csmooth.img"
DEFAULT_POINT_SOURCE_FILE = "src.fits"
DEFAULT_RUN_SPECEXTRACT = False
DEFAULT_RUN_SHERPA = False
DEFAULT_SHERPA_BACKGROUND_MODE = "wstat"
DEFAULT_ENERGY_MIN_KEV = 0.5
DEFAULT_ENERGY_MAX_KEV = 7.0
DEFAULT_BKG_INNER_R500 = 1.2
DEFAULT_BKG_OUTER_R500 = 1.8
DEFAULT_EXCISE_CORE = False
DEFAULT_CORE_INNER_R500 = 0.15
DEFAULT_CENTER_MODE = "xray_peak"
DEFAULT_XRAY_PEAK_SEARCH_ARCSEC = 120.0
DEFAULT_MASK_POINT_SOURCES = True
DEFAULT_POINT_SOURCE_SIGMA_MIN = 5.0
DEFAULT_SPECEXTRACT_CORRECTPSF = "no"
DEFAULT_SPECEXTRACT_WEIGHT = "no"
DEFAULT_SPECEXTRACT_BKGRESP = "no"
```

当前 `DEFAULT_SPECEXTRACT_WEIGHT = "no"` 是实用默认值，因为 `weight=yes` 会在很大的 `R500` 区域上调用 `mkwarf`，可能非常慢。`weight=no` 使用 aperture center 处的单一响应，速度快，适合项目中的第一轮批处理。若要做更严格的论文级分析，应重新测试 response weighting 和 aperture/systematic effects。

`DEFAULT_EXCISE_CORE` 控制光谱源区是否包含星系团中心。如果是 `False`，源区就是 `0-R500` 的圆。如果是 `True`，源区会变成从 `DEFAULT_CORE_INNER_R500 * R500` 到 `R500` 的环形区域。标度关系中经常使用 core-excised temperature，例如 `0.15R500-R500`，因为 cool core 可能会影响全局温度。

`DEFAULT_CENTER_MODE = "xray_peak"` 表示脚本先从 catalog/table center 出发，然后在 `DEFAULT_XRAY_PEAK_SEARCH_ARCSEC` 范围内寻找局部 X-ray peak。其他可选模式是 `catalog` 和 `manual`。实际使用的中心、catalog center 和二者偏移量都会写入 summary JSON/CSV。输出文件名中会包含 center mode，例如 `r500_xray_peak`，避免不同中心选择的 spectra 被混用。

`DEFAULT_MASK_POINT_SOURCES = True` 会让脚本读取 CIAO `wavdetect` 的 source table，通常是 `src.fits`，并从源区和背景区中排除显著的 compact sources。默认阈值比较保守，为 `SRC_SIGNIFICANCE >= 5`，因为 wavdetect 列表可能包含弱源以及弥散星系团结构。aperture overlay 会用红圈标记被 mask 的源，相关输出文件名中会包含 `psmask`。

`DEFAULT_SHERPA_BACKGROUND_MODE = "wstat"` 是现在默认的 Sherpa 背景处理方式。在这个模式下，脚本不会调用 `subtract(i)` 做背景扣除。Sherpa 会同时加载 source PHA 和对应的 background PHA，并用 WSTAT 进行拟合。WSTAT 是适合 PHA 数据的 Poisson source+background likelihood，它把背景作为拟合统计量的一部分处理，而不是先把背景计数减掉。旧的背景扣除模式仍可用：`--sherpa-background-mode subtract`。

## 5. 如何运行

使用 CIAO conda 环境运行：

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python postprocess_cluster.py
```

上面的命令只做快速后处理，除非你在脚本中把 `DEFAULT_RUN_SPECEXTRACT` 和 `DEFAULT_RUN_SHERPA` 改成 `True`。

显式运行完整光谱抽取和拟合：

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python postprocess_cluster.py --run-specextract --run-sherpa
```

如果已经有 per-ObsID 光谱，只想重新跑 Sherpa 拟合和画图：

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python postprocess_cluster.py --no-run-specextract --run-sherpa
```

如果想和旧的背景扣除拟合做对比：

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python postprocess_cluster.py --no-run-specextract --run-sherpa --sherpa-background-mode subtract
```

运行 core-excised 光谱抽取和拟合：

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python postprocess_cluster.py --excise-core --core-inner-r500 0.15 --run-specextract --run-sherpa
```

core-excised 输出会带有单独的 `r500_coreexcised` 文件名标签，因此不会覆盖完整 `R500` 的 spectra 和 fit 文件。

强制使用 catalog/table center：

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python postprocess_cluster.py --center-mode catalog --run-specextract --run-sherpa
```

使用手动指定中心：

```bash
/opt/miniconda3/bin/conda run -n ciao-4.18 python postprocess_cluster.py --center-mode manual --center-ra 22.9703 --center-dec -13.6147 --run-specextract --run-sherpa
```

处理另一个星系团时，通常步骤是：

1. 在 `cluster_center_table.csv` 中添加或检查该星系团的参数行。
2. 如果数据文件夹名称和 cluster key 不一致，在 `CLUSTER_DATA_DIRS` 里添加别名。
3. 把 `DEFAULT_CLUSTER_KEY` 改成目标星系团。
4. 在 CIAO 环境中运行脚本。

## 6. 逐步工作流程

### 第 1 步：读取星系团参数

脚本从 `cluster_center_table.csv` 中读取目标星系团，得到：

- cluster name/key；
- 中心 RA 和 Dec；
- 红移；
- 输入的 `M500`；
- `M500` 是否为 `h^-1 Msun`；
- ObsID 列表。

如果表格中质量单位是 `h^-1 Msun`，脚本会根据设定的 `H0` 转成物理太阳质量。

### 第 2 步：计算 R500

脚本使用：

```text
M500 = (4/3) pi R500^3 500 rho_crit(z)
```

其中 `rho_crit(z)` 是该红移处的临界密度。然后用角直径距离把 `R500` 从 Mpc 转换成角半径 arcsec。

当前 Abell 0209 的结果约为：

```text
R500 = 1.523 Mpc
R500 = 451.10 arcsec
```

### 第 3 步：写出源区和背景区

源区是以星系团中心为圆心的圆：

```text
radius = R500
```

背景区是本地环形区域：

```text
inner radius = 1.2 R500
outer radius = 1.8 R500
```

输出的 DS9 region files 为：

```text
cluster209/postprocess_r500/Abell_0209_r500_src.reg
cluster209/postprocess_r500/Abell_0209_r500_bkg.reg
```

如果打开 core masking，源区文件会变成：

```text
cluster209/postprocess_r500/Abell_0209_r500_coreexcised_src.reg
```

此时源区是 annulus，而不是 circle。

做光谱抽取时，脚本还会对每个 ObsID 分别计算星系团中心在该 event file 物理像素坐标中的位置。这很重要，因为不同 ObsID 的 WCS 映射可能不同。

脚本还会在星系团图像上画出 aperture overlay：

```text
cluster209/postprocess_r500/Abell_0209_r500_aperture_overlay.png
cluster209/postprocess_r500/Abell_0209_r500_coreexcised_aperture_overlay.png
```

这张图会显示外侧 `R500` 源区边界、可选的 masked core、背景环和星系团中心。它用于快速确认真正用于拟合的 aperture 是否落在图像上的正确位置。

如果打开 point-source masking，这张图还会用红色圆圈标出从 `wavdetect` 列表中排除的源。这些区域会从传给 `specextract` 的 source 和 background region 表达式中减去。

### 第 4 步：快速估计 flux 和 luminosity

脚本在 `R500` 内对 exposure-corrected flux image 求和，并估计：

```text
L = 4 pi D_L^2 F
```

这是一个快速检查用的 observed-band luminosity。它对 sanity check 有用，但还不是严格的 rest-frame、k-corrected、基于光谱模型的光度。

当前 Abell 0209 的结果为：

```text
aperture_flux_erg_s_cm2 = 1.140e-11
aperture_luminosity_erg_s = 1.400e45
```

注意：当前光度来自 flux image。如果图像更接近 photon flux image，脚本会做近似转换。最终用于标度关系的光度最好从光谱模型中计算。

### 第 5 步：寻找单 exposure event files

脚本用下面的模式寻找每个 exposure 的 evt2 文件：

```text
raw/*/repro/*_repro_evt2.fits
```

对于 Abell 0209，会找到：

```text
cluster209/raw/3579/repro/acisf03579_repro_evt2.fits
cluster209/raw/522/repro/acisf00522_repro_evt2.fits
```

### 第 6 步：用 CIAO specextract 抽取光谱

脚本对每个 ObsID 单独调用 CIAO `specextract`。命令结构大致为：

```bash
specextract \
  infile=<evt2>[sky=circle(x,y,r)] \
  bkgfile=<evt2>[sky=annulus(x,y,rinner,router)] \
  outroot=<output_prefix> \
  correctpsf=no \
  weight=no \
  bkgresp=no \
  clobber=yes
```

关键是每个 ObsID 都有自己的光谱和响应文件：

```text
Abell_0209_obs3579_r500.pi
Abell_0209_obs3579_r500_bkg.pi
Abell_0209_obs3579_r500.arf
Abell_0209_obs3579_r500.rmf

Abell_0209_obs522_r500.pi
Abell_0209_obs522_r500_bkg.pi
Abell_0209_obs522_r500.arf
Abell_0209_obs522_r500.rmf
```

### 第 7 步：写出并运行 Sherpa 联合拟合脚本

后处理脚本会写出 Sherpa 脚本：

```text
cluster209/postprocess_r500/fit_Abell_0209_r500_sherpa.py
```

Sherpa 脚本加载所有单独 exposure 的光谱，并使用同一个模型：

```text
xsphabs * xsapec
```

当前选择为：

- Galactic `NH` 固定；
- 红移固定；
- abundance 初始固定为 `0.3 Zsun`；
- 温度自由；
- APEC normalization 自由；
- 默认统计量为 `wstat`；
- 默认背景处理方式为非扣除式 Sherpa source+background likelihood，直接使用 background PHA；
- 拟合能段为 `0.7-7.0 keV`。

这是联合拟合：所有 spectra 共同限制同一个星系团温度，但每个 spectrum 使用自己的 ARF/RMF。

当 `DEFAULT_SHERPA_BACKGROUND_MODE = "wstat"` 时，生成的 Sherpa 脚本不会先扣背景。它把 source spectrum 和 background spectrum 都作为 Poisson 测量，并由 WSTAT 在似然函数中处理背景。注意，这和更高级的 `set_full_model` / `set_bkg_full_model` 物理背景成分建模不同；后者通常需要 response-folded background components，并且最好在 `specextract` 时生成 `bkgresp=yes` 的背景响应文件。当前默认值是对现有数据产品最稳妥的 CIAO/Sherpa first-pass 背景建模方式。

### 第 8 步：生成拟合诊断图

拟合后，Sherpa 脚本会生成：

```text
cluster209/postprocess_r500/Abell_0209_r500_fit_plot.png
```

图中包括：

- 上面板：每个 ObsID 的 data 和 model；
- 下面板：每个 ObsID 的 residuals。

可以像检查光学 SED fitting 一样检查这张图：模型应该跟随观测光谱形状，residuals 应该围绕 0 随机散布。

### 第 9 步：写出结果

主要输出文件为：

```text
cluster209/postprocess_r500/Abell_0209_r500_summary.json
cluster209/postprocess_r500/Abell_0209_r500_summary.csv
cluster209/postprocess_r500/Abell_0209_r500_fit_results.json
cluster209/postprocess_r500/Abell_0209_r500_fit_plot.png
cluster209/postprocess_r500/Abell_0209_r500_aperture_overlay.png
```

summary JSON/CSV 保存 aperture 信息、快速光度、所用 spectra 和 fit 文件路径。fit-results JSON 保存光谱拟合参数和诊断信息。

脚本最后的终端输出也会明确列出 `aperture layout X-ray image`，这样每次运行结束后可以直接检查用于光谱抽取的 `R500` 源区、可选 core mask、点源 mask 和背景环。

终端输出还会包含 `Files used` 区块，列出只用于图像/计数诊断的 merged event file、用于每个 ObsID 光谱产品的 individual event files，以及 Sherpa 实际加载的 individual spectra。

默认 WSTAT 模式下，拟合结果文件名会包含 `wstat` 标签，例如：

```text
cluster209/postprocess_r500/Abell_0209_r500_xray_peak_psmask_wstat_fit_results.json
cluster209/postprocess_r500/Abell_0209_r500_xray_peak_psmask_wstat_fit_plot.png
```

对于 core-excised 运行，对应文件会带有 `r500_coreexcised` 标签，例如：

```text
cluster209/postprocess_r500/Abell_0209_r500_coreexcised_summary.json
cluster209/postprocess_r500/Abell_0209_r500_coreexcised_fit_results.json
cluster209/postprocess_r500/Abell_0209_r500_coreexcised_fit_plot.png
cluster209/postprocess_r500/Abell_0209_r500_coreexcised_aperture_overlay.png
```

## 7. 当前 JSON 中的拟合诊断

fit-results JSON 包含如下字段：

```json
{
  "temperature_keV": 20.263,
  "statname": "wstat",
  "sherpa_background_mode": "wstat",
  "rstat": 1.204,
  "q_value": 3.16e-05,
  "fit_quality_flag": "high_reduced_statistic_check_model_background_or_calibration",
  "confidence_intervals": {
    "icm.kT": {
      "best": 20.263,
      "lower_delta_1sigma": -1.518,
      "upper_delta_1sigma": 2.210
    }
  },
  "residual_summaries": [
    {
      "dataset_id": 1,
      "mean_residual": 0.0038,
      "rms_residual": 0.0369,
      "max_abs_residual": 0.1739
    }
  ]
}
```

这些诊断字段是为了之后批量处理多个星系团时更方便。它们不能完全代替人工查看拟合图。

## 8. 如何评价 X 射线拟合好坏

需要同时看统计量和物理合理性。

好的迹象：

- data 和 model 的整体光谱形状一致；
- residuals 围绕 0 随机散布；
- 两个 ObsID 的结果彼此一致；
- confidence interval 有限且合理；
- 拟合温度对该星系团质量来说合理。

需要进一步检查的情况：

- `reduced chi2` 远大于 1：可能模型不好、背景有问题、校准有问题，或缺少物理成分；
- `reduced chi2` 远小于 1：可能误差偏保守、binning/grouping 太强，或统计量选择影响；
- 对 WSTAT 来说，reduced statistic 和 residual plot 主要作为诊断参考；它不是简单的 chi-square goodness-of-fit test；
- 高能端 residual 有系统趋势：可能背景不匹配；
- Fe-K 附近 residual 明显：可能温度、丰度或校准有问题；
- 不同 ObsID 之间差异很大：可能 response、background 或抽取区域有问题。

对于 Abell 0209，当前拟合给出：

```text
T_X = 20.26 keV
1-sigma 误差约为 -1.52 / +2.21 keV
WSTAT reduced statistic = 1.204
```

这个非扣除式背景拟合可以正常运行，但温度对 Abell 0209 来说偏高，统计量也略高，因此 JSON 会标记需要继续检查背景、aperture、模型假设以及背景区中是否仍有星系团辐射污染。

## 9. 科学注意事项

作为课程项目，这个流程已经是一个很好的 first-pass analysis。若要做更严格的科学结果，可以考虑：

- 在抽光谱前更严格地 mask point sources；
- 比较 local background 和 blank-sky background；
- 对低计数或背景主导光谱使用 `WSTAT`/Cash statistics；
- 提取 core-excised temperature，例如 `0.15R500-R500`，更适合某些标度关系比较；
- 如果数据质量允许，让 abundance 自由拟合；
- 用光谱模型计算标准能段内的 rest-frame luminosity；
- 如果运行时间允许，测试 `specextract weight=yes` 或 weighted responses；
- 检查 chip gaps 和背景区是否仍含有星系团辐射。
