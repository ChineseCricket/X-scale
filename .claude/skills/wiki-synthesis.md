---
name: wiki-synthesis
description: 综合 wiki 中的文献知识，生成可用于报告的分析
---

You are a knowledge synthesis agent. Your task is to read the project's LLM Wiki and generate a comprehensive synthesis for a specific topic.

## Wiki Location
`wiki/`

## Input
The user specifies what to synthesize. Common requests:
- "综合 T_X-M_500 的文献结果"
- "对比不同文献的斜率和 scatter"
- "准备 Introduction 部分的背景"
- "准备 Discussion 部分"

## Steps

### 1. Read index
Read `wiki/index.md` to understand the full scope of available literature.

### 2. Read relevant pages
Based on the synthesis topic, read:
- Relevant `papers/` pages
- Relevant `concepts/` pages
- Relevant `methods/` pages

### 3. Run health check first
Before synthesis, run `/wiki-check` to ensure the wiki is healthy and consistent. Report any issues found.

### 4. Generate synthesis
Produce a structured Markdown output with:

#### For scaling relation comparison:
```markdown
## T_X - M_500 Scaling Relation: Literature Comparison

| Study | Sample | Slope | Normalization | Scatter | Core-excised? | Method |
|-------|--------|-------|---------------|---------|---------------|--------|
| Pratt+09 | 31 | ... | ... | ... | Yes | ... |
| Mantz+16 | ... | ... | ... | ... | ... | ... |
| **This work** | 23 | ... | ... | ... | ... | ... |

### Key findings from the literature:
- (Pattern 1)
- (Pattern 2)

### Systematic differences:
- (Between surveys/methods)
```

#### For Introduction/Discussion sections:
- Clear prose synthesizing the background
- Proper citations using Author (Year) format
- Key equations with physical interpretation
- Gaps in current knowledge that this work addresses

### 5. Quality checks
- All numerical values cited back to specific papers
- No contradictions between papers left unexplained
- Clear statement of where this project's results fit in the literature

## Output
- Print the synthesis to the terminal
- Optionally save to `wiki/outputs/synthesis_<topic>_<date>.md`
