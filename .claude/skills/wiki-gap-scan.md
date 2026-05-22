---
name: wiki-gap-scan
description: 检测 wiki 中的知识缺口——覆盖度不足、深度不够、结构缺失
---

You are a wiki gap detection agent. Scan the LLM Wiki to identify knowledge gaps that need attention.

## Wiki Location
`wiki/`

## Gap Types to Detect

### 1. Depth Gap
- Scan `wiki/papers/*.md` for pages where all citations are at abstract level (no section-level locators like "sec.X", "Table Y")
- These papers need deeper reading to extract more detailed results
- Priority: papers that are cited by many concept pages (high connectivity)

### 2. Coverage Gap
- Read concept pages with comparison tables (e.g., `scaling_relations.md`)
- Identify rows with missing values (marked "—", "~", or "TBD")
- These are literature results not yet extracted from the papers
- Also check: papers in `wiki/raw/` that have no corresponding `papers/*.md` page

### 3. Structural Gap
- Scan `wiki/papers/*.md` and check which papers are NOT referenced by any concept or method page
- Papers with zero inbound links from concept/method pages may need to be integrated
- Check if important keywords in paper frontmatter have no corresponding concept/method page

### 4. Synthesis Gap
- Identify topics that span ≥3 paper pages but have no synthesis page in `wiki/synthesis/`
- Suggest synthesis topics based on clusters of related papers

## Steps

### 1. Run lint first
```bash
python scripts/wiki_lint.py --quiet
```

### 2. Scan for gaps
Read `wiki/index.md`, scan all paper page frontmatter, and check concept pages.

### 3. Priority ranking
Rank gaps by impact:
- **HIGH**: Coverage gaps in core scaling relations (Tx-M, Lx-M comparison tables)
- **MEDIUM**: Depth gaps in highly-cited papers
- **LOW**: Structural gaps in peripheral papers

### 4. Output report

```
## Wiki Gap Scan — YYYY-MM-DD

### Summary
- Depth gaps: N papers need deeper reading
- Coverage gaps: N missing values in comparison tables
- Structural gaps: N papers not integrated into concepts
- Synthesis gaps: N suggested synthesis topics

### HIGH Priority
- [COVERAGE] scaling_relations.md: Tx-M slope missing for Pratt+09
- [DEPTH] mantz_2010.md: only abstract-level citations

### MEDIUM Priority
- [STRUCTURAL] sun_2009.md: not referenced by any concept page
- [DEPTH] vikhlinin_2009.md: key results not section-level cited

### Suggested Actions
- `/wiki-ingest` <missing_paper> to fill coverage gaps
- Re-read mantz_2010 PDF for deeper claims extraction
- Create synthesis topic: "Core-excised vs total Lx scatter comparison"
```

## Important Rules
- This is a read-only diagnostic — do NOT modify any files
- Focus on actionable gaps, not cosmetic issues
- Prioritize gaps that affect the core scaling relation analysis
