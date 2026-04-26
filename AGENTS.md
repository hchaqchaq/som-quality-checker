# AGENTS.md

## Project Scope
- This repo is a pandas-based SOM Excel quality checker in active notebook-first development.
- Canonical validation behavior is in `som_analyzer.ipynb`; `som_analyze.py` is only a read/print smoke script.
- `main.py` launches the PyQt desktop app for running analysis, previewing results, exporting output, and browsing run history.

## Architecture and Data Flow
- Input workbook is user-selected in the desktop app and passed explicitly to the analyzer.
- Output location is user-selected in the desktop app and passed explicitly to export.
- `normalize(df, WANTED_COLUMNS)` casts selected columns to `str` and strips whitespace before checks.
- Validation runs as boolean fail masks:
  - `fail_EMAIL_COLUMNS` via `EMAIL_REGEX`
  - `fail_COLUMN_LENGTH` via `CHAR_PATTERN_REGEX` (`6 chars + two spaces + 2 chars`)
  - `fail_COLUMN_LENGTH_12` via `check_column_length(... == CHAR_LENGTH)`
  - `fail_CONTACTED` via `check_column_against_allowed_values` with lowercased allowed values
  - `fail_COLUMN_LOCATION` via `is_valid_location` using `_LOCATION_REGEX` signals on `LOCATION_COLUMNS`
- Row score is aggregated into `df_normalized["Check"]` as integer sum of all fail masks.
- Row explanation is aggregated into `df_normalized["Comment"]` using `build_comment_for_row(index)` and joined with `" | "` when multiple conditions fail.
- Current notebook workflow expects `INPUT_FILE` and `OUTPUT_FILE` to be set explicitly before execution.

## Project-Specific Conventions
- Keep validation-driving constants centralized near the top of the notebook:
  - `WANTED_COLUMNS`, `LOCATION_COLUMNS`, `EMAIL_COLUMNS`, `CHAR_LENGTH_COLUMNS`, `CHAR_LENGTH_COLUMN_12`, `CONTACTED_ALLOWED_VALUES`.
- Preserve output columns `Check` and `Comment` whenever adding/changing rules.
- For category checks (for example `Contacted`), normalize with `strip().lower()` before membership tests.
- For location fields, keep validation through `is_valid_location` (regex-signal based), not just non-empty checks.
- New rules should emit both:
  - a boolean fail mask used in `Check` aggregation
  - a human-readable reason appended in `build_comment_for_row`
- Do not add hardcoded workbook or output paths; pass input and output paths explicitly.

## Dependencies and Integrations
- Runtime deps in `pyproject.toml`: `pandas`, `openpyxl`, `PyQt6`; Python `>=3.12`.
- `openpyxl` is required for Excel IO; avoid switching engine unless intentional.
- `uv.lock` indicates `uv` workflow is expected for reproducible environments.

## Developer Workflows
- Install/sync environment: `uv sync`
- Smoke load Excel file: `uv run python som_analyze.py <input.xlsx>`
- Run desktop app: `uv run python main.py`
- Notebook workflow: execute `som_analyzer.ipynb` cells in order; later cells depend on earlier fail masks/constants.

## Guidance for Future Agent Changes
- Follow the existing extension pattern: constant list -> validator function -> fail mask -> add to `Check` -> append reason in `Comment`.
- Keep current behavior stable when refactoring notebook logic into modules (especially `normalize`, regex checks, and comment composition).
- Keep input/output file paths user-driven in app, scripts, and notebook workflow.
