# SOM Quality Checker

## Purpose

SOM Quality Checker is a desktop application that analyzes the first worksheet of an Excel workbook, applies validation rules to selected rows, exports an annotated analysis workbook, and stores execution history in SQLite.

The checker reports data-quality problems. It does not silently repair or rewrite source values.

## User workflow

1. Select an input Excel workbook.
2. Select an output folder.
3. Optionally filter rows by `Plant`, `Contacted`, and `Info completed`.
4. Run the analysis.
5. Review the preview and status summary.
6. Open the exported analysis workbook.
7. Review previous runs and rule totals in History.

Selecting `All` means that field does not restrict the analysis scope. With no explicit filters, all rows are assessed.

## Result semantics

An assessed row with no failures:

```text
Check: 0
Comment: Quality check passed
```

A row excluded by the filters:

```text
Check: Not assessed
Comment: Not assessed
```

A row with several failures:

```text
Check: 4
Comment: Missing required value: Quality contact, Seller COFOR2 | Invalid email: Logistic contact | Invalid COFOR pattern: Manufacturer COFOR
```

`Check` is the total number of validation failures. Field-level rules contribute one per failing field; row-level consistency rules contribute one per failed condition.

`Comment` groups fields with the same failure reason. Different reasons are separated with ` | `. Missing values and malformed values are reported separately.

## Required columns

The first worksheet must contain:

- `Seller COFOR2`
- `Manufacturer COFOR`
- `Manufacturer address`
- `Shipper COFOR2`
- `Shipper COFOR Address`
- `Location ID2`
- `Location ID Address`
- `Quality contact`
- `Logistic contact`
- `Contacted`
- `Info completed`
- `NOTE`
- `Owner`
- `Format check`
- `Status`
- `SOM double-check`
- `Plant`

If any required column is absent, the whole analysis stops and the error lists every missing column.

## Validation rules

### Email fields

`Quality contact` and `Logistic contact` are required values. Empty values fail. Populated values must contain valid email addresses.

Multiple addresses may be separated by commas, semicolons, slashes, newlines, or supported spacing. Each failing field contributes one to `Check`.

### COFOR fields

`Seller COFOR2`, `Manufacturer COFOR`, and `Shipper COFOR2` are required values. Each must contain six alphanumeric characters, two spaces, and two alphanumeric characters.

Each empty or malformed field contributes one failure.

### Location ID

`Location ID2` is required and must contain exactly 12 characters after surrounding whitespace is ignored.

### Contacted

When a row is assessed, `Contacted` must contain one of these case-insensitive values:

- `yes`
- `no`
- `out of scope`

An empty or unsupported value contributes one failure.

### Location fields

These fields are required:

- `Manufacturer address`
- `Shipper COFOR Address`
- `Location ID Address`

A populated value must contain a recognized location signal such as a postal code, street number, city/country pattern, or supported street-type keyword. Each empty or invalid field contributes one failure.

### Excel error tokens

The following fields are checked for Excel error tokens:

- `Info completed`
- `Format check`
- `Owner`

Detected tokens include `#N/A`, `#REF!`, `#VALUE!`, `#DIV/0!`, `#NAME?`, `#NULL!`, `#NUM!`, and `#GETTING_DATA`.

Empty values do not fail this rule. `Format check` and `Owner` remain optional, and `Info completed` has no separate general required-value rule.

### Status consistency

When `Status` is `Complete`, an empty `Info completed` value contributes one failure:

```text
Missing required value: Info completed is empty while Status is "Complete"
```

### Manufacturer consistency

Rows sharing a non-empty `Manufacturer COFOR` must not contain conflicting non-empty `Manufacturer address` values.

Each affected row receives one additional failure:

```text
Conflicting Manufacturer address: Manufacturer COFOR "ABC123  45" is linked to multiple addresses
```

### Shipper consistency

Rows sharing a non-empty `Shipper COFOR2` must not contain conflicting non-empty `Shipper COFOR Address` values.

Each affected row receives one additional failure:

```text
Conflicting Shipper COFOR Address: Shipper COFOR2 "XYZ789  12" is linked to multiple addresses
```

## Filtering

Filters determine whether a row is assessed; they do not change validation rules.

- `All` means no restriction for that field.
- No explicit filters means all rows are assessed.
- `Contacted` matching is case-insensitive.
- Other filter values are trimmed before comparison.
- Excluded rows receive `Not assessed`.
- Desktop, package, and smoke-test entry points use the same default scope semantics.

## Export

The analysis workbook:

- Preserves the original row order.
- Preserves original source values.
- Adds or replaces `Check` and `Comment`.
- Includes assessed and not-assessed rows.
- Uses normalized copies only while evaluating rules.
- Is written as a new `.xlsx` workbook.

It does not guarantee preservation of source formatting, formulas, merged cells, macros, workbook metadata, or additional worksheet behavior. Only the first worksheet is analyzed.

## Run history

History records validation independently from export. A successful analysis means validation completed; it does not guarantee that export succeeded.

History stores:

- Start and finish timestamps
- Duration
- Input file
- Exported file when available
- Total rows
- Assessed rows
- Failed rows
- Status
- Error message when applicable
- Failure totals by rule and field

Failed attempts are retained with `status = failed` and their error message.

`rows_failed` is the number of assessed rows having at least one failure, not the total failure count.

Deleting a run removes only its SQLite history metadata and related rule totals. It never deletes input or exported workbooks.

## Processing flow

```text
Select workbook
    ↓
Read first worksheet
    ↓
Verify required columns
    ↓
Create validation-normalized copy
    ↓
Apply explicit scope filters
    ↓
Evaluate rules on assessed rows
    ↓
Aggregate Check and Comment
    ↓
Mark excluded rows as Not assessed
    ↓
Restore original row order and values
    ↓
Record analysis history
    ↓
Export analysis workbook
```

## Current implementation gaps

The current code does not yet implement every documented rule:

- Empty email, COFOR, location ID, location, and `Contacted` values currently pass.
- Excluded rows currently say `Out of filters`.
- Export groups assessed rows before excluded rows.
- Export uses normalized values instead of preserving originals.
- CLI execution uses hidden default filters.
- Consistency comments omit the conflicting COFOR value.
- Failed analysis attempts are not recorded.
- Comments do not yet distinguish missing values from malformed values.
