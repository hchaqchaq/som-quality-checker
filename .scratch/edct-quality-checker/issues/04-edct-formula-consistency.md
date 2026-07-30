# 04 — Detect inconsistent eDCT formulas

**What to build:** Validate every configured formula column against the formula in the first indexed supplier row, allowing expected row translation and harmless formatting differences while flagging changed or unavailable formulas.

**Blocked by:** 02 — Run an eDCT workbook through the complete application.

**Status:** resolved

- [ ] Every configured formula column uses the formula reference row.
- [ ] Later rows are compared after translating expected row-relative references.
- [ ] Formula comparison ignores letter case, whitespace outside quoted values, and an optional leading `+`.
- [ ] Changed functions, operators, references, conditions, or quoted values fail.
- [ ] Empty cells and manually entered constants fail when a valid reference formula exists.
- [ ] If the formula reference row lacks a formula, every assessed row receives one failure for that formula column.
- [ ] Missing-reference comments state that the formula reference row is missing the reference formula and include the exact column name.
- [ ] A missing reference for one formula column does not stop other rules or formula columns.
- [ ] The checker does not recalculate formulas or validate their calculated results.
- [ ] Workbook-level tests cover translated formulas, harmless differences, changed logic, constants, missing formulas, and a missing first-row baseline.

## Answer

Implemented formula-reference-row learning, row-relative translation, normalized comparison, per-column failures, and continuation after missing baselines.
