# SOM Quality Checking

The shared business language for selecting workbook rows, assessing data quality, and recording the outcome.

## Language

**Required column**:
A column header that must exist in the first worksheet. Missing required columns prevent analysis.
_Avoid_: Mandatory field

**Required value**:
A non-empty cell required by a particular validation rule.
_Avoid_: Required column

**Analysis scope**:
The workbook rows selected for validation by the active filters.
_Avoid_: Filtered data

**Assessed row**:
A row inside the analysis scope on which validation rules were executed.
_Avoid_: Checked line

**Not assessed row**:
A row excluded from validation by the active filters. It is neither passed nor failed.
_Avoid_: Out of filters, skipped row

**Validation rule**:
A condition that defines valid values and empty-value behavior for one or more fields.
_Avoid_: Check

**Validation failure**:
One failed field-level validation or one failed row-level consistency condition.
_Avoid_: Error

**Check**:
The total number of validation failures on an assessed row.
_Avoid_: Status, result

**Comment**:
A human-readable explanation of a row's validation failures, including relevant field names and values.
_Avoid_: Error log

**Failed row**:
An assessed row with at least one validation failure.
_Avoid_: Invalid workbook

**Failure count**:
The total number of validation failures across fields and consistency rules.
_Avoid_: Failed rows

**Analysis run**:
One validation execution, independent of whether its result is exported.
_Avoid_: Export

**Analysis workbook**:
A new workbook derived from the source with `Check` and `Comment`; each checker project defines its preservation
guarantees.
_Avoid_: Corrected workbook, source workbook

**Checker project**:
The selected SOM or eDCT validation context, with its own workbook boundary, rules, and run history.
_Avoid_: Application

**Formula reference row**:
The first assessed eDCT row, whose formulas define the expected formula structures for later assessed rows.
_Avoid_: Template row, first worksheet row
