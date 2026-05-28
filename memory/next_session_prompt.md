---
note: 将此文件内容直接粘贴到新 session 作为初始 prompt，然后删除本文件。
---

# Next Session Prompt: Phase 4 Scaling Follow-up

Read `CLAUDE.md`, `memory/pipeline_status.csv`, and `memory/workflow_plan.md` first.

## Current status

- Canonical spectral table: created at `output/products/spectral/spectral_summary.csv`.
- Main scaling sample: 18 included, 5 excluded.
- Excluded clusters: Abell_0697, Abell_0750, MS2137-2353, RXJ1347.5-1145, ZwCl_0857.9+2107.
- Formal scripts:
  - `src/03_scaling/build_spectral_summary.py`
  - `src/03_scaling/fit_scaling_relations.py`
- Scaling script status: migrated and run successfully with CIAO Python + linmix.

## Key outputs

- `output/products/scaling/scaling_linmix_fixed_evolution_comparison_summary.csv`
- `output/products/scaling/scaling_linmix_fixed_evolution_exclude_bad_report.md`
- `output/products/scaling/scaling_quality_classification.csv`
- `output/figures/scaling/lx_m500_linmix_exclude_bad.png`
- `output/figures/scaling/tx_m500_linmix_exclude_bad.png`
- `output/figures/scaling/m500_tx_literature_style_exclude_bad.png`

Main exclude_bad results:
- Lx-M500 beta=0.76 -0.43/+0.39, scatter=0.194 dex.
- Tx-M500 beta=0.52 -0.25/+0.27, scatter=0.112 dex.

## Next priority

1. Add Lx-Tx fixed-evolution or no-evolution fit to `src/03_scaling/fit_scaling_relations.py`.
2. Add leave-one-out or high/suspect sensitivity tests for Abell_0068, Abell_0611, MACSJ0647.7+7015, MACSJ1206.2-0847.
3. Start planning core-excised spectral extraction/fitting for final literature-style comparison.

## Important caveats

- Do not use old `output/products/spectral/spectral_twostep_summary.csv` as final input.
- `weiwwqeo_scaling/` is a raw reference, not the formal output location.
- Core-excised scaling remains future work.
