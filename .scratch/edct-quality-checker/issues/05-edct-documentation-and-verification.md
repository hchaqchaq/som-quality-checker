# 05 — Document and verify the complete eDCT checker

**What to build:** Publish a human-readable rule catalogue aligned with executable configuration, update repository and domain documentation, and verify the complete SOM/eDCT application against generated fixtures and the real eDCT sample workbook.

**Blocked by:** 03 — Apply eDCT field, lifecycle, and Open Task rules; 04 — Detect inconsistent eDCT formulas.

**Status:** resolved

- [ ] Markdown documentation lists every checked field, applicability condition, empty-value policy, accepted format/value, and failure behavior.
- [ ] Formula-reference and `Open Task` behavior are documented explicitly.
- [ ] Every excluded field is listed separately.
- [ ] Executable configuration is identified as the runtime source of truth.
- [ ] `materials/edct_vallidation_rules.xlsx.xlsx` is retained and identified as a legacy non-runtime source.
- [ ] Repository documentation explains project selection and both checker workflows.
- [ ] The domain glossary defines checker project and formula reference row without implementation details.
- [ ] A consistency test detects drift between configured rule targets and the Markdown catalogue.
- [ ] The full automated test suite covers SOM regression behavior and all eDCT acceptance seams.
- [ ] The real `materials/eDCT_input.xlsx` smoke run reports actual processed and failed row counts.
- [ ] The smoke run confirms every original worksheet remains and the source file is unchanged.
- [ ] Final verification reports test, smoke, and diff-check evidence.

## Answer

Published the executable-rule catalogue and repository/domain documentation, added a configuration-drift test, and recorded the verified real-sample smoke results.
