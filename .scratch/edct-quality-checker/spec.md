# Add eDCT as a Second Quality-Checker Project

## Problem Statement

The application currently supports only SOM workbook quality checking. Users also need to assess eDCT onboarding workbooks without maintaining a second desktop application or mixing eDCT rules into SOM behavior.

An eDCT workbook is structurally different: it contains multiple worksheets, uses `Supplier Level` as the main assessment sheet, depends on `Open Task` for a cross-sheet rule, contains formulas that must remain intact, and needs project-specific validation. The current single-project navigation, values-based export, and unscoped run history do not support that workflow safely.

## Solution

Add an initial project-selection screen offering `SOM Quality Checker` and `eDCT Quality Checker`. Preserve the existing SOM experience. The eDCT experience lets the user select an input workbook and output folder, assesses every `Supplier Level` row whose `Index` is populated, annotates a complete workbook copy with `Check` and `Comment`, and displays eDCT-only history.

Executable eDCT rules live in dedicated Python configuration. A Markdown catalogue documents those rules. The legacy Excel rules workbook remains as a non-runtime source document.

The eDCT checker preserves every worksheet, formula, style, source value, and row position. It adds or replaces `Check` and `Comment` inside `Tabella2` and never overwrites the input workbook.

## User Stories

1. As a quality analyst, I want to choose SOM or eDCT when the application opens, so that one application supports both projects.
2. As a SOM user, I want the existing workflow preserved, so that adding eDCT does not disrupt current work.
3. As a user, I want to return to project selection, so that I can switch checker projects without restarting.
4. As an eDCT user, I want to select the input workbook and output folder, so that current files and storage locations remain under my control.
5. As an eDCT user, I want `Supplier Level` and `Open Task` required, so that validation never runs against an incomplete workbook.
6. As an eDCT user, I want all missing sheets and active-rule columns reported together, so that template problems are efficient to correct.
7. As an eDCT user, I want only rows with a populated `Index` assessed, so that unused rows are ignored.
8. As an eDCT user, I want every indexed row assessed without filters, so that no supplier is silently excluded.
9. As an eDCT user, I want `Check` to count every validation failure, so that each row has a useful correction total.
10. As an eDCT user, I want `Comment` to name exact fields and reasons, so that corrections are actionable.
11. As an eDCT user, I want passed rows marked with `Check = 0` and `Quality check passed`, so that successful assessment is explicit.
12. As an eDCT user, I want email cells to contain one valid address or addresses separated only by `;`, so that contact data has one reliable format.
13. As an eDCT user, I want malformed emails, alternate separators, display names, and surrounding text rejected, so that inconsistent contact data is visible.
14. As an eDCT user, I want populated COFOR fields to use the six-character, two-space, two-character pattern, so that identifiers are valid.
15. As an eDCT user, I want optional phone fields to reject implausible populated values, so that arbitrary text does not pass.
16. As an eDCT user, I want native Excel dates and `DD.MM.YYYY` text accepted, so that normal date entry works.
17. As an eDCT user, I want only `Effective kick-off date` to reject future dates, so that planned dates remain valid.
18. As an eDCT user, I want dated comments to require a valid date, colon, and non-empty text, so that timeline comments are consistent.
19. As an eDCT user, I want `Triple Status` required as `Valid` or `No Valid` after `Cofor created date`, so that created COFOR records have an outcome.
20. As an eDCT user, I want `Shipping location` required as `Yes` or `No` when `Overseas = Yes`, so that overseas routing is explicit.
21. As an eDCT user, I want portal readiness fields required as `YES` or `NOT` after effective kickoff, so that readiness is complete at the correct stage.
22. As an eDCT user, I want `EDI Mode` required after `Cofor created date`, so that created records have a supported mode.
23. As an eDCT user, I want choice values compared case-insensitively after trimming while preserving original export values, so that harmless formatting does not cause failures or rewrite data.
24. As an eDCT user, I want `OPEN TASK = YES` when the punch code exists in `Open Task`, so that tracked work is reflected.
25. As an eDCT user, I want `OPEN TASK` empty when the punch code is absent from `Open Task`, so that stale values are flagged.
26. As an eDCT user, I want formula columns compared with the first processed row, so that copied formula structures remain consistent.
27. As an eDCT user, I want row-relative formula references and harmless case, whitespace, or leading-plus differences accepted, so that equivalent formulas pass.
28. As an eDCT user, I want changed formula logic, constants, or missing formulas rejected, so that broken calculations are visible.
29. As an eDCT user, I want every processed row flagged when the first row lacks a reference formula, so that the unavailable baseline is visible without stopping other checks.
30. As an eDCT user, I want explicitly excluded fields left unchecked, so that the checker does not invent rules.
31. As an eDCT user, I want the entire workbook preserved in export, so that auxiliary sheets, formulas, formatting, and tables remain usable.
32. As an eDCT user, I want `Check` and `Comment` inside `Tabella2`, so that table filtering and styling include results.
33. As an eDCT user, I want reruns to replace result columns, so that duplicate fields are not created.
34. As an eDCT user, I want timestamped `_eDCT_checked_` filenames, so that the source workbook is never overwritten.
35. As an eDCT user, I want a compact preview of index, punch code, supplier, check, and comment, so that results remain readable.
36. As an eDCT user, I want analysis off the UI thread, so that the desktop application stays responsive.
37. As a quality manager, I want SOM and eDCT histories separated by project, so that their metrics are not mixed.
38. As a quality manager, I want existing history preserved as SOM during migration, so that no historical data is lost.
39. As a quality manager, I want failed eDCT attempts retained with their error messages, so that structural problems can be investigated.
40. As a maintainer, I want executable eDCT rules separate from SOM configuration, so that both projects remain understandable.
41. As a maintainer, I want a Markdown rule catalogue, so that business rules can be reviewed without reading Python.
42. As a maintainer, I want the legacy Excel rules retained but excluded from runtime, so that provenance remains without creating two rule sources.
43. As a maintainer, I want executable configuration and documentation checked for drift, so that documented fields match active rules.

## Implementation Decisions

- Keep one application and add project selection instead of building another executable.
- Preserve SOM and add a dedicated eDCT configuration and analysis path.
- Use existing validation helpers only when their semantics match; eDCT email validation is intentionally stricter.
- Keep Excel work on the existing worker-thread pattern.
- Use openpyxl for eDCT to preserve the complete workbook.
- Require `Supplier Level` and `Open Task`; read `Supplier Level` headers from row 2.
- Assess only rows with a populated `Index`.
- Reference columns by name, never by Excel letters.
- Resolve legacy `AY`, `BP`, and `AC` references respectively as `Effective kick-off date`, `Cofor created date`, and `Overseas`.
- Normalize for validation only; preserve original values.
- Count one failure per failed field or condition and group compatible comment reasons with ` | `.
- Keep dates optional unless another condition requires data.
- Learn each formula structure from the first processed row and translate row-relative references for comparison.
- If the first formula baseline is missing, add one named failure to every processed row and continue.
- Preserve explicitly unchecked fields without validation.
- Reuse existing result columns or append them inside `Tabella2`.
- Export as `<original-name>_eDCT_checked_YYYYMMDD_HHMMSS.xlsx`.
- Add a project discriminator to history; migrate existing rows to `SOM`.
- Keep one SQLite database and filter history by project.
- Show only `Index`, `Supplier Punch code`, `Supplier name`, `Check`, and `Comment` in the eDCT preview.
- Keep the legacy rules workbook as a documented non-runtime source.
- Do not add a generic checker-plugin framework or new dependency.

## Testing Decisions

- Test external behavior through the highest practical seam.
- The primary seam supplies a workbook to the public analysis/export workflow and inspects the exported workbook plus SQLite history.
- Programmatically generated workbooks cover structure validation, indexed-row selection, field and conditional rules, formula translation, missing formula baselines, cross-sheet matching, result aggregation, table extension, naming, and project history.
- Tests assert exact `Check` totals and relevant field names/reasons in `Comment`.
- Export tests verify every original sheet, representative formulas and styles, original values, row order, and an unchanged source file.
- Migration tests verify existing runs become `SOM`, eDCT runs remain separate, and failed attempts are recorded.
- One thin offscreen GUI seam covers project selection, eDCT controls, absence of SOM filters, compact preview, project history, and back navigation.
- Existing pytest validation and database tests provide the repository's prior art.
- The real sample workbook is a smoke test whose observed processed and failed counts are reported rather than predetermined.

## Out of Scope

- Validating other worksheets except reading `Open Task` for its cross-sheet rule.
- Adding SOM-style filters to eDCT.
- Recalculating formulas or validating calculated results.
- Detecting a consistently wrong formula copied from the first processed row.
- Loading runtime rules from the legacy Excel workbook.
- Letting users choose a rule file.
- Automatically correcting source values.
- Overwriting the input workbook.
- Removing the legacy rules workbook.
- Validating explicitly excluded fields.
- Adding a generic plugin architecture or new dependency.
- Displaying the Markdown rule catalogue inside the application.

## Further Notes

- Canonical spelling is `eDCT`.
- `materials/eDCT_input.xlsx` is development evidence, not a hardcoded runtime input.
- `materials/edct_vallidation_rules.xlsx.xlsx` remains the legacy non-runtime source despite its spelling and duplicate extension.
- The Markdown catalogue documents every active field, condition, empty-value policy, accepted format/value, and failure behavior, plus excluded fields.
- The detailed implementation sequence is in `docs/superpowers/plans/2026-07-30-edct-quality-checker.md`.
