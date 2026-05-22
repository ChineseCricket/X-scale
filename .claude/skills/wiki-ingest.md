---
name: wiki-ingest
description: 摄入一篇天体物理文献到 LLM Wiki，提取关键结果和结构化 claims，更新概念页面
---

You are a research wiki ingestion agent. Your task is to read an astrophysics paper and compile it into the project's LLM Wiki.

## Context
This project studies Galaxy Cluster X-ray scaling relations (L_X-M_500 and T_X-M_500). The wiki is at `wiki/`.

## Input
The user provides a paper source. It can be:
- A PDF file path in `wiki/raw/`
- An arXiv ID (e.g., "0909.3038")
- A paper title or author+year

## Pre-check: Manifest Dedup

Read `wiki/.manifest.json`. If the paper slug already exists with `"status": "compiled"`, report duplicate and ask user whether to force re-compile.

## Steps

### 1. Read the paper
- If PDF: use the Read tool to read the PDF file
- If arXiv ID: use WebSearch to find and fetch the paper, then use WebFetch to read it
- If title/author: use WebSearch to find it

### 2. Extract structured information
Extract the following from the paper:
- **Metadata**: title, authors, year, journal, arXiv ID, DOI
- **Sample**: number of clusters, survey source, redshift range, mass range
- **Key equations**: scaling relation formulas (in LaTeX)
- **Key numerical results**: slopes, normalizations, intrinsic scatter, pivot values
- **Methods**: instruments used, fitting method, energy bands
- **Section-level locators**: note which Table/Figure/Section each result comes from

### 3. Extract structured claims
Extract 3-8 key claims from the paper and format as frontmatter:

```yaml
claims:
  - text: "core-excised Lx-M scatter <10%"
    locator: "Table 7, sec.4.2"
    type: empirical_result
  - text: "slope consistent with self-similar prediction"
    locator: "sec.5.1"
    type: physical_insight
```

Claims type:
- `empirical_result` — numerical results (slopes, scatter, normalizations)
- `method_claim` — methodology statements
- `physical_insight` — physical interpretation/conclusions
- `definition` — definitions of formulas or terms

**Locator rules**: must cite specific location in paper (Table X, Figure Y, sec.Z, Eq.N). Never fabricate locators.

### 4. Write paper page
Write to `wiki/papers/<first_author>_<year>.md` with this structure:

```markdown
---
title: "Full Title"
authors: [Author1, Author2, ...]
year: YYYY
journal: "Journal"
arxiv: "XXXX.XXXX"
keywords: [scaling-relations, x-ray, galaxy-clusters, ...]
provenance: source-derived
sample_size: N
redshift_range: [z_min, z_max]
mass_range: [M_min, M_max]
claims:
  - text: "claim 1"
    locator: "Table X"
    type: empirical_result
  - text: "claim 2"
    locator: "sec.Y"
    type: physical_insight
---

# Author et al. (Year)

## One-line Summary
(One sentence summary)

## Sample
(Describe the sample)

## Key Results
(With specific locators for each numerical result)

### T_X - M_500
- Slope: $\beta = X.XX \pm X.XX$ (Table X)
- Normalization: ...
- Scatter: ...

### L_X - M_500
(if applicable)

## Key Equations
(LaTeX formulas)

## Methods
(Instruments, fitting approach, energy bands)

## Relations to Other Work
- [[other_paper]] — comparison or extension
```

### 5. Update concept pages
Read existing concept pages in `wiki/concepts/` and add this paper's results to comparison tables. For example, in `scaling_relations.md`, add a row to the comparison table.

### 6. Update index
Read `wiki/index.md` and add the new paper to the literature table.

### 7. Update manifest
Add entry to `wiki/.manifest.json`:
```json
"<slug>": {
  "status": "compiled",
  "compiled_at": "YYYY-MM-DD",
  "has_claims": true,
  "provenance": "source-derived"
}
```

### 8. Append to log
Append to `wiki/log.md`:
```
## [YYYY-MM-DD] ingest | Author et al. (Year)
- Title: ...
- Added: papers/author_year.md
- Claims: N extracted
- Updated: concepts/xxx.md, index.md
```

### 9. Run health check
Run `python scripts/wiki_lint.py` to verify, then `/wiki-check` for semantic checks.

## Important Rules
- Never modify files in `wiki/raw/`
- Every paper page MUST have `provenance: source-derived`
- Every paper page MUST have at least 3 claims in frontmatter
- Use `[[wikilink]]` format for cross-references
- Include LaTeX formulas in `$$...$$` or `$...$` format
- All numerical results must cite which table/figure they come from
- Check `wiki/.manifest.json` before processing to avoid duplicates
