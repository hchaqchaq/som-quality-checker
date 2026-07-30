# 03 — Apply eDCT field, lifecycle, and Open Task rules

**What to build:** Apply the agreed eDCT business rules to every indexed supplier row, producing one failure per invalid field or condition and actionable comments containing exact column names.

**Blocked by:** 02 — Run an eDCT workbook through the complete application.

**Status:** resolved

- [ ] Executable eDCT rules live separately from SOM configuration.
- [ ] Email fields accept one plain valid email or multiple plain emails separated only by `;`.
- [ ] Alternate separators, display names, surrounding text, empty email items, and malformed addresses fail.
- [ ] Populated COFOR fields require six alphanumeric characters, two spaces, and two alphanumeric characters.
- [ ] Optional phone fields accept numeric and international formatting only when 7–20 digits remain after supported punctuation is removed.
- [ ] Optional date fields accept native Excel dates or `DD.MM.YYYY` text.
- [ ] Only `Effective kick-off date` rejects future dates.
- [ ] `Comments` and `Kick-off comments` accept `DD.MM.YYYY: comment` or `DD/MM/YYYY: comment`.
- [ ] `Readiness Comments` and `EDI Comments` accept only `DD.MM.YYYY: comment`.
- [ ] When `Cofor created date` is populated, `Triple Status` is required as `Valid` or `No Valid`.
- [ ] When `Overseas = Yes`, `Shipping location` is required as `Yes` or `No`.
- [ ] After `Effective kick-off date`, the five portal fields are required as `YES` or `NOT`; before it, empty is allowed.
- [ ] When `Cofor created date` is populated, `EDI Mode` is required as `WEB EDI` or `Standard EDI`.
- [ ] `Supplier Confimation` accepts `YES` or empty, and `Overseas` accepts `YES`, `NO`, or empty.
- [ ] Choice comparisons trim and normalize case for validation while preserving original exported values.
- [ ] A punch code found in `Open Task` requires `OPEN TASK = YES` on `Supplier Level`.
- [ ] A punch code absent from `Open Task` requires `OPEN TASK` to be empty.
- [ ] Numeric and text punch codes compare consistently.
- [ ] Explicitly unchecked fields never contribute to `Check`.
- [ ] Each failed field or condition adds one to `Check`.
- [ ] Comments group compatible reasons, separate different reasons with ` | `, and name exact fields.
- [ ] Workbook-level tests exercise every rule through exported `Check` and `Comment` behavior.

## Answer

Implemented the configured field, lifecycle, comment, choice, Open Task, score, and exact-field comment rules with workbook-level tests.
