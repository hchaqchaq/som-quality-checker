# 02 — Run an eDCT workbook through the complete application

**What to build:** Deliver the first complete eDCT workflow: select a workbook and output folder, validate its structure, assess indexed supplier rows, export a preserved workbook with results, preview those results, and record the run in eDCT history.

**Blocked by:** 01 — Add checker-project selection and project-specific history.

**Status:** resolved

- [ ] The eDCT screen lets the user choose an input workbook and output folder.
- [ ] `Supplier Level` and `Open Task` are mandatory worksheets.
- [ ] Active-rule and dependency columns are validated by header name, with all missing structure reported together.
- [ ] `Supplier Level` headers are read from row 2.
- [ ] Only rows with a populated `Index` are assessed; eDCT has no scope filters.
- [ ] Passed rows receive `Check = 0` and `Comment = Quality check passed`.
- [ ] The entire workbook is copied without changing the input file.
- [ ] Original worksheets, formulas, formatting, source values, and row order remain present in export.
- [ ] Existing `Check` and `Comment` columns are reused; otherwise they are added inside `Tabella2`.
- [ ] The output filename follows `<original-name>_eDCT_checked_YYYYMMDD_HHMMSS.xlsx`.
- [ ] The preview shows only `Index`, `Supplier Punch code`, `Supplier name`, `Check`, and `Comment`.
- [ ] Excel processing and export run outside the UI thread.
- [ ] Successful and failed attempts appear only in eDCT history.
- [ ] A workbook-level acceptance test verifies export preservation and history through the public workflow.

## Answer

Implemented user-selected eDCT input/output, structural validation, indexed-row processing, preserved-workbook export, compact preview, worker execution, and eDCT history.
