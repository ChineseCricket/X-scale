# Wiki Schema — X_scale Galaxy Cluster Scaling Relations

## 页面类型

### papers/ — 文献笔记
- 文件名: `<first_author>_<year>.md`
- frontmatter 必须包含: title, authors, year, journal, arxiv, keywords, provenance
- 正文: 一句话摘要 → 样本 → 关键结果 → 公式 → 方法 → 文献关系

### concepts/ — 概念页面
- 跨文献综合，包含对比表
- provenance: `llm-derived`（除非人工确认 → `user-verified`）

### methods/ — 方法论页面
- 分析/拟合方法描述
- provenance: `llm-derived`

### data_sources/ — 数据来源
- 巡天/样本描述
- provenance: `llm-derived`

### synthesis/ — 综合分析
- 跨论文主题综合，必须有 `## Thesis` 段
- provenance: `llm-derived`，需引用 ≥1 个 source-derived 文献

## 溯源模型 (Provenance)

3 级信任度：

| Level | 含义 | 规则 |
|-------|------|------|
| `source-derived` | 直接从 PDF/论文原文提取 | 可用于 synthesis 引用 |
| `llm-derived` | LLM 跨文献综合/推理 | 需引用 ≥1 个 source-derived 文献 |
| `user-verified` | 人工确认的内容 | 最高信任度，不可覆盖 |

**规则**:
- 论文页面 (papers/) 必须使用 `source-derived`
- concept/method/data_source/synthesis 页面使用 `llm-derived`
- 用户明确确认后可升级为 `user-verified`
- 矛盾声明必须显式标注（`## Contradictions`），不可静默解决

## 结构化 Claims

每篇论文页面在 frontmatter 中提取 3-8 个关键 claims：

```yaml
claims:
  - text: "core-excised Lx-M scatter <10%"
    locator: "Table 7, sec.4.2"
    type: empirical_result
  - text: "非引力加热主要影响 r<0.15r500"
    locator: "sec.5"
    type: physical_insight
```

### Claims type（天文适配）
- `empirical_result` — 观测/数值结果（斜率、scatter、归一化）
- `method_claim` — 方法声明（拟合方法、数据选择）
- `physical_insight` — 物理解释/结论
- `definition` — 定义（公式、术语）

### Locator 规则
标注具体来源位置：`Table X`, `Figure Y`, `sec.Z`, `Eq.N`, `Appendix`
不可编造 locator。不确定时用 `全文` 或省略。

## 引用格式

数值结果引用格式：`斜率 1.33±0.08 (Table 7, [[mantz_2010]])`

交叉引用使用 `[[wikilink]]`：`[[pratt_2009]]`, `[[scaling_relations]]`

## 维护规则

1. **摄入新文献时**: 写 paper 页面 → 更新 concept 页面 → 更新 index.md → 追加 log.md → 运行 `/wiki-check`
2. **raw/ 目录中的 PDF 文件永远不修改**
3. **数值结果必须标注来源文献和具体位置**
4. **manifest 检查**: 摄入前查 `wiki/.manifest.json` 避免重复处理

## 文件位置
- Wiki: `wiki/`
- 原始 PDF: `wiki/raw/`
- 索引: `wiki/index.md`
- 日志: `wiki/log.md`
- 编译状态: `wiki/.manifest.json`
- Lint 脚本: `scripts/wiki_lint.py`
