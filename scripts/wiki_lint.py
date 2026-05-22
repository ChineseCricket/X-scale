#!/usr/bin/env python3
"""Wiki Lint — Deterministic health checks for the X_scale LLM Wiki.

Zero LLM cost. Checks frontmatter, provenance, wikilinks, index coverage,
claims, and orphan pages. Outputs PASS/FAIL/WARN per check.

Usage:
    python scripts/wiki_lint.py [--fix] [--json] [--quiet]
"""

import json
import os
import re
import sys
from pathlib import Path

WIKI_DIR = Path(__file__).resolve().parent.parent / "wiki"
PAPERS_DIR = WIKI_DIR / "papers"
CONCEPTS_DIR = WIKI_DIR / "concepts"
METHODS_DIR = WIKI_DIR / "methods"
DATA_SOURCES_DIR = WIKI_DIR / "data_sources"
SYNTHESIS_DIR = WIKI_DIR / "synthesis"
INDEX_FILE = WIKI_DIR / "index.md"
ALL_DIRS = [PAPERS_DIR, CONCEPTS_DIR, METHODS_DIR, DATA_SOURCES_DIR, SYNTHESIS_DIR]

VALID_PROVENANCE = {"source-derived", "llm-derived", "user-verified"}
VALID_CLAIM_TYPES = {"empirical_result", "method_claim", "physical_insight", "definition"}

PAPER_REQUIRED_FIELDS = {"title", "authors", "year", "journal", "keywords", "provenance"}
NON_PAPER_REQUIRED_FIELDS = {"provenance"}  # title optional for concepts/methods (use 'name' if no title)


class Issue:
    def __init__(self, level, check, file, msg):
        self.level = level  # PASS, FAIL, WARN
        self.check = check
        self.file = file
        self.msg = msg

    def __str__(self):
        prefix = f"[{self.level}]"
        if self.file:
            return f"{prefix} {self.check}: {self.file} — {self.msg}"
        return f"{prefix} {self.check}: {self.msg}"


def parse_frontmatter(text):
    m = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return None
    fm = {}
    raw = m.group(1)
    for line in raw.split('\n'):
        kv = re.match(r'^(\w[\w-]*):\s*(.*)', line)
        if not kv:
            continue
        key = kv.group(1).strip()
        val = kv.group(2).strip().strip('"').strip("'")
        if val.startswith('[') and val.endswith(']'):
            val = [s.strip().strip('"').strip("'") for s in val[1:-1].split(',') if s.strip()]
        fm[key] = val
    return fm if fm else None


def list_md(directory):
    if not directory.exists():
        return []
    return sorted(directory.glob("*.md"))


def all_pages():
    pages = []
    for d in ALL_DIRS:
        pages.extend(list_md(d))
    return pages


def slug_exists(slug):
    for d in ALL_DIRS:
        if (d / f"{slug}.md").exists():
            return True
    return False


def rel_path(p):
    try:
        return str(p.relative_to(WIKI_DIR))
    except ValueError:
        return str(p)


def check_frontmatter(pages):
    issues = []
    ok = 0
    for p in pages:
        text = p.read_text(encoding='utf-8')
        fm = parse_frontmatter(text)
        rp = rel_path(p)

        if not fm:
            issues.append(Issue("FAIL", "frontmatter", rp, "missing YAML frontmatter"))
            continue

        is_paper = "papers" in str(p)
        required = PAPER_REQUIRED_FIELDS if is_paper else NON_PAPER_REQUIRED_FIELDS
        keys = set(fm.keys())
        missing = required - keys
        if missing:
            issues.append(Issue("FAIL", "frontmatter", rp, f"missing field(s): {', '.join(sorted(missing))}"))
            continue

        if is_paper and not isinstance(fm.get("authors"), list):
            issues.append(Issue("WARN", "frontmatter", rp, "authors should be a list"))

        ok += 1

    issues.insert(0, Issue("PASS", "frontmatter", "", f"{ok} pages have valid frontmatter"))
    return issues


def check_provenance(pages):
    issues = []
    ok = 0
    for p in pages:
        text = p.read_text(encoding='utf-8')
        fm = parse_frontmatter(text)
        rp = rel_path(p)

        if not fm or "provenance" not in fm:
            continue

        prov = fm["provenance"]
        if prov not in VALID_PROVENANCE:
            issues.append(Issue("FAIL", "provenance", rp, f"invalid provenance: '{prov}'"))
            continue

        is_paper = "papers" in str(p)
        if is_paper and prov != "source-derived":
            issues.append(Issue("WARN", "provenance", rp, f"paper page should be source-derived, got '{prov}'"))

        ok += 1

    issues.insert(0, Issue("PASS", "provenance", "", f"{ok} pages have valid provenance"))
    return issues


def check_wikilinks(pages):
    issues = []
    ok = 0
    broken = 0
    wl_re = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')

    index_pages = []
    if INDEX_FILE.exists():
        index_pages.append(INDEX_FILE)
    all_files = list(pages) + index_pages

    for p in all_files:
        text = p.read_text(encoding='utf-8')
        rp = rel_path(p) if p != INDEX_FILE else "index.md"

        for m in wl_re.finditer(text):
            slug = m.group(1).strip()
            if slug_exists(slug):
                ok += 1
            else:
                issues.append(Issue("FAIL", "wikilinks", rp, f"broken link: [[{slug}]]"))
                broken += 1

    if broken == 0:
        issues.insert(0, Issue("PASS", "wikilinks", "", f"all {ok} wikilinks resolve"))
    else:
        issues.insert(0, Issue("FAIL", "wikilinks", "", f"{broken} broken links out of {ok + broken} total"))
    return issues


def check_index_coverage(pages):
    issues = []
    if not INDEX_FILE.exists():
        issues.append(Issue("FAIL", "index", "", "index.md not found"))
        return issues

    index_text = INDEX_FILE.read_text(encoding='utf-8')
    paper_files = {p.stem for p in list_md(PAPERS_DIR)}

    covered = 0
    missing = []
    for slug in paper_files:
        if f"[[{slug}]]" in index_text:
            covered += 1
        else:
            missing.append(slug)

    if missing:
        for slug in missing:
            issues.append(Issue("FAIL", "index", f"papers/{slug}.md", "not referenced in index.md"))
        issues.insert(0, Issue("FAIL", "index", "", f"{len(missing)} papers missing from index ({covered}/{len(paper_files)} covered)"))
    else:
        issues.insert(0, Issue("PASS", "index", "", f"all {covered} papers referenced in index"))
    return issues


def check_claims(pages):
    issues = []
    ok = 0
    no_claims = 0

    for p in pages:
        if "papers" not in str(p):
            continue

        text = p.read_text(encoding='utf-8')
        rp = rel_path(p)

        # Extract frontmatter block
        fm_match = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
        if not fm_match:
            continue

        fm_text = fm_match.group(1)

        # Count claims by looking for "- text:" pattern in frontmatter
        claim_count = len(re.findall(r'^\s+-\s+text:', fm_text, re.MULTILINE))

        if claim_count == 0:
            no_claims += 1
            issues.append(Issue("WARN", "claims", rp, "no claims in frontmatter"))
        elif claim_count < 3:
            issues.append(Issue("WARN", "claims", rp, f"only {claim_count} claims (recommended: 3-8)"))
        else:
            ok += 1

    if no_claims > 0:
        issues.insert(0, Issue("WARN", "claims", "", f"{no_claims} paper pages without claims, {ok} with sufficient claims"))
    else:
        issues.insert(0, Issue("PASS", "claims", "", f"{ok} paper pages have sufficient claims"))
    return issues


def check_orphans(pages):
    issues = []
    wl_re = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')

    inbound = {}
    all_files = list(pages)
    if INDEX_FILE.exists():
        all_files.append(INDEX_FILE)

    for p in all_files:
        text = p.read_text(encoding='utf-8')
        for m in wl_re.finditer(text):
            slug = m.group(1).strip()
            inbound.setdefault(slug, []).append(rel_path(p) if p != INDEX_FILE else "index.md")

    orphans = []
    for p in pages:
        slug = p.stem
        if slug not in inbound:
            orphans.append(slug)

    if orphans:
        for slug in orphans:
            issues.append(Issue("WARN", "orphans", f"{slug}.md", "no inbound wikilinks"))
        issues.insert(0, Issue("WARN", "orphans", "", f"{len(orphans)} orphan pages"))
    else:
        issues.insert(0, Issue("PASS", "orphans", "", "no orphan pages"))
    return issues


def run_all_checks():
    pages = all_pages()
    all_issues = []

    checks = [
        ("frontmatter", check_frontmatter),
        ("provenance", check_provenance),
        ("wikilinks", check_wikilinks),
        ("index", check_index_coverage),
        ("claims", check_claims),
        ("orphans", check_orphans),
    ]

    for name, fn in checks:
        issues = fn(pages)
        all_issues.extend(issues)

    return all_issues


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Wiki Lint — deterministic health checks")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--quiet", action="store_true", help="only show failures")
    args = parser.parse_args()

    if not WIKI_DIR.exists():
        print(f"FAIL: wiki directory not found at {WIKI_DIR}")
        sys.exit(1)

    issues = run_all_checks()

    if args.json:
        output = []
        for iss in issues:
            output.append({"level": iss.level, "check": iss.check, "file": iss.file, "msg": iss.msg})
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    fails = sum(1 for i in issues if i.level == "FAIL")
    warns = sum(1 for i in issues if i.level == "WARN")

    for iss in issues:
        if args.quiet and iss.level == "PASS":
            continue
        print(iss)

    print(f"\n{'='*50}")
    print(f"Total: {fails} FAIL, {warns} WARN")
    print(f"{'='*50}")

    sys.exit(1 if fails > 0 else 0)


if __name__ == "__main__":
    main()
