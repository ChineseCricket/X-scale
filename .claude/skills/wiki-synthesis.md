---
name: wiki-synthesis
description: 综合 wiki 中的文献知识，生成带有 Thesis 的结构化综合分析页面
---

You are a knowledge synthesis agent. Your task is to read the project's LLM Wiki and generate a structured synthesis for a specific topic.

## Wiki Location
`wiki/`

## Input
The user specifies what to synthesize. Common requests:
- "综合 T_X-M_500 的文献结果"
- "对比不同文献的斜率和 scatter"
- "准备 Introduction 部分的背景"
- "准备 Discussion 部分"

## Pre-check: Lint Gate

Run `python scripts/wiki_lint.py` first. If any FAIL issues, report them and stop. Fix structural issues before synthesis.

## Steps

### 1. Read index
Read `wiki/index.md` to understand the full scope of available literature.

### 2. Read relevant pages
Based on the synthesis topic, read:
- Relevant `papers/` pages (use frontmatter claims for quick overview)
- Relevant `concepts/` pages
- Relevant `methods/` pages

### 3. Synthesis Decision (UPDATE vs CREATE)

Before writing, check if a synthesis page already exists for this topic in `wiki/synthesis/`:

- If YES: read existing `## Thesis` section. Does it cover the new insight?
  - UPDATE: add sources, strengthen argument, update `last_reviewed`
  - SPLIT: if thesis has diverged into two independent arguments
- If NO: CREATE new synthesis page

### 4. Write synthesis page

Write to `wiki/synthesis/<topic_slug>.md` with this structure:

```markdown
---
title: "T_X-M_500 Literature Synthesis"
type: synthesis
provenance: llm-derived
sources: [pratt_2009, mantz_2010, vikhlinin_2009]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Synthesis: <Topic>

## Thesis
(One paragraph stating the core argument or finding from the synthesis)

## Evidence
(Structured evidence from multiple sources, with citations)

### From [[pratt_2009]]:
- Key finding 1 (sec.X)
- Key finding 2

### From [[mantz_2010]]:
- Key finding 1 (Table Y)

## Synthesis Table (for scaling relations)

| Study | Sample | Slope | Scatter | Core-excised? | Method |
|-------|--------|-------|---------|---------------|--------|
| Pratt+09 | 31 | ... | ... | Yes | BCES |
| **This work** | 23 | ... | ... | ... | linmix |

## Open Questions
(1-3 unresolved questions from the literature)

## Related
- [[concept_page]] — related concept
```

### 5. Update index
Add synthesis entry to `wiki/index.md` under a new `## Synthesis Pages` section.

### 6. Append to log
```
## [YYYY-MM-DD] synthesis | <topic>
- Created/Updated: synthesis/<topic_slug>.md
- Sources: N papers cited
- Thesis: <one-line thesis>
```

### 7. Quality checks
- All numerical values cited back to specific papers with locators
- No contradictions left unexplained
- Clear statement of where this project's results fit
- Synthesis uses ≥1 source-derived references

## Important Rules
- Every synthesis MUST have a `## Thesis` section
- Use `provenance: llm-derived` for synthesis pages
- Do NOT include query-derived content (from `/kb-ask` style Q&A)
- Flag contradictions explicitly — do not silently resolve
- Keep synthesis focused: one thesis per page
