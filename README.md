# SOM and eDCT Quality Checker

This repository includes one desktop application with separate SOM and eDCT workbook-quality projects.

## Run the PyQt app

```powershell
uv run python main.py
```

The app opens with a project selector:

- **SOM Quality Checker** uses the existing SOM rules and workflow.
- **eDCT Quality Checker** validates indexed rows on `Supplier Level`, cross-checks `Open Task`, and exports a preserved copy of the complete workbook.

Both projects require the user to choose an input workbook and output folder. Their run histories are kept separate.

See [eDCT validation rules](docs/EDCT_VALIDATION_RULES.md) for the complete eDCT rule catalogue.

## Package-local workflow

```powershell
Push-Location som_analyzer
uv sync
uv run som-analyze
Pop-Location
```

## Smoke test for analysis + DB history

```powershell
Push-Location som_analyzer
uv run som-analyze-smoke "C:\path\to\input.xlsx"
Pop-Location
```
