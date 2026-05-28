# Galaxy Cluster X-ray Scaling Relation

用 Chandra X-ray 数据复现 L_X-M_500 和 T_X-M_500 标度关系。

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
| 光谱分析 | **完成 full-R500** — 23/23 有结果；主 scaling 样本 18 团，5 团标记 bad/excluded |
| 标度关系拟合 | **Phase 4 full-R500 初版完成** — canonical table + linmix Lx-M500/Tx-M500 |
| 最终可视化 | 初版 scaling 图已生成，最终报告图待整理 |

详细进度见 `memory/pipeline_status.csv`。

## 运行方式

### 运行 CIAO pipeline
```bash
source /data/jyz/Applications/ciao-4.18/ciao-4.18/bin/ciao.sh
python src/01_reduction/run_ciao_pipeline.py
```

### 运行光谱分析
```bash
source /data/jyz/Applications/ciao-4.18/ciao-4.18/bin/ciao.sh
python src/02_spectral/postproces_cluster.py --cluster <cluster_key> --run-specextract --run-sherpa
```

### 运行 Phase 4 scaling
```bash
source /data/jyz/Applications/ciao-4.18/ciao-4.18/bin/ciao.sh
python src/03_scaling/build_spectral_summary.py
python src/03_scaling/fit_scaling_relations.py
```
