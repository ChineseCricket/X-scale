# scripts/

代码已迁移到 `src/` 按功能阶段组织：

| 原 scripts/ 文件 | 现位于 |
|---|---|
| `download_secondary.py` | `src/00_download/download_secondary.py` |
| `run_ciao_pipeline.py` | `src/01_reduction/run_ciao_pipeline.py` |
| `ciao_pipeline.sh` | `src/01_reduction/ciao_pipeline.sh` |
| `postproces_cluster.py` | `src/02_spectral/postproces_cluster.py` |
| `generate_contours.py` | `src/04_visualization/generate_contours.py` |
| `plot_results.py` | `src/04_visualization/plot_results.py` |
| `cluster_center_table.csv` | `configs/cluster_table.csv` |
