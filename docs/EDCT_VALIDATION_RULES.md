# eDCT Validation Rules

The runtime source of truth is the eDCT Python configuration. The legacy
`materials/edct_vallidation_rules.xlsx.xlsx` workbook is retained only as the original business-rule source; the application never loads it.

## Workbook boundary

- Required worksheets: `Supplier Level` and `Open Task`.
- `Supplier Level` headers are on row 2.
- `Open Task` must contain `Punch Code`.
- A row is assessed only when `Index` is populated.
- `Supplier Punch code` identifies the supplier for the cross-sheet rule.
- `Supplier name` is included in the result preview.

## Result

Each failed field or condition adds one to `Check`. `Comment` groups fields with the same failure reason and separates different reasons with `|`. A row without failures receives `Check = 0` and `Quality check passed`.

The exported workbook preserves the source values and worksheets. `Check` and `Comment` are added or replaced inside `Tabella2`.

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
- `Phone`
- `Phone2`
- `Phone3`
- `Phone4`
- `Phone5`
- `Phone6`
- `Phone7`
- `First communication sent`
- `Planned Kick-off meeting`
- `Kick-off Invitation sent`
- `Kick-off meeting postponed date`
- `Effective kick-off date`
- `Cofor created date`
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
- `Shipping location`
- `Overseas`
- `Supplier Confimation`
- `OPEN TASK`
- `EDI Mode`

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

The checker does not calculate formulas or validate their displayed results.

## Field rules

| Fields                                                                                                                                                                              | Applies when                                              | Empty allowed | Accepted value                                                         |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | ------------: | ---------------------------------------------------------------------- |
| `Sales contact`, `Logistic contact`                                                                                                                                                 | `Effective kick-off date` is populated                    |           Yes | Plain emails separated by `;`; trailing semicolons are ignored         |
| `Plant Manager`, `Logistic Manager contact`, `Key Account Contact`, `Logistic specialist Contact`, `Transport manager`, `Packaging Specialist`, `EDI Contact`, `Participants`       | When populated                                            |           Yes | Plain emails separated by `;`; trailing semicolons are ignored         |
| `Seller COFOR`, `Manufacturer COFOR`, `Shipper COFOR`, `Empty Cofor`                                                                                                                | `Effective kick-off date` is populated                    |           Yes | Six alphanumeric characters, two spaces, two alphanumeric characters   |
| `Phone`, `Phone2`, `Phone3`, `Phone4`, `Phone5`, `Phone6`, `Phone7`                                                                                                                 | When populated                                            |           Yes | 7-20 digits after removing spaces, `+`, parentheses, dots, and hyphens |
| `First communication sent`, `Planned Kick-off meeting`, `Kick-off Invitation sent`, `Kick-off meeting postponed date`, `Cofor created date`, `DDE Validated date /sent to edi team` | When populated                                            |           Yes | Native Excel date or `DD.MM.YYYY`                                      |
| `Effective kick-off date`                                                                                                                                                           | When populated                                            |           Yes | Native Excel date or `DD.MM.YYYY`; today or earlier                    |
| `Comments`, `Kick-off comments`                                                                                                                                                     | When populated                                            |           Yes | `DD.MM.YYYY: comment` or `DD/MM/YYYY: comment`                         |
| `Readiness Comments`, `EDI Comments`                                                                                                                                                | When populated                                            |           Yes | `DD.MM.YYYY: comment`                                                  |
| `Triple Status`                                                                                                                                                                     | `Cofor created date` is populated                         |            No | `Valid` or `No Valid`                                                  |
| `Overseas`                                                                                                                                                                          | Always                                                    |           Yes | `YES` or `NO`                                                          |
| `Shipping location`                                                                                                                                                                 | `Overseas = YES`                                          |            No | `YES` or `NO`                                                          |
| `Supplier Confimation`                                                                                                                                                              | Always                                                    |           Yes | `YES`                                                                  |
| `eSupplierConnect`, `B2B`, `New supplier portal`, `SPM`, `iTMS`                                                                                                                     | Required after `Effective kick-off date`; optional before |   Conditional | `YES` or `NOT`                                                         |
| `EDI Mode`                                                                                                                                                                          | Required after `Cofor created date`; optional before      |   Conditional | `WEB EDI` or `Standard EDI`                                            |
| `OPEN TASK`                                                                                                                                                                         | Cross-checked for every assessed row                      |   Conditional | `YES` when the punch code exists in `Open Task`; empty otherwise       |

Choice comparisons trim surrounding whitespace and ignore case. The exported workbook retains the original cell values.

## Explicitly unchecked fields

These legacy source fields remain unchanged and do not add failures:

- `Alten owner`
- `Priority`
- `Seller Name`
- `Seller address`
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
- `Creation of Cofors request date`
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
