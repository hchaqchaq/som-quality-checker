# AGENTS.md

## Project Scope

- This repo is a pandas-based SOM Excel quality checker in active notebook-first development.
- Canonical validation behavior is in `som_analyzer.ipynb`; the reusable runtime in `som_analyzer/src/som_analyzer/`
  powers the GUI and CLI scripts.
- `main.py` launches the PyQt desktop app for running analysis, previewing results, exporting output, and browsing run
  history.
- `som_analyzer/` is a separate installable package with `som-analyze` and `som-analyze-smoke` entry points defined in
  `som_analyzer/pyproject.toml`.

## Architecture and Data Flow

- Input workbook is user-selected in the desktop app and passed explicitly to the analyzer.
- Output location is user-selected in the desktop app and passed explicitly to export.
- `normalize(df, WANTED_COLUMNS)` casts selected columns to `str` and strips whitespace before checks.
- `som_analyzer/src/som_analyzer/analysis/loader.py` validates workbook existence and required columns before any rules
  run.
- Validation runs as boolean fail masks:
    - `fail_EMAIL_COLUMNS` via `EMAIL_REGEX`
    - `fail_COLUMN_LENGTH` via `CHAR_PATTERN_REGEX` (`6 chars + two spaces + 2 chars`)
    - `fail_COLUMN_LENGTH_12` via `check_column_length(... == CHAR_LENGTH)`
    - `fail_CONTACTED` via `check_column_against_allowed_values` with lowercased allowed values
    - `fail_COLUMN_LOCATION` via `is_valid_location` using `_LOCATION_REGEX` signals on `LOCATION_COLUMNS`
- The package runner in `som_analyzer/src/som_analyzer/analysis/runner.py` applies scope filters first, evaluates only
  in-scope rows, aggregates `Check` and `Comment`, and marks out-of-scope rows as `Out of filters`.
- Validation is now implemented in `som_analyzer/src/som_analyzer/analysis/validator.py` with reusable rules for email
  lists, COFOR pattern, 12-character IDs, allowed `Contacted` values, location regex checks, Excel error-token checks,
  and the `Status`/`Info completed` consistency rule.
- Row score is aggregated into `df_normalized["Check"]` as integer sum of all fail masks.
- Row explanation is aggregated into `df_normalized["Comment"]` using `build_comment_for_row(index)` and joined with
  `" | "` when multiple conditions fail.
- Current notebook workflow expects `INPUT_FILE` and `OUTPUT_FILE` to be set explicitly before execution.
- The SQLite history database lives at `data/som_analyzer.db` in development and under
  `%LOCALAPPDATA%\SOM Quality Checker\som_analyzer.db` when bundled/frozen.

## Project-Specific Conventions

- Keep validation-driving constants centralized near the top of the notebook:
    - `WANTED_COLUMNS`, `LOCATION_COLUMNS`, `EMAIL_COLUMNS`, `CHAR_LENGTH_COLUMNS`, `CHAR_LENGTH_COLUMN_12`,
      `CONTACTED_ALLOWED_VALUES`.
- Keep SOM rules in `som_analyzer/src/som_analyzer/config.py`. Keep the independently configured eDCT workbook
  boundary and rule targets in `som_analyzer/src/som_analyzer/edct_config.py`.
- Preserve output columns `Check` and `Comment` whenever adding/changing rules.
- For category checks (for example `Contacted`), normalize with `strip().lower()` before membership tests.
- For location fields, keep validation through `is_valid_location` (regex-signal based), not just non-empty checks.
- When adding a SOM rule, thread it through `config.py` -> `analysis/validator.py` -> `analysis/runner.py`. Keep eDCT
  rules on the existing `edct_config.py` -> `analysis/edct.py` path. Every rule must contribute to both `Check` and
  `Comment` and, when applicable, run-history totals.
- Keep scope filters normalized the same way as the GUI does in `som_analyzer/src/som_analyzer/gui/screens.py` (`Plant`,
  `Contacted`, and `Info completed` selected from the input workbook).
- New SOM rules should emit both:
    - a boolean fail mask used in `Check` aggregation
    - a human-readable reason appended in `build_comment_for_row`
- New eDCT rules should record one failure entry per failed field or condition; each entry increments `Check`, supplies
  the field name and value for `Comment`, and contributes to run-history totals.
- Do not add hardcoded workbook or output paths; pass input and output paths explicitly.
- Keep the GUI analysis path on a worker thread (`AnalysisWorker` + `QThread`) so workbook loading and export do not
  block the UI.

## Dependencies and Integrations

- Runtime deps in `pyproject.toml` / `som_analyzer/pyproject.toml`: `pandas`, `openpyxl`, `PyQt6`; Python
  `>=3.12`.
- `openpyxl` is required for Excel IO and export.
- `uv.lock` indicates `uv` workflow is expected for reproducible environments.
- `som_analyzer/pyproject.toml` defines the `som-analyze` GUI entry point and the `som-analyze-smoke` CLI smoke test.

## Developer Workflows

- Install/sync environment: `uv sync`
- Run desktop app: `uv run python main.py`
- Package-local app: `Push-Location som_analyzer; uv run som-analyze; Pop-Location`
- Smoke test analysis + DB history:
  `Push-Location som_analyzer; uv run som-analyze-smoke "C:\path\to\input.xlsx"; Pop-Location`
- Notebook workflow: execute `som_analyzer.ipynb` cells in order; later cells depend on earlier fail masks/constants.

## Guidance for Future Agent Changes

- Follow the existing extension pattern: constant list -> validator function -> fail mask -> add to `Check` -> append
  reason in `Comment`.
- Keep current behavior stable when refactoring notebook logic into modules (especially `normalize`, regex checks, and
  comment composition).
- Keep input/output file paths user-driven in app, scripts, and notebook workflow.
- If you touch run history, update `som_analyzer/src/som_analyzer/db/schema.py` and
  `som_analyzer/src/som_analyzer/db/repository.py` together, including the `exported_file` migration logic.
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
