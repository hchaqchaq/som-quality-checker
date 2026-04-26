# som-analyze

Modular SOM Excel quality checker with:
- object-oriented validation rules
- SQLite run history
- PyQt desktop dashboard + history

## Layout

- `data/` input and output workbooks plus SQLite DB
- `src/som_analyzer/analysis/loader.py` reads and validates workbook shape
- `src/som_analyzer/analysis/validator.py` contains reusable rule classes and predicate helpers
- `src/som_analyzer/analysis/runner.py` applies scope filters, runs rules, and exports results
- `src/som_analyzer/config.py` is the central place for required columns, scope filters, and rule definitions
- `src/som_analyzer/db/` stores schema and repository helpers
- `src/som_analyzer/gui/` contains the PyQt desktop app

## Quick start

```powershell
uv sync
uv run som-analyze
```

## Smoke test

```powershell
uv run som-analyze-smoke
```

## Adding a new validation rule

1. Add any new required columns or shared column groups in `src/som_analyzer/config.py`.
2. If the rule is another regex, length, allowed-value, or location-style check, add a new rule definition to `DEFAULT_RULE_DEFINITIONS`.
3. If the rule needs new logic, add a predicate helper or a dedicated `ValidationRule` subclass in `src/som_analyzer/analysis/validator.py`.

This keeps new column criteria mostly declarative and avoids editing the runner each time.
