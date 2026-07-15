# som-analyze

Modular SOM Excel quality checker with:

- object-oriented conditional and cross-row validation rules
- SQLite run history
- PyQt desktop dashboard and history

## Layout

- data/ stores SQLite run history; input and output workbooks are user-selected
- src/som_analyzer/analysis/loader.py validates workbook shape
- src/som_analyzer/analysis/validator.py contains the replacement rule classes
- src/som_analyzer/analysis/runner.py applies optional filters, runs rules, and exports results
- src/som_analyzer/config.py centralizes required columns and optional scope filters
- src/som_analyzer/db/ stores schema and repository helpers
- src/som_analyzer/gui/ contains the PyQt desktop app

## Current validation rules

The active rule set checks:

- completed Status versus Info completed
- conditional Completion date and COFOR format
- Relance freshness from dates in NOTE
- duplicate Shipper and Manufacturer COFOR addresses
- required Quality and Logistic contact emails
- Contacted when Status is filled
- strict DD/MM/YYYY dates in NOTE

All rows are analyzed by default. GUI filters are optional.

## Quick start

Run uv sync, then run uv run som-analyze.

## Smoke test

Run uv run som-analyze-smoke.

## Adding a validation rule

1. Add any new required columns in src/som_analyzer/config.py.
2. Add a focused ValidationRule subclass in src/som_analyzer/analysis/validator.py.
3. Register it in build_default_rules so it returns a boolean fail mask, a human-readable message, and a column fail total.
