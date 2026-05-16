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
| CIAO Pipeline | **进行中** — 17/23 团完成，6 团 csmooth 补跑中 |
| 光谱分析 | Abell_0068 测试通过（T_X=33.4 keV），脚本修复完成，待批量处理 |
| 标度关系拟合 | 未开始 |
| 最终可视化 | 未开始 |

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
