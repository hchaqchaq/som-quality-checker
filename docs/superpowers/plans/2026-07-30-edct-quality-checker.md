# eDCT Quality Checker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an eDCT checker beside SOM in the existing desktop application, validating `Supplier Level` from a user-selected multi-sheet workbook while preserving the complete workbook on export.

**Architecture:** Keep SOM behavior intact. Add one eDCT configuration module and one eDCT analysis module that use `openpyxl` to preserve workbook sheets, formulas, tables, and styles. Add a project-selection page to the existing PyQt window and store `SOM`/`eDCT` on history rows so each checker displays only its own runs.

**Tech Stack:** Python 3.12+, pandas, openpyxl, PyQt6, SQLite, pytest, uv.

## Global Constraints

- Use `eDCT` as the canonical display and documentation name.
- Users select the input workbook and output folder; never hardcode either path.
- Require worksheets named exactly `Supplier Level` and `Open Task`.
- `Supplier Level` headers are on Excel row 2; process only rows whose `Index` is populated.
- Preserve every worksheet, formula, style, and original cell value in the exported workbook.
- Add or replace `Check` and `Comment` inside the existing `Tabella2` table.
- Normalize values only for validation; leave exported source values unchanged.
- The formula reference row supplies each formula column's reference formula.
- If its reference formula is missing, add one failure to every assessed row for that column and continue.
- Keep `materials/edct_vallidation_rules.xlsx.xlsx` as a non-runtime legacy source.
- Do not add a new dependency.
- Keep Excel work off the PyQt UI thread.

---

## File Map

- Create `som_analyzer/src/som_analyzer/edct_config.py`: eDCT worksheet names, required columns, rule groups, allowed values, and output naming.
- Create `som_analyzer/src/som_analyzer/analysis/edct.py`: eDCT loading, primitive validation, formula comparison, cross-sheet validation, result aggregation, workbook export, and history insertion.
- Create `som_analyzer/tests/test_edct_analysis.py`: focused workbook fixtures and all eDCT analysis/export tests.
- Modify `som_analyzer/src/som_analyzer/db/schema.py`: add `project` to new `runs` tables.
- Modify `som_analyzer/src/som_analyzer/db/repository.py`: migrate existing databases, persist project, and filter history by project.
- Modify `som_analyzer/tests/test_validation_rules.py`: keep SOM history behavior covered after the schema change.
- Modify `som_analyzer/src/som_analyzer/analysis/runner.py`: write SOM history with `project="SOM"`.
- Modify `som_analyzer/src/som_analyzer/gui/app.py`: expose project-filtered history and eDCT execution to the UI.
- Modify `som_analyzer/src/som_analyzer/gui/screens.py`: add project selection, eDCT screen, worker, compact preview, back navigation, and project-specific history.
- Create `docs/EDCT_VALIDATION_RULES.md`: human-readable eDCT validation catalogue.
- Modify `README.md`: describe project selection and both checker workflows.
- Modify `CONTEXT.md`: add eDCT and shared checker terminology without implementation details.

---

### Task 1: Define and test eDCT primitive rules

**Files:**
- Create: `som_analyzer/src/som_analyzer/edct_config.py`
- Create: `som_analyzer/src/som_analyzer/analysis/edct.py`
- Create: `som_analyzer/tests/test_edct_analysis.py`

**Interfaces:**
- Produces: `EDCT_REQUIRED_SHEETS`, `EDCT_REQUIRED_COLUMNS`, `EDCT_FORMULA_COLUMNS`, and named rule groups in `edct_config.py`.
- Produces: `is_valid_edct_email(value: object) -> bool`.
- Produces: `is_valid_edct_phone(value: object) -> bool`.
- Produces: `parse_edct_date(value: object, *, allow_slash: bool = False) -> date | None`.
- Produces: `is_valid_dated_comment(value: object, *, allow_slash: bool) -> bool`.
- Produces: `normalize_choice(value: object) -> str`.

- [ ] **Step 1: Write failing primitive-rule tests**

```python
from datetime import date, datetime, timedelta

import pytest

from som_analyzer.analysis.edct import (
    is_valid_dated_comment,
    is_valid_edct_email,
    is_valid_edct_phone,
    parse_edct_date,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("first@company.com", True),
        ("first@company.com; second@company.com", True),
        ("first@company.com, second@company.com", False),
        ("Name - first@company.com", False),
        ("first@company.com; wrong-email", False),
        ("", True),
    ],
)
def test_edct_email_requires_semicolon_separated_plain_addresses(value, expected):
    assert is_valid_edct_email(value) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("+33 (0)1 23 45 67 89", True),
        (918657978599, True),
        ("123456", False),
        ("+33 call me", False),
        ("", True),
    ],
)
def test_edct_phone_accepts_optional_international_numbers(value, expected):
    assert is_valid_edct_phone(value) is expected


def test_edct_dates_accept_excel_or_dot_text():
    assert parse_edct_date(datetime(2026, 7, 30)) == date(2026, 7, 30)
    assert parse_edct_date("30.07.2026") == date(2026, 7, 30)
    assert parse_edct_date("30/07/2026") is None


def test_dated_comment_controls_slash_format():
    assert is_valid_dated_comment("30.07.2026: contacted supplier", allow_slash=False)
    assert is_valid_dated_comment("30/07/2026: contacted supplier", allow_slash=True)
    assert not is_valid_dated_comment("30/07/2026: contacted supplier", allow_slash=False)
    assert not is_valid_dated_comment("30.07.2026:", allow_slash=True)
```

- [ ] **Step 2: Run tests and verify the missing module/functions fail**

Run:

```powershell
Push-Location som_analyzer
uv run pytest tests/test_edct_analysis.py -q
Pop-Location
```

Expected: collection fails because `som_analyzer.analysis.edct` does not exist.

- [ ] **Step 3: Add declarative eDCT configuration**

Create constants for:

```python
EDCT_REQUIRED_SHEETS = ("Supplier Level", "Open Task")
EDCT_HEADER_ROW = 2
EDCT_INDEX_COLUMN = "Index"
EDCT_PROJECT = "eDCT"

EDCT_FORMULA_COLUMNS = (
    "Onboarding Status",
    "Starting date",
    "Triplet COFOR",
    "Seller_Manuf",
    "Seller_Shipper",
    "Kick-off meeting postponed week",
    "Effective kick-off week",
    "Kick-off status",
    "Readiness status",
)

EDCT_OPTIONAL_EMAIL_COLUMNS = (
    "Sales contact",
    "Logistic contact",
    "Plant Manager",
    "Logistic Manager contact",
    "Key Account Contact",
    "Logistic specialist Contact",
    "Transport manager",
    "Packaging Specialist",
    "EDI Contact",
    "Participants",
)

EDCT_COFOR_COLUMNS = (
    "Seller COFOR",
    "Manufacturer COFOR",
    "Shipper COFOR",
    "Empty Cofor",
)

EDCT_PHONE_COLUMNS = ("Phone", "Phone2", "Phone3", "Phone4", "Phone5", "Phone6", "Phone7")
EDCT_STANDARD_DATE_COLUMNS = (
    "First communication sent",
    "Planned Kick-off meeting",
    "Kick-off Invitation sent",
    "Kick-off meeting postponed date",
    "Effective kick-off date",
    "Cofor created date",
    "DDE Validated date /sent to edi team",
)
```

Build `EDCT_REQUIRED_COLUMNS` as the union of every active rule target and dependency, including `Index`, `Effective kick-off date`, `Cofor created date`, `Supplier Punch code`, `OPEN TASK`, `Overseas`, and `Shipping location`. Do not include fields explicitly documented as unchecked.

- [ ] **Step 4: Implement the minimum primitive validators**

Use `re.fullmatch`, `datetime.strptime`, `datetime.date`, and `pandas.isna`. Email validation splits only on `;`, trims each item, rejects empty items, and applies the existing email regex to every item. Phone validation removes ` +().-` and accepts 7–20 remaining digits. Dated comments split once on `:` and require both a valid date prefix and non-empty comment.

- [ ] **Step 5: Run the primitive tests**

Run:

```powershell
Push-Location som_analyzer
uv run pytest tests/test_edct_analysis.py -q
Pop-Location
```

Expected: all primitive-rule tests pass.

- [ ] **Step 6: Commit the primitive rules**

```powershell
git add som_analyzer/src/som_analyzer/edct_config.py som_analyzer/src/som_analyzer/analysis/edct.py som_analyzer/tests/test_edct_analysis.py
git commit -m "feat: define edct validation primitives"
```

---

### Task 2: Implement workbook validation and preservation

**Files:**
- Modify: `som_analyzer/src/som_analyzer/analysis/edct.py`
- Modify: `som_analyzer/src/som_analyzer/edct_config.py`
- Modify: `som_analyzer/tests/test_edct_analysis.py`

**Interfaces:**
- Produces: `EdctRunResult` with `input_file`, `workbook`, `assessed_rows`, `rows_failed`, `row_results`, `rule_totals`, `run_id`, and timing fields.
- Produces: `run_edct_analysis(input_path: Path | str, connection: sqlite3.Connection | None = None) -> EdctRunResult`.
- Produces: `export_edct_result(result: EdctRunResult, output_dir: Path | str) -> Path`.
- Produces: `normalize_formula(formula: str, *, origin: str, target: str) -> str`.
- Consumes later: GUI worker calls `run_edct_analysis` then `export_edct_result`.

- [ ] **Step 1: Add a minimal workbook fixture**

In `test_edct_analysis.py`, create an `openpyxl.Workbook` with:

- `Supplier Level` and `Open Task`.
- Metadata on row 1 and active headers on row 2.
- Two assessed rows with `Index` values and one ignored row with empty `Index`.
- A table named `Tabella2`.
- Valid first-row formulas and row-adjusted second-row formulas.
- `Open Task.Punch Code` matching only the first supplier.

Use `tmp_path` and save the fixture as `input.xlsx`.

- [ ] **Step 2: Write failing structure and row-boundary tests**

```python
def test_edct_requires_both_sheets(tmp_path):
    path = build_edct_workbook(tmp_path, include_open_task=False)
    with pytest.raises(EdctLoadError, match="Open Task"):
        run_edct_analysis(path)


def test_edct_processes_only_rows_with_index(tmp_path):
    result = run_edct_analysis(build_edct_workbook(tmp_path))
    assert result.assessed_rows == (3, 4)
```

- [ ] **Step 3: Implement workbook loading**

Load with `openpyxl.load_workbook(input_path, data_only=False)`. Validate both sheet names and all active-rule columns in one error. Map `Supplier Level` headers from row 2 and `Open Task` headers from row 2 after trimming header text. Process only rows where normalized `Index` is non-empty.

- [ ] **Step 4: Write failing field-rule tests**

Cover:

- Strict semicolon-separated email validation.
- COFOR format `^[A-Za-z0-9]{6} {2}[A-Za-z0-9]{2}$`.
- Optional phone and date formats.
- No-future check only for `Effective kick-off date`.
- `DD.MM.YYYY: comment` rules and slash allowance only for `Comments`/`Kick-off comments`.
- Case-insensitive `Triple Status`, portal, supplier-confirmation, overseas, and EDI-mode values.
- `Shipping location` required as yes/no only when `Overseas = Yes`.
- Portal fields required as yes/not only after `Effective kick-off date`.
- `EDI Mode` required only after `Cofor created date`.

Assert both numeric `Check` and exact field names in `Comment`.

- [ ] **Step 5: Implement row-rule aggregation**

Represent each failure as `(rule_name, column_name, message)`. Increment `Check` once per failed field/condition. Group identical messages by reason while retaining exact column names, separated by ` | `. Set `Comment = "Quality check passed"` when `Check == 0`.

Normalize for comparisons only. Never write normalized source values back to workbook cells.

- [ ] **Step 6: Write failing formula-reference tests**

```python
def test_formula_columns_use_formula_reference_row(tmp_path):
    path = build_edct_workbook(tmp_path, second_starting_date_formula='=IF(BB4="","",BB4)')
    result = run_edct_analysis(path)
    assert result.row_results[4].check == 1
    assert "Starting date" in result.row_results[4].comment


def test_missing_formula_reference_flags_every_assessed_row_and_continues(tmp_path):
    path = build_edct_workbook(tmp_path, first_starting_date_formula=None)
    result = run_edct_analysis(path)
    assert all(
        "formula reference row is missing the reference formula for Starting date" in result.row_results[row].comment
        for row in (3, 4)
    )
```

- [ ] **Step 7: Implement formula normalization**

Use `openpyxl.formula.translate.Translator` to translate the first formula from its origin cell to each target cell. Normalize both expected and actual formulas by:

- Removing an optional `+` immediately after `=`.
- Removing whitespace outside quoted strings.
- Comparing case-insensitively.

Do not ignore changed functions, operators, references, or quoted values. When the formula reference row lacks a formula, add one failure to every assessed row using:

```text
Formula validation failed: formula reference row is missing the reference formula for <column>
```

- [ ] **Step 8: Write failing `Open Task` tests**

```python
def test_open_task_requires_yes_only_for_matching_punch_codes(tmp_path):
    path = build_edct_workbook(tmp_path, first_open_task="", second_open_task="NO")
    result = run_edct_analysis(path)
    assert "OPEN TASK" in result.row_results[3].comment
    assert "OPEN TASK" in result.row_results[4].comment
```

The first punch code exists in `Open Task`, so blank fails; the second does not exist, so `NO` fails because it must be empty.

- [ ] **Step 9: Implement the cross-sheet rule**

Normalize numeric/text punch codes into stripped text without a trailing `.0`. Build a set from non-empty `Open Task.Punch Code` cells. Require `YES` for matches and an empty value for non-matches.

- [ ] **Step 10: Write failing export-preservation tests**

Assert:

- Every original sheet remains.
- Existing formulas and a styled cell remain unchanged.
- `Check` and `Comment` are added/replaced on `Supplier Level`.
- `Tabella2.ref` expands to include both result columns.
- The empty-`Index` row receives no results.
- Output matches `<stem>_eDCT_checked_YYYYMMDD_HHMMSS.xlsx`.

- [ ] **Step 11: Implement export**

Operate on the workbook already held by `EdctRunResult`. Reuse existing `Check`/`Comment` columns when present; otherwise append them after the current table boundary. Copy header/data styles from the adjacent table column using `copy.copy`, clear prior results, write results for assessed rows, extend `Tabella2.ref`, and save to the selected output directory without changing the input.

- [ ] **Step 12: Run the eDCT analysis tests**

Run:

```powershell
Push-Location som_analyzer
uv run pytest tests/test_edct_analysis.py -q
Pop-Location
```

Expected: all eDCT analysis and export tests pass.

- [ ] **Step 13: Commit workbook analysis**

```powershell
git add som_analyzer/src/som_analyzer/analysis/edct.py som_analyzer/src/som_analyzer/edct_config.py som_analyzer/tests/test_edct_analysis.py
git commit -m "feat: validate and export edct workbooks"
```

---

### Task 3: Separate run history by project

**Files:**
- Modify: `som_analyzer/src/som_analyzer/db/schema.py`
- Modify: `som_analyzer/src/som_analyzer/db/repository.py`
- Modify: `som_analyzer/src/som_analyzer/analysis/runner.py`
- Modify: `som_analyzer/src/som_analyzer/analysis/edct.py`
- Modify: `som_analyzer/tests/test_validation_rules.py`
- Modify: `som_analyzer/tests/test_edct_analysis.py`

**Interfaces:**
- Changes: `RunRecord.project: str`.
- Changes: `list_runs(connection, project: str, limit: int = 200) -> list[sqlite3.Row]`.
- Preserves: existing history rows migrate to `project = "SOM"`.

- [ ] **Step 1: Write failing migration and filtering tests**

Create an old `runs` schema without `project`, insert one run, call `initialize_schema`, and assert the migrated row has `project == "SOM"`. Insert an eDCT run and assert `list_runs(connection, "eDCT")` excludes SOM rows.

- [ ] **Step 2: Run history tests and verify failure**

Run:

```powershell
Push-Location som_analyzer
uv run pytest tests/test_validation_rules.py tests/test_edct_analysis.py -q
Pop-Location
```

Expected: failures show the missing `project` field and unsupported filter.

- [ ] **Step 3: Implement the schema migration**

Add:

```sql
project TEXT NOT NULL DEFAULT 'SOM'
```

to `RUNS_DDL`. Extend the existing migration path to add the column to old databases without losing runs or `run_columns`. Keep foreign keys enabled after migration.

- [ ] **Step 4: Thread project through repository and runners**

Add `project` to `RunRecord`, INSERT/SELECT statements, and `list_runs`. SOM uses `"SOM"`; eDCT uses `"eDCT"`. Failed eDCT load/analysis attempts are inserted with `status="failed"` and their error message. Export remains a later optional update to `exported_file`.

- [ ] **Step 5: Run history tests**

Run:

```powershell
Push-Location som_analyzer
uv run pytest tests/test_validation_rules.py tests/test_edct_analysis.py -q
Pop-Location
```

Expected: migration, project filtering, successful runs, and failed attempts pass.

- [ ] **Step 6: Commit history separation**

```powershell
git add som_analyzer/src/som_analyzer/db som_analyzer/src/som_analyzer/analysis/runner.py som_analyzer/src/som_analyzer/analysis/edct.py som_analyzer/tests
git commit -m "feat: separate checker history by project"
```

---

### Task 4: Add project selection and the eDCT screen

**Files:**
- Modify: `som_analyzer/src/som_analyzer/gui/app.py`
- Modify: `som_analyzer/src/som_analyzer/gui/screens.py`
- Create: `som_analyzer/tests/test_gui_projects.py`

**Interfaces:**
- Produces: `ProjectSelectionPage`.
- Produces: `EdctPage`.
- Produces: `EdctAnalysisWorker`.
- Changes: `SomAnalyzeController.history_runs(project: str)`.
- Adds: `SomAnalyzeController.run_edct(input_file: str) -> EdctRunResult`.
- Adds: `SomAnalyzeController.export_edct(result: EdctRunResult, output_dir: str) -> Path`.

- [ ] **Step 1: Write failing project-navigation tests**

With `QT_QPA_PLATFORM=offscreen`, instantiate `MainWindow` and assert:

- The initial page presents `SOM Quality Checker` and `eDCT Quality Checker`.
- Choosing eDCT shows its input/output/run controls.
- Back returns to project selection.
- eDCT has no SOM filter widgets.

- [ ] **Step 2: Run GUI tests and verify failure**

Run:

```powershell
Push-Location som_analyzer
$env:QT_QPA_PLATFORM = "offscreen"
uv run pytest tests/test_gui_projects.py -q
Pop-Location
```

Expected: failure because the project-selection and eDCT widgets do not exist.

- [ ] **Step 3: Add project navigation with existing Qt widgets**

Use the existing `QStackedWidget`, `QPushButton`, and card styles. Initial page contains two accessible buttons. SOM opens the existing pages unchanged. eDCT opens its own page and history. Add a visible `Back to projects` button to each project shell.

- [ ] **Step 4: Add the eDCT worker and screen**

Follow the existing `AnalysisWorker + QThread` pattern. The worker calls `run_edct_analysis` and `export_edct_result`, emits result/path/error, and never performs workbook work on the UI thread.

The eDCT screen contains only:

- Input workbook picker.
- Output folder picker.
- Run button and busy state.
- Status and exported path.
- Compact preview with `Index`, `Supplier Punch code`, `Supplier name`, `Check`, `Comment`.
- eDCT-filtered history.
- Back button.

- [ ] **Step 5: Run GUI tests**

Run:

```powershell
Push-Location som_analyzer
$env:QT_QPA_PLATFORM = "offscreen"
uv run pytest tests/test_gui_projects.py -q
Pop-Location
```

Expected: all project-navigation tests pass.

- [ ] **Step 6: Commit the UI**

```powershell
git add som_analyzer/src/som_analyzer/gui som_analyzer/tests/test_gui_projects.py
git commit -m "feat: add som and edct project selection"
```

---

### Task 5: Document the rules and verify the complete application

**Files:**
- Create: `docs/EDCT_VALIDATION_RULES.md`
- Modify: `README.md`
- Modify: `CONTEXT.md`
- Modify: `som_analyzer/tests/test_edct_analysis.py`

**Interfaces:**
- Documents: the authoritative Python rule config and the legacy Excel source.
- Adds no runtime interface.

- [ ] **Step 1: Add a config-to-documentation consistency test**

Parse the Markdown checked-fields table and assert every configured rule target from `edct_config.py` appears. Assert every `EDCT_FORMULA_COLUMNS` entry appears in the formula section. This prevents the executable rules and human documentation from drifting silently.

- [ ] **Step 2: Write `EDCT_VALIDATION_RULES.md`**

Include:

- Runtime source of truth: `som_analyzer/src/som_analyzer/edct_config.py`.
- Legacy source: `materials/edct_vallidation_rules.xlsx.xlsx`, explicitly non-runtime.
- Required sheets, header row, and `Index` row boundary.
- One table with columns: Field, Applies when, Empty allowed, Accepted format/values, Failure behavior.
- Formula-reference behavior and the exact missing-reference message.
- `Open Task` cross-sheet behavior.
- A separate list of every explicitly unchecked field.
- Export and `Check`/`Comment` semantics.

- [ ] **Step 3: Update repository and domain documentation**

Update `README.md` with project selection and eDCT run instructions. Add concise glossary entries to `CONTEXT.md` for:

- **Checker project**: the selected SOM or eDCT validation context.
- **Formula reference row**: the first eDCT row with a populated `Index`, whose formulas define expected structures.

Keep implementation paths and library details out of `CONTEXT.md`.

- [ ] **Step 4: Run documentation consistency and full tests**

Run:

```powershell
Push-Location som_analyzer
$env:QT_QPA_PLATFORM = "offscreen"
uv run pytest tests -q
Pop-Location
```

Expected: all tests pass.

- [ ] **Step 5: Run the real sample smoke check**

Run analysis against `materials/eDCT_input.xlsx` into a temporary output directory. Open the result with `openpyxl` and assert:

- All original worksheet names remain.
- `Supplier Level` has `Check` and `Comment`.
- Rows with `Index` are counted.
- The source workbook timestamp and size are unchanged.

Report the actual assessed and failed row counts; do not prescribe expected counts before the rules run.

- [ ] **Step 6: Run formatting and diff checks**

Run:

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors; only intentional feature files are changed.

- [ ] **Step 7: Commit documentation and final verification**

```powershell
git add README.md CONTEXT.md docs/EDCT_VALIDATION_RULES.md som_analyzer/tests/test_edct_analysis.py
git commit -m "docs: document edct quality rules"
```

---

## Self-Review

- Spec coverage: landing selection, eDCT screen, user-selected paths, exact worksheets, row boundary, executable config, Markdown conversion, every agreed rule category, first-row formula learning, complete-workbook export, table extension, compact preview, and project history each map to a task.
- Simplification: no generic plugin framework or second application; one dedicated config and one dedicated analysis module are enough for the two current checker projects.
- Safety: the source workbook is never overwritten; failed structure validation stops export; failed rule checks still produce an annotated copy.
- Type consistency: GUI consumes `EdctRunResult` from `run_edct_analysis`; export consumes the same result; history consistently uses `project="SOM"` or `project="eDCT"`.
- Documentation consistency: executable field groups are checked against the Markdown catalogue.
