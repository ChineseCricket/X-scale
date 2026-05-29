# Galaxy Cluster X-ray Scaling Relation

用 Chandra X-ray 数据复现 L_X-M_500、T_X-M_500 和 L_X-T_X 标度关系。

## 样本

- 30 个星系团来自 CLASH (16) + LoCuSS (14) 巡天
- 7 个 dropped（见 `configs/dropped.list`），最终样本 23 个团
- M500 来自弱引力透镜测量

## 目录结构

```
X_scale/
├── chandra_data_evt/    # 原始 Chandra 数据（30 个星系团）
├── data/raw -> chandra_data_evt/  # 数据入口（symlink）
├── src/                  # 代码
│   ├── 00_download/      #   数据下载
│   ├── 01_reduction/     #   CIAO 数据处理
│   ├── 02_spectral/      #   光谱分析 + 配套文档
│   ├── 03_scaling/       #   标度关系拟合
│   ├── 04_visualization/ #   可视化
│   └── sandbox/          #   实验性代码
├── configs/              # 配置文件
│   ├── cluster_table.csv       # 星系团参数表
│   └── dropped.list            # 排除的团
├── memory/               # Agent 工作记忆
│   ├── pipeline_status.csv     #   处理进度追踪
│   └── workflow_plan.md        #   工作流程计划
├── wiki/                 # 参考文献知识库（LLM Wiki）
└── output/               # 输出（图、日志、数据产品）
    ├── logs/             #   运行日志 (pipeline/, spectral/)
    ├── products/         #   数据产品 (pipeline/, spectral/, scaling/)
    └── figures/          #   图表 (pipeline/, spectral/, scaling/)
```

## 当前状态

| 步骤 | 状态 |
|------|------|
| 数据下载 | 完成（30 团 + stat1/bias 补下载） |
| 文献准备 & Wiki | 完成 |
| CIAO Pipeline | **完成** — 23/23 团完成（6 团 csmooth 跳过，仅影响可视化） |
| 光谱分析 | **完成** — full-R500 23/23；core-excised 18/18 主样本完成 |
| 标度关系拟合 | **完成** — full-R500 baseline + core-excised comparison |
| 最终可视化 | scaling 图和 spectral QA 图已生成，进入最终报告整理 |

详细进度见 `memory/pipeline_status.csv`。

## 当前科学结果

主样本为 18 个 included clusters；Abell_0697、Abell_0750、MS2137-2353、RXJ1347.5-1145、ZwCl_0857.9+2107 因光谱质量或参考值问题从主 scaling 样本排除。

Full-R500 baseline (`output/products/scaling/`, exclude_bad N=18):

| Relation | beta | intrinsic scatter |
|---|---:|---:|
| Lx-M500 | 1.09 -0.48/+0.45 | 0.169 dex |
| Tx-M500 | 0.50 -0.27/+0.29 | 0.117 dex |
| Lx-Tx | 0.77 -0.44/+0.47 | 0.227 dex |

Core-excised comparison (`0.15-1.0 R500`, `output/products/scaling/core_excised/`, exclude_bad N=18):

| Relation | beta | intrinsic scatter |
|---|---:|---:|
| Lx-M500 | 1.15 -0.51/+0.54 | 0.186 dex |
| Tx-M500 | 0.55 -0.34/+0.36 | 0.157 dex |
| Lx-Tx | 0.69 -0.41/+0.40 | 0.245 dex |

Full-R500 remains the canonical baseline. Core-excised products are the literature-style comparison branch and must be labeled explicitly as `0.15-1.0 R500`.

Important uncertainty caveat: core-excised Lx errors use native Sherpa `sample_energy_flux`; core-excised Tx confidence intervals are not stored in the JSONs, so Tx-M500 and Lx-Tx use the documented 10% Tx fallback.

## 运行方式

### 运行 CIAO pipeline
```bash
source /data/jyz/Applications/ciao-4.18/ciao-4.18/bin/ciao.sh
python src/01_reduction/run_ciao_pipeline.py
```

### 运行光谱分析
```bash
source /data/jyz/Applications/ciao-4.18/ciao-4.18/bin/ciao.sh
python src/02_spectral/fit_spectral_xrb.py --cluster <cluster_key> --xrb-policy fixed_shape --renormalize-blanksky-pha
python src/02_spectral/fit_spectral_xrb.py --cluster <cluster_key> --excise-core --core-inner-r500 0.15 --xrb-policy fixed_shape --renormalize-blanksky-pha
```

### 运行 Phase 4 scaling
```bash
source /data/jyz/Applications/ciao-4.18/ciao-4.18/bin/ciao.sh
python src/03_scaling/build_spectral_summary.py
python src/03_scaling/fit_scaling_relations.py
python src/03_scaling/build_spectral_summary.py --results-dir output/products/spectral/core_excised --output output/products/spectral/spectral_summary_core_excised.csv --default-aperture-label core_excised_0.15_1.0R500
python src/03_scaling/fit_scaling_relations.py --summary output/products/spectral/spectral_summary_core_excised.csv --outdir output/products/scaling/core_excised --figdir output/figures/scaling/core_excised --skip-sensitivity
```

## 关键产品

- Full-R500 spectral summary: `output/products/spectral/spectral_summary.csv`
- Core-excised spectral summary: `output/products/spectral/spectral_summary_core_excised.csv`
- Full-R500 scaling products: `output/products/scaling/`
- Core-excised scaling products: `output/products/scaling/core_excised/`
- Core-excised spectral QA report: `output/products/spectral/core_excised_spectral_qa_report.md`
- Full-vs-core comparison: `output/products/scaling/full_vs_core_excised_comparison.md`
