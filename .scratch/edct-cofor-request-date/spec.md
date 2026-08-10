# Validate eDCT COFOR Request Dates

Status: ready-for-agent

## Problem Statement

eDCT users have added `Creation of Cofors request date` to `Supplier Level`, but the eDCT checker currently classifies this field as unchecked. A populated value can therefore contain an invalid date, and an assessed row can omit the date even when its supplier punch code is already present in the workbook's COFOR-creation reference sheet.

Users need the checker to distinguish between a required column and a conditionally required value. The column must always exist. Its value may remain empty when no corresponding punch code exists in the reference sheet, but it must be populated when a corresponding punch code exists. Every populated value must be a valid date.

Without this validation, an analysis run can report that an assessed row passed even though the COFOR request is missing or malformed.

## Solution

Add an eDCT validation rule for `Creation of Cofors request date`.

Require the `Supplier Level` column and the `Template-Cofor-Creation` worksheet. Require `Punch Code` in cell `D1` of that worksheet, ignore row 2, and build the reference set from non-empty values in `D3` downward.

For each assessed `Supplier Level` row, compare `Supplier Punch code` with the reference set using a normalized full match: trim surrounding whitespace and compare case-insensitively, while preserving all internal characters. Do not perform partial, fuzzy, or numeric-equivalence matching.

When a match exists, require a non-empty `Creation of Cofors request date`. Regardless of whether a match exists, validate every populated value as either a native Excel date or strict `DD.MM.YYYY` text. Accept any valid calendar date without past/future range restrictions.

Each failed condition contributes one validation failure to `Check`, a precise explanation to `Comment`, and a distinct run-history failure total.

## User Stories

1. As an eDCT quality analyst, I want `Creation of Cofors request date` assessed, so that the checker no longer ignores a business-critical field.
2. As an eDCT quality analyst, I want the column header to be required, so that analysis cannot silently skip the rule when the workbook template is incomplete.
3. As an eDCT quality analyst, I want `Template-Cofor-Creation` required, so that conditional requiredness is evaluated against the intended reference data.
4. As an eDCT quality analyst, I want the reference sheet name matched exactly, so that an obsolete or incorrectly named sheet does not silently replace the supported template.
5. As an eDCT quality analyst, I want the checker to require `Punch Code` in cell `D1`, so that it does not read an unrelated column after the template layout changes.
6. As an eDCT quality analyst, I want row 2 of the reference sheet ignored, so that its formulas or subheaders are not treated as punch-code data.
7. As an eDCT quality analyst, I want reference punch codes read from `D3` downward, so that the checker follows the actual workbook layout.
8. As an eDCT quality analyst, I want blank reference cells ignored, so that empty rows do not trigger required dates.
9. As an eDCT quality analyst, I want each assessed row's `Supplier Punch code` compared with the reference punch codes, so that requiredness is attached to the correct supplier.
10. As an eDCT quality analyst, I want surrounding whitespace ignored during punch-code comparison, so that harmless leading or trailing spaces do not prevent a match.
11. As an eDCT quality analyst, I want punch-code comparison to be case-insensitive, so that letter casing does not prevent a match.
12. As an eDCT quality analyst, I want the complete normalized punch code to match, so that substrings do not trigger unrelated rows.
13. As an eDCT quality analyst, I want leading zeros to remain significant, so that `00123` does not incorrectly match `123`.
14. As an eDCT quality analyst, I want internal spaces and punctuation to remain significant, so that distinct business identifiers are not collapsed.
15. As an eDCT quality analyst, I want numeric-looking representations to remain distinct, so that `123.0` does not automatically match `123`.
16. As an eDCT quality analyst, I want a COFOR request date required when the supplier punch code exists in the reference set, so that every referenced COFOR request has a recorded date.
17. As an eDCT quality analyst, I want the date allowed to remain empty when the supplier punch code is absent from the reference set, so that the rule does not require work that has not been requested.
18. As an eDCT quality analyst, I want every populated date validated even when the punch code is absent, so that optional values cannot contain malformed dates.
19. As an eDCT quality analyst, I want native Excel date cells accepted, so that normal Excel date entry passes validation.
20. As an eDCT quality analyst, I want text dates accepted only in `DD.MM.YYYY`, so that textual date entry has one unambiguous format.
21. As an eDCT quality analyst, I want impossible calendar dates rejected, so that values such as `31.02.2026` cannot pass.
22. As an eDCT quality analyst, I want slash-formatted dates rejected, so that `DD/MM/YYYY` does not introduce a second textual convention.
23. As an eDCT quality analyst, I want timestamps rejected as text, so that the field remains a date rather than a date-time field.
24. As an eDCT quality analyst, I want past, current, and future dates accepted, so that this rule enforces validity rather than an unstated business range.
25. As an eDCT quality analyst, I want missing required workbook structure to stop analysis with a clear load error, so that incomplete validation is never presented as a successful run.
26. As an eDCT quality analyst, I want a missing matched date reported with the reason `Creation of Cofors request date is required because the Punch Code exists in Template-Cofor-Creation`, so that the corrective action is explicit.
27. As an eDCT quality analyst, I want an invalid populated date reported with the reason `Creation of Cofors request date has an invalid date format`, so that format failures are distinguishable from missing values.
28. As an eDCT quality analyst, I want a missing required date grouped under `date_required`, so that run history distinguishes completeness failures from malformed dates.
29. As an eDCT quality analyst, I want an invalid populated date grouped under `date`, so that it remains consistent with other eDCT date-validation totals.
30. As an eDCT quality analyst, I want each failure to increment the assessed row's `Check`, so that the correction count remains accurate.
31. As an eDCT quality analyst, I want each failure included in the assessed row's `Comment`, including the field and original value, so that exported results are actionable.
32. As an eDCT quality analyst, I want each failure included in run-history totals, so that quality trends include the new rule.
33. As an eDCT quality analyst, I want rows without either failure to retain the normal passing result, so that the new rule does not alter unrelated outcomes.
34. As an eDCT quality analyst, I want the source workbook preserved during analysis and export, so that validation does not rewrite punch codes or dates.

## Implementation Decisions

- Extend the eDCT checker project rather than the SOM validation path.
- Move `Creation of Cofors request date` from the unchecked field catalogue into the active date-validation configuration.
- Treat `Creation of Cofors request date` as a required column. A missing header is a workbook-structure failure that prevents analysis; an empty cell is governed separately by the conditional required-value rule.
- Add `Template-Cofor-Creation` to the required eDCT workbook boundary.
- Validate the reference layout by physical location and header: cell `D1` must contain exactly `Punch Code`.
- Ignore reference row 2 and collect non-empty punch codes from column D starting at row 3.
- Compare the assessed row's `Supplier Punch code` with the reference set.
- Normalize both sides for matching by converting to their textual value, trimming surrounding whitespace, and case-folding. Do not remove or alter internal spaces, punctuation, decimal suffixes, or leading zeros.
- Use complete-string set membership only. Do not use substring, fuzzy, or numeric-equivalence matching.
- Duplicate reference values have no additional effect; membership is boolean for each assessed row.
- A matching punch code makes `Creation of Cofors request date` a required value.
- A non-matching or empty punch code does not make the date a required value, but any populated date still undergoes format validation.
- Accept native Excel/Python date values through the existing eDCT date parser.
- Accept textual values only when they parse strictly as `DD.MM.YYYY`.
- Do not enable the slash-date exception used by dated-comment fields.
- Do not impose the no-future constraint used by `Effective kick-off date`.
- Emit exactly one `date_required` validation failure when a matched row has an empty date. Its reason is `Creation of Cofors request date is required because the Punch Code exists in Template-Cofor-Creation`.
- Emit exactly one `date` validation failure when a populated date cannot be parsed. Its reason is `Creation of Cofors request date has an invalid date format`.
- A matched row with a populated invalid date receives the format failure, not an additional required-value failure, because the required value is present.
- Reuse the existing eDCT failure aggregation so each occurrence increments `Check`, appears in `Comment` with the original cell value, and contributes to the corresponding rule/column failure count.
- Reuse the existing generic export, GUI preview, and run-history persistence paths; no rule-specific GUI or database schema change is required.

## Testing Decisions

- Use `run_edct_analysis` as the primary and highest behavioral test seam. Tests should create representative workbooks, run the public analysis operation, and assert row outcomes or load failures rather than inspect helper implementation.
- Exercise export through the existing `export_edct_result` seam only where needed to confirm that the new validation failures reach `Check` and `Comment` in the analysis workbook. Do not add GUI-specific tests because the GUI consumes generic eDCT results and needs no rule-specific branch.
- Follow the existing eDCT workbook-test prior art: construct row-2 `Supplier Level` headers and assessed rows, include required worksheets, run analysis, and inspect `EdctRunResult` plus exported cells.
- Extend the workbook fixture with the required target column and a `Template-Cofor-Creation` sheet whose `D1` is `Punch Code`, whose row 2 is ignored, and whose data begins at `D3`.
- Add structural behavior cases for a missing reference sheet, missing target column, wrong `D1` header, and punch-like content outside the supported D-column layout. Each must prevent analysis with a clear `EdctLoadError`.
- Add requiredness behavior cases for a normalized match with an empty date, a normalized match with a valid date, a non-match with an empty date, and a non-match with a populated invalid date.
- Add matching boundaries for surrounding whitespace and letter case, plus non-matches for partial values, leading-zero differences, internal-space differences, punctuation differences, and `123.0` versus `123`.
- Add date boundaries for native Excel dates, valid strict `DD.MM.YYYY` text, slash text, impossible dates, malformed text, text timestamps, and valid future dates.
- Assert observable failure contracts: row `Check`, exact `Comment` reason and field name, original empty/value rendering, failed-row count, and distinct `date_required`/`date` failure totals.
- Confirm that a populated invalid date produces one format failure rather than both format and required-value failures.
- Confirm that duplicate reference punch codes do not duplicate row failures.
- Confirm that unaffected assessed rows retain the standard passing result.
- Good tests defend workbook-level and row-level behavior. They must not assert private helper names, source-code structure, internal set construction, or incidental implementation order beyond the established exported comment contract.

## Out of Scope

- Changing SOM checker behavior.
- Renaming `Creation of Cofors request date` or correcting its business spelling.
- Supporting aliases for `Template-Cofor-Creation`.
- Discovering `Punch Code` by header outside cell `D1`.
- Reading reference punch codes from row 2 or from columns other than D.
- Partial, fuzzy, punctuation-insensitive, internal-whitespace-insensitive, or numeric-equivalence punch-code matching.
- Treating `123.0` and `123` as equivalent.
- Treating values with and without leading zeros as equivalent.
- Accepting slash dates, alternate textual date formats, or textual timestamps.
- Restricting dates to past dates, the analysis date, or any other business range.
- Requiring the date when the supplier punch code is absent from the reference set.
- Requiring unmatched rows to keep the date empty.
- Changing export layout, GUI preview columns, database schema, or run-history storage design.
- Correcting workbook values automatically.

## Further Notes

- The inspected workbook uses the exact sheet name `Template-Cofor-Creation`, stores `Punch Code` at `D1`, contains formulas/subheaders on row 2, and begins punch-code values at `D3`.
- `Creation of Cofors request date` already exists in the current eDCT field catalogue but is explicitly unchecked. This feature activates it without introducing a new workbook column name.
- The existing eDCT date parser already provides the desired native-date and strict `DD.MM.YYYY` behavior. The new rule should reuse that convention without the dated-comment slash exception or the effective-kickoff future-date restriction.
- The selected test seams match the current architecture: public analysis for structural and row behavior, with focused export/history assertions for established downstream contracts.
