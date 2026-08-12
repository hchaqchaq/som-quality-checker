# SOM Validation Rules

The runtime source of truth is `quality_checker/src/quality_checker/checkers/som/config.py` and `validator.py`. This document describes only rules currently executed by the application.

## Workbook boundary

- The checker reads the first worksheet with pandas.
- Every configured column listed below is required before validation starts.
- `Check` and `Comment` are analysis result columns and are added or replaced.
- Scope filters are applied before rules execute; rules evaluate assessed rows only.

## Result

Each failed condition adds one to `Check`. Each SOM rule can add at most one failure to a row. `Comment` joins rule messages with `|`. A row without failures receives `Check = 0` and `Quality check passed`.

Rows excluded by scope filters receive `Check = Out of filters` and `Comment = Out of filters`. Assessed rows are exported before excluded rows.

## Configured column inventory

- `Manufacturer COFOR`
- `Manufacturer address`
- `Shipper COFOR2`
- `Shipper COFOR Address`
- `Quality contact`
- `Logistic contact`
- `Contacted`
- `Info completed`
- `NOTE`
- `Format check`
- `Status`
- `Completion date`
- `Plant`

`Completion date` retains its loaded value type. All other configured columns are cast to pandas string values and stripped before evaluation.

## Validation rules

| Rule                           | Tracked column          | Applies when                                                         | Accepted condition                                                                                                                         | Failure comment                                                                                               |
| ------------------------------ | ----------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| `status_completed`             | `Info completed`        | `Status` is `Complete` or `Completed`                                | `Info completed` is `Complete` or `Completed`                                                                                              | `INFO COMPLETED MUST BE COMPLETED`                                                                            |
| `completion_date`              | `Completion date`       | `Status` and `Info completed` are complete and `Contacted = Yes`     | A native date/datetime value or text in `DD/MM/YYYY` format                                                                                | `COMPLETION DATE IS MISSING` or `COMPLETION DATE IS INVALID`                                                  |
| `relance`                      | `NOTE`                  | `Info completed` is empty and `Contacted = Yes`                      | `NOTE` contains at least one valid `DD/MM/YYYY` date; its latest valid date is between the analysis date and three days earlier, inclusive | `RELANCE DATE IS MISSING OR INVALID`, `RELANCE DATE IS IN THE FUTURE`, or `RELANCE DATE IS OLDER THAN 3 DAYS` |
| `shipper_cofor_address`        | `Shipper COFOR Address` | Non-empty `Shipper COFOR2` and address participate in comparison     | Every row with the same normalized `Shipper COFOR2` has the same normalized non-empty address                                              | `SHIPPER COFOR <value> HAS MULTIPLE ADDRESSES`                                                                |
| `manufacturer_cofor_address`   | `Manufacturer address`  | Non-empty `Manufacturer COFOR` and address participate in comparison | Every row with the same normalized `Manufacturer COFOR` has the same normalized non-empty address                                          | `MANUFACTURER COFOR <value> HAS MULTIPLE ADDRESSES`                                                           |
| `cofor_format`                 | `Format check`          | `Contacted = Yes` and `Info completed` is complete                   | `Format check` is not `NOK`                                                                                                                | `COFOR PATTERN (6 CHARS + 2 SPACES + 2 CHARS)`                                                                |
| `quality_contact_email`        | `Quality contact`       | Always                                                               | Exactly one non-empty email matching the configured email pattern                                                                          | `INVALID OR MISSING EMAIL: Quality contact`                                                                   |
| `logistic_contact_email`       | `Logistic contact`      | Always                                                               | Exactly one non-empty email matching the configured email pattern                                                                          | `INVALID OR MISSING EMAIL: Logistic contact`                                                                  |
| `contacted_when_status_filled` | `Contacted`             | `Status` is non-empty                                                | `Contacted = Yes`                                                                                                                          | `CONTACTED MUST BE YES WHEN STATUS IS FILLED`                                                                 |
| `note_date_format`             | `NOTE`                  | Always                                                               | At least one date-like token exists and every detected token is a real `DD/MM/YYYY` date                                                   | `NOTE DATE MUST USE DD/MM/YYYY`                                                                               |

Text choices trim surrounding whitespace and ignore case where stated. The configured email pattern accepts ASCII letters, digits, `.`, `_`, `%`, `+`, and `-` in the local part and requires a dotted alphabetic domain suffix of at least two characters.

## Rule details

### Completion date

The rule accepts Python `date`, Python `datetime`, and non-missing pandas `Timestamp` values. Text dates accept only `DD/MM/YYYY`. It does not reject future completion dates.

### Relance date

The analysis date defaults to the day the run starts. Tests and direct callers may provide another analysis date. The three-day window is inclusive. When `NOTE` contains multiple valid dates, only the latest date determines freshness.

### COFOR/address consistency

COFOR keys and addresses are normalized by trimming, collapsing internal whitespace, and ignoring case. Rows with an empty COFOR or empty address do not participate. Every participating row associated with a conflicting COFOR receives one failure.

The checker does not independently parse the COFOR text. The `cofor_format` rule trusts the workbook's `Format check` value and fails only when that value is `NOK` under its activation condition.

### Email fields

Both contact fields are required on every assessed row. Each field must contain exactly one email address. Lists separated by commas, semicolons, slashes, spaces, or newlines are not supported by the implemented SOM rule.

### NOTE format

The rule detects date-like tokens containing one- to four-digit year/day groups separated by `.`, `/`, or `-`. Every detected token must be a valid `DD/MM/YYYY` date. A note without any date-like token fails.

## Filtering

The GUI can provide filters for `Plant`, `Contacted`, and `Info completed`.

- Selecting all values for a field omits that filter.
- Filtered text is stripped before comparison.
- The GUI configures `Contacted` and `Info completed` comparisons without case folding.
- With no active filters, every loaded row is assessed.
- Filtering changes analysis scope; it does not change rule behavior.

## Export and history

The export is a new `.xlsx` workbook produced from the pandas result. It contains the configured source columns plus `Check` and `Comment`. It does not preserve the source workbook's formulas, formatting, macros, metadata, additional worksheets, or original interleaving of assessed and excluded rows.

Run history records one total for every rule and tracked column pair shown in the validation table, including zero-failure totals. It also records total rows, assessed rows, failed rows, timing, input path, export path when available, status, and an error message when supplied.
