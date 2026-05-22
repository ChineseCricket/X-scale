---
name: wiki-check
description: 检查 LLM Wiki 的健康度，结合确定性 lint 脚本和 LLM 语义检查
---

You are a wiki health check agent. Your task is to audit the project's LLM Wiki and fix any issues found.

## Phase 1: Deterministic Checks (run first)

Run the lint script first — zero LLM cost, catches structural issues:

```bash
python scripts/wiki_lint.py
```

If any FAIL issues are found, report them and fix what can be auto-fixed:
- Missing `provenance` field → add `provenance: source-derived` for papers, `provenance: llm-derived` for others
- Broken wikilinks → fix if the correct slug can be inferred
- Missing index entries → add to `wiki/index.md`

Re-run lint to confirm all FAILs resolved before proceeding to Phase 2.

## Phase 2: Semantic Checks (LLM-assisted)

### 1. Cross-reference Consistency
- Read concept pages that contain comparison tables (e.g., `scaling_relations.md`)
- Verify numerical values match the corresponding paper pages
- Flag any discrepancies — do NOT auto-fix

### 2. Keyword Coverage
- Read all paper page frontmatter keywords
- For each keyword, check if a corresponding concept page or method page exists
- Report missing concept/method pages for important keywords

### 3. Log Completeness
- Read `wiki/log.md`
- List all PDF files in `wiki/raw/`
- Verify each PDF has a corresponding log entry
- Report any gaps

### 4. Manifest Consistency
- Read `wiki/.manifest.json`
- Compare with actual files in `wiki/papers/`
- Report any manifest entries without corresponding files, or files without manifest entries

### 5. Claims Quality
- Sample 3-5 paper pages with claims
- Verify claims are accurate, non-trivial, and correctly typed
- Flag vague or useless claims (e.g., "this paper studies clusters")

## Output Format

```
## Wiki Health Check Report — YYYY-MM-DD

### Phase 1: Lint (Deterministic)
- [PASS/FAIL] frontmatter: N pages
- [PASS/FAIL] provenance: N pages
- [PASS/FAIL] wikilinks: N total
- [PASS/FAIL] index: N papers
- [WARN] claims: N without claims
- [PASS/WARN] orphans: N orphans

### Phase 2: Semantic (LLM)
- Cross-reference: PASS/N issues
- Keyword coverage: PASS/N missing
- Log completeness: PASS/N gaps
- Manifest consistency: PASS/N mismatches
- Claims quality: PASS/N issues

### Actions Taken
(list any auto-fixes applied)
```

## Auto-fix Rules
- Missing `provenance` → auto-add (source-derived for papers, llm-derived for others)
- Missing index entries → auto-add to index.md
- Broken wikilinks with obvious fix → auto-fix
- Manifest out of sync → auto-update
- Do NOT auto-fix cross-reference consistency issues (flag for review)
- Do NOT auto-fix claims quality issues (flag for review)
