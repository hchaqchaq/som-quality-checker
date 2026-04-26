# som-analyze

Modular SOM Excel quality checker with:
- object-oriented validation rules
- SQLite run history
- Textual TUI dashboard + history

## Layout

- `data/` input and output workbooks plus SQLite DB
- `src/som_analyze/analysis/` loader, validator, runner
- `src/som_analyze/db/` schema and repository helpers
- `src/som_analyze/tui/` Textual app and screens

## Quick start

```powershell
uv sync
uv run som-analyze
```

## Smoke test

```powershell
uv run som-analyze-smoke
```

The TUI has a dedicated **Export current result** action to write `data/output.xlsx`.

