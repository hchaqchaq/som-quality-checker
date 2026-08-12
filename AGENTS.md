# AGENTS.md

## Project Scope

- This repo is a pandas/openpyxl Quality Checker with separate SOM and eDCT workbook checker modules.
- Canonical SOM validation behavior is in `som_analyzer.ipynb`; the reusable runtime in
  `quality_checker/src/quality_checker/` powers the GUI and CLI scripts.
- `main.py` launches the PyQt desktop app for selecting a checker, running analysis, previewing results, exporting
  output, and browsing checker-specific run history.
- `quality_checker/` is a separate installable package with `quality-checker` and `quality-checker-smoke` entry points
  defined in `quality_checker/pyproject.toml`.

## Architecture and Data Flow

- Input workbook is user-selected in the desktop app and passed explicitly to the analyzer.
- Output location is user-selected in the desktop app and passed explicitly to export.
- `normalize(df, WANTED_COLUMNS)` casts selected columns to `str` and strips whitespace before checks.
- `quality_checker/src/quality_checker/checkers/som/loader.py` validates SOM workbook existence and required columns
  before any rules run.
- Validation runs as boolean fail masks:
  - `fail_EMAIL_COLUMNS` via `EMAIL_REGEX`
  - `fail_COLUMN_LENGTH` via `CHAR_PATTERN_REGEX` (`6 chars + two spaces + 2 chars`)
  - `fail_COLUMN_LENGTH_12` via `check_column_length(... == CHAR_LENGTH)`
  - `fail_CONTACTED` via `check_column_against_allowed_values` with lowercased allowed values
  - `fail_COLUMN_LOCATION` via `is_valid_location` using `_LOCATION_REGEX` signals on `LOCATION_COLUMNS`
- The SOM runner in `quality_checker/src/quality_checker/checkers/som/runner.py` applies scope filters first, evaluates
  only in-scope rows, aggregates `Check` and `Comment`, and marks out-of-scope rows as `Out of filters`.
- SOM validation is implemented in `quality_checker/src/quality_checker/checkers/som/validator.py` with reusable rules
  for email lists, COFOR pattern, 12-character IDs, allowed `Contacted` values, location regex checks, Excel error-token
  checks, and the `Status`/`Info completed` consistency rule.
- Row score is aggregated into `df_normalized["Check"]` as integer sum of all fail masks.
- Row explanation is aggregated into `df_normalized["Comment"]` using `build_comment_for_row(index)` and joined with
  `" | "` when multiple conditions fail.
- Current notebook workflow expects `INPUT_FILE` and `OUTPUT_FILE` to be set explicitly before execution.
- The SQLite history database lives at `quality_checker/data/quality_checker.db` in development and under
  `%LOCALAPPDATA%\Quality Checker\quality_checker.db` when bundled/frozen.

## Project-Specific Conventions

- Keep validation-driving constants centralized near the top of the notebook:
  - `WANTED_COLUMNS`, `LOCATION_COLUMNS`, `EMAIL_COLUMNS`, `CHAR_LENGTH_COLUMNS`, `CHAR_LENGTH_COLUMN_12`,
    `CONTACTED_ALLOWED_VALUES`.
- Keep SOM rules under `quality_checker/src/quality_checker/checkers/som/`. Keep eDCT workbook targets and rules under
  `quality_checker/src/quality_checker/checkers/edct/`.
- Preserve output columns `Check` and `Comment` whenever adding/changing rules.
- For category checks (for example `Contacted`), normalize with `strip().lower()` before membership tests.
- For location fields, keep validation through `is_valid_location` (regex-signal based), not just non-empty checks.
- When adding a SOM rule, thread it through `checkers/som/config.py` -> `checkers/som/validator.py` ->
  `checkers/som/runner.py`. Keep eDCT rules on the `checkers/edct/config.py` -> `checkers/edct/runner.py` path. Every
  rule must contribute to both `Check` and `Comment` and, when applicable, run-history totals.
- Keep scope filters normalized the same way as the GUI does in `quality_checker/src/quality_checker/gui/screens.py`
  (`Plant`, `Contacted`, and `Info completed` selected from the input workbook).
- New SOM rules should emit both:
  - a boolean fail mask used in `Check` aggregation
  - a human-readable reason appended in `build_comment_for_row`
- New eDCT rules should record one failure entry per failed field or condition; each entry increments `Check`, supplies
  the field name and value for `Comment`, and contributes to run-history totals.
- Do not add hardcoded workbook or output paths; pass input and output paths explicitly.
- Keep the GUI analysis path on a worker thread (`AnalysisWorker` + `QThread`) so workbook loading and export do not
  block the UI.

## Dependencies and Integrations

- Runtime deps in `pyproject.toml` / `quality_checker/pyproject.toml`: `pandas`, `openpyxl`, `PyQt6`; Python
  `>=3.12`.
- `openpyxl` is required for Excel IO and export.
- `uv.lock` indicates `uv` workflow is expected for reproducible environments.
- `quality_checker/pyproject.toml` defines the `quality-checker` GUI entry point and the `quality-checker-smoke` CLI smoke test.

## Developer Workflows

- Install/sync environment: `uv sync`
- Run desktop app: `uv run python main.py`
- Package-local app: `Push-Location quality_checker; uv run quality-checker; Pop-Location`
- Smoke test analysis + DB history:
  `Push-Location quality_checker; uv run quality-checker-smoke "C:\path\to\input.xlsx"; Pop-Location`
- Notebook workflow: execute `som_analyzer.ipynb` cells in order; later cells depend on earlier fail masks/constants.

## Guidance for Future Agent Changes

- Follow the existing extension pattern: constant list -> validator function -> fail mask -> add to `Check` -> append
  reason in `Comment`.
- Keep current behavior stable when refactoring notebook logic into modules (especially `normalize`, regex checks, and
  comment composition).
- Keep input/output file paths user-driven in app, scripts, and notebook workflow.
- If you touch run history, update `quality_checker/src/quality_checker/db/schema.py` and
  `quality_checker/src/quality_checker/db/repository.py` together, including the `exported_file` migration logic.
- If you touch the GUI, preserve the split between `gui/app.py` (controller/app bootstrap) and `gui/screens.py` (
  widgets, workers, and history views).

## Agent skills

### Issue tracker

Issues and specs are tracked as local Markdown under `.scratch/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Triage uses the five default canonical labels. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository using root `CONTEXT.md` and system-wide ADRs under `docs/adr/`. See
`docs/agents/domain.md`.
