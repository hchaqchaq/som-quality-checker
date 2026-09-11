# eDCT Validation Rules

The runtime source of truth is the eDCT Python configuration. The legacy
`../materials/edct_vallidation_rules.xlsx` workbook is retained only as the original business-rule source; the application never loads it.

## Workbook boundary

- Required worksheets: `Supplier Level`, `PN Level`, `Open Task`, and `Template-Cofor-Creation`.
- `Supplier Level` headers are on row 2. `PN Level` headers are on row 1 and must include `Punch seller` and `Triplet COFOR`, as in the reference workbooks.
- `Open Task` must contain `Punch Code` on row 2.
- `Template-Cofor-Creation` must contain `Punch Code` on row 2; reference values are read from row 3 downward.
- Supplier rows are assessed when `Index` is populated; `Line` is used only when the `Index` header is absent. A blank `Index` never falls back to `Line` on an individual row.
- `Supplier Punch code` identifies the supplier for the cross-sheet rules.
- PN rows are assessed when their nonblank `Punch seller` matches a punch code from assessed supplier rows. PN assessment does not require `Index` or `Line`; blank and unknown sellers are not assessed.
- `Supplier name` is included in the result preview.
- Export requires table `Tabella2` on `Supplier Level`; missing tables stop export after analysis.
- PN export does not require a table or a fixed table name; existing PN tables retain their ranges and definitions.

Workbook selection inspects these worksheets and required columns in a read-only worker process before enabling analysis. Header matching trims surrounding whitespace, ignores case, honors configured mappings, accepts the explicit `Index`/`Line` and `Supplier Confimation`/`Supplier Confirmation` aliases, and rejects ambiguous matches. Extra columns are allowed. Selection inspection does not scan assessed rows, check `Tabella2`, or create an analysis run.

The eDCT selection and Settings sample-workbook flows keep the GUI thread free and show indeterminate stage feedback. Analysis reports loading, PN validation, supplier validation, result preparation, export, and export verification stages at actual execution boundaries.

## Result

Each failed field or condition adds one to `Check`. `Comment` groups fields with the same failure reason and separates different reasons with `|`. A row without failures receives `Check = 0` and `Quality check passed`. Not assessed rows have no result annotations.

Results retain worksheet and source-row identity: `assessed_rows` contains `(worksheet, row)` pairs and `row_results` is keyed by those pairs. Equal row numbers on different sheets cannot collide. `pn_values` contains the resolved seller and triplet values for assessed PN rows, for preview display without exposing formula text.

One analysis run includes assessed rows and failed rows from both sheets. Rule/column totals count individual failures, not failed rows. Status `ok` means execution succeeded even when validation failures exist. Analysis history is recorded before export and updated with the exported path afterward.

The exported workbook preserves the source values and worksheets. `Check` and `Comment` are added or replaced inside Supplier `Tabella2`, and on `PN Level` without resizing its existing tables. Stale annotations are cleared on rows no longer assessed.

## Configured column inventory

This list is checked automatically against the executable configuration:

- `Index`
- `Triple Status`
- `Supplier Punch code`
- `Supplier name`
- `Onboarding Status`
- `Starting date`
- `Triplet COFOR`
- `Seller_Manuf`
- `Seller_Shipper`
- `Kick-off meeting postponed week`
- `Effective kick-off week`
- `Kick-off status`
- `Readiness status`
- `Sales contact`
- `Logistic contact`
- `Plant Manager`
- `Logistic Manager contact`
- `Key Account Contact`
- `Logistic specialist Contact`
- `Transport manager`
- `Packaging Specialist`
- `EDI Contact`
- `Participants`
- `Seller COFOR`
- `Manufacturer COFOR`
- `Shipper COFOR`
- `Empty Cofor`
- `First communication sent`
- `Planned Kick-off meeting`
- `Kick-off Invitation sent`
- `Kick-off meeting postponed date`
- `Effective kick-off date`
- `Cofor created date`
- `Creation of Cofors request date`
- `DDE Validated date /sent to edi team`
- `Comments`
- `Kick-off comments`
- `Readiness Comments`
- `EDI Comments`
- `eSupplierConnect`
- `B2B`
- `New supplier portal`
- `SPM`
- `iTMS`
- `Overseas`
- `Supplier Confimation`
- `OPEN TASK`
- `EDI Mode`
- `Punch seller`

## Formula rules

These columns must contain formulas:

- `Onboarding Status`
- `Starting date`
- `Triplet COFOR`
- `Seller_Manuf`
- `Seller_Shipper`
- `Kick-off meeting postponed week`
- `Effective kick-off week`
- `Kick-off status`
- `Readiness status`

For each column, the first assessed row is the formula reference row. Later formulas must have the same structure after expected row-relative translation. Comparison ignores function/cell-reference case, whitespace outside quoted values, and an optional leading `+`.

If the reference row lacks a formula, every assessed row receives:

```text
Formula validation failed: formula reference row is missing the reference formula for <column>
```

Supplier formula rules check formula structure, not calculated values. The PN membership rule below separately reads saved calculated identifiers.

## PN triplet membership

Build one mapping from each assessed supplier's normalized `Supplier Punch code` to a set of nonblank normalized `Triplet COFOR` values. Duplicate pairs are deduplicated on insertion; a nonblank punch with only blank triplets retains an empty allowed set. Excluded supplier rows and blank punch codes cannot authorize PN values.

For a known PN seller, `Triplet COFOR` must be nonblank and belong to that seller's allowed set. Each offending PN row receives exactly one `pn_triplet_cofor` failure, attributed to `Triplet COFOR`, even when the invalid pair repeats. Repeated valid pairs pass. Allowed supplier triplets need not occur on PN.

Both identifiers are compared after trimming surrounding whitespace and ignoring case. Internal whitespace, punctuation, and stored leading zeros remain significant. Triplet cells are whole identifiers, never comma- or slash-separated lists. No numeric coercion reconstructs or removes zeros.

Comments identify the seller, rejected triplet, and sorted allowed triplets, explicitly explaining blank rejected values and empty allowed sets. Original cells are not normalized or corrected.

Formula-valued identifiers use their saved calculated values from a companion `data_only` workbook. The checker does not calculate formulas. If a formula needed by this rule has no saved result or its cached result is an Excel error such as `#REF!`, analysis stops with its worksheet/cell location and instructions to correct formula errors, recalculate, and save in Excel. A saved empty string follows the normal blank-value policy. Unknown sellers do not require their triplet formulas to have cached results. The exporter retains original formulas and their cached results so the exported workbook can be analyzed again.

## Field rules

| Fields                                                                                                                                                                              | Applies when                                                                                      | Empty allowed | Accepted value                                                                                  |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------: | ----------------------------------------------------------------------------------------------- |
| `Sales contact`, `Logistic contact`                                                                                                                                                 | `Effective kick-off date` is populated                                                            |           Yes | Plain emails separated by `;`; trailing semicolons are ignored                                  |
| `Plant Manager`, `Logistic Manager contact`, `Key Account Contact`, `Logistic specialist Contact`, `Transport manager`, `Packaging Specialist`, `EDI Contact`, `Participants`       | When populated                                                                                    |           Yes | Plain emails separated by `;`; trailing semicolons are ignored                                  |
| `Seller COFOR`, `Manufacturer COFOR`, `Shipper COFOR`, `Empty Cofor`                                                                                                                | `Effective kick-off date` is populated                                                            |           Yes | Six alphanumeric characters, two spaces, two alphanumeric characters                            |
| `First communication sent`, `Planned Kick-off meeting`, `Kick-off Invitation sent`, `Kick-off meeting postponed date`, `Cofor created date`, `DDE Validated date /sent to edi team` | When populated                                                                                    |           Yes | Native Excel date or `DD/MM/YYYY`                                                               |
| `Creation of Cofors request date`                                                                                                                                                   | Required when `Supplier Punch code` exists in `Template-Cofor-Creation`; otherwise when populated |   Conditional | Native Excel date or `DD/MM/YYYY`                                                               |
| `Supplier Punch code`                                                                                                                                                               | `Creation of Cofors request date` is populated                                                    |            No | Exact Punch Code from `Template-Cofor-Creation` column D, rows 3 onward                         |
| `Effective kick-off date`                                                                                                                                                           | When populated                                                                                    |           Yes | Native Excel date or `DD/MM/YYYY`; today or earlier                                             |
| `Comments`, `Kick-off comments`, `Readiness Comments`, `EDI Comments`                                                                                                               | When populated                                                                                    |           Yes | `DD/MM/YYYY: comment`                                                                           |
| `Triple Status`                                                                                                                                                                     | `Cofor created date` is populated                                                                 |            No | `Valid` or `No Valid`                                                                           |
| `Overseas`                                                                                                                                                                          | Always                                                                                            |           Yes | Exact `YES`, `NOT`, or empty after trimming surrounding whitespace                              |
| `Supplier Confimation`                                                                                                                                                              | Always                                                                                            |           Yes | `YES`                                                                                           |
| `eSupplierConnect`, `B2B`, `New supplier portal`, `SPM`, `iTMS`                                                                                                                     | Required after `Effective kick-off date`; optional before                                         |   Conditional | `YES` or `NOT`                                                                                  |
| `EDI Mode`                                                                                                                                                                          | Required after `Cofor created date`; optional before                                              |   Conditional | `WEB EDI` or `Standard EDI`                                                                     |
| `OPEN TASK`                                                                                                                                                                         | Cross-checked for every assessed row                                                              |   Conditional | `YES` when the punch code exists in `Open Task`; empty otherwise                                |
| `PN Level.Triplet COFOR`                                                                                                                                                            | `Punch seller` matches an assessed supplier punch code                                            |            No | One whole triplet from that supplier's allowed set; trim surrounding whitespace and ignore case |

Choice comparisons trim surrounding whitespace and ignore case, except `Overseas`, which requires exact uppercase `YES` or `NOT`. The exported workbook retains original cell values and displays native dates in the eight validated date columns as `DD/MM/YYYY`.

## Explicitly unchecked fields

These legacy source fields remain unchanged and do not add failures:

- `Alten owner`
- `Priority`
- `Seller Name`
- `Seller address`
- `Phone`
- `Phone2`
- `Phone3`
- `Phone4`
- `Phone5`
- `Phone6`
- `Phone7`
- `Shipping location`
- `Manufacturer Name`
- `Manufacturer company address`
- `Shipper Cofor Name`
- `Shipper address`
- `Seller/Manuf already in EQP`
- `Seller/Shipper already in EQP`
- `EDI already known`
- `Plants`
- `Incoterm`
- `Planned Kick-off week`
- `ABP Training`
- `EDI EQP No`
- `EDI Scenario`
- `Date of Start of EDI validation / migration`
- `UNB DELFOR`
- `Qualifier UNB DELFOR`
- `UNB DELJIT`
- `Qualifier UNB DELJIT`
- `UNB DESADV`
- `Qualifier UNB DESADV`
- `Hybrid Cofor`
- `EQP Status`
- `CZ STATUS DELJIT`
- `CZ progress (Avancement CZ) EQP step`
- `CZ current step (Etape courante CZ)`
- `Status CZ Date of DELJIT/DESADV`
- `MF STATUS DELFOR`
- `MF progress (Avancement MF) EQP step`
- `MF current step (Etape courante MF)`
- `Status MF Date of DELFOR`
- `Status EDI Certified`
- `SET UP IN CORAIL`

## Verified sample smoke

On 2026-07-30, `materials/eDCT_input.xlsx` produced 112 assessed rows and 33 failed rows. The exported copy retained all 11 worksheets, all 16 XML parts containing extension lists, and every source package part; it contained `Check` and `Comment`, and the source file hash remained unchanged.

Unsupported OOXML extension lists are restored from the source package after `openpyxl` saves the annotated workbook. Source cell values, formulas, styles, tables, worksheets, and legacy data-validation extensions are preserved.

## Tracked rule identifiers

Run history records one failure total per rule and field. Zero-failure rule/field pairs are not stored for eDCT.

| Rule                    | Tracked fields or condition                                                     |
| ----------------------- | ------------------------------------------------------------------------------- |
| `formula`               | Every configured formula column                                                 |
| `email`                 | Every configured email column                                                   |
| `cofor`                 | `Seller COFOR`, `Manufacturer COFOR`, `Shipper COFOR`, `Empty Cofor`            |
| `date`                  | Every configured date column when its populated value has an invalid format     |
| `date_future`           | `Effective kick-off date` when later than the analysis date                     |
| `dated_comment`         | `Comments`, `Kick-off comments`, `Readiness Comments`, `EDI Comments`           |
| `triple_status`         | `Triple Status`                                                                 |
| `overseas`              | `Overseas`                                                                      |
| `supplier_confirmation` | `Supplier Confimation`                                                          |
| `portal`                | `eSupplierConnect`, `B2B`, `New supplier portal`, `SPM`, `iTMS`                 |
| `edi_mode`              | `EDI Mode`                                                                      |
| `date_required`         | `Creation of Cofors request date` when required by `Template-Cofor-Creation`    |
| `cofor_template`        | `Supplier Punch code` when a request date is populated without a template match |
| `open_task`             | `OPEN TASK` for both matching and non-matching `Open Task` punch codes          |
| `pn_triplet_cofor`      | `Triplet COFOR` on assessed `PN Level` rows                                     |

An empty required `Creation of Cofors request date` receives `date_required`; a populated value with an invalid format receives `date`. A populated request date whose `Supplier Punch code` is absent from `Template-Cofor-Creation` receives `cofor_template`; this failure is independent of date-format validation.
