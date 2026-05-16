# Wiki 维护规则

本文件定义 agent 维护 wiki 时遵循的规则。

## 实体类型

### papers/ — 文献笔记
- 文件名格式: `<first_author>_<year>.md`
- 必须包含 YAML frontmatter: title, authors, year, journal, arxiv, keywords, sample_size
- 正文结构:
  1. 一句话摘要
  2. 样本描述
  3. 关键公式（LaTeX）
  4. 关键数值结果
  5. 与其他文献的关系（使用 `[[wikilink]]`）

### concepts/ — 概念页面
- 跨文献综合
- 包含各文献结果的对比表
- 使用 `[[wikilink]]` 链接到 papers/ 和 methods/

### methods/ — 方法论页面
- 描述具体的分析/拟合方法
- 包含公式和使用场景

### data_sources/ — 数据来源
- 巡天/样本描述
- M_500 测量方法和误差来源

## 维护规则

1. **摄入新文献时**:
   - 写 paper 页面
   - 更新相关 concept 页面（添加新文献的结果）
   - 更新 index.md
   - 追加到 log.md
   - 运行 `/wiki-check`

2. **使用 `[[wikilink]]` 格式** 进行交叉引用

3. **数值结果必须标注来源文献**

4. **raw/ 目录中的 PDF 文件永远不修改**

## 文件位置
- Wiki 根目录: `wiki/`
- 原始文献: `wiki/raw/`
- 索引: `wiki/index.md`
- 日志: `wiki/log.md`
