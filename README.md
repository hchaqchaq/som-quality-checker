# Quality Checker

This repository includes one desktop application with separate SOM and eDCT workbook checker modules.

## Run the PyQt app

```powershell
uv run python main.py
```

The app opens with a project selector:

- **SOM Quality Checker** uses the existing SOM rules and workflow.
- **eDCT Quality Checker** validates indexed rows on `Supplier Level`, cross-checks `Open Task`, validates `PN Level` triplets against each assessed supplier's allowed `Triplet COFOR` set, and exports a preserved copy of the complete workbook with annotations on both assessed worksheets.

Both projects require the user to choose an input workbook and output folder. Their run histories are kept separate.

See [eDCT validation rules](docs/EDCT_QUALITY_CHECKER.md) for the complete eDCT rule catalogue.

## Package-local workflow

```powershell
Push-Location quality_checker
uv sync
uv run quality-checker
Pop-Location
```

## Smoke test for analysis + DB history

```powershell
Push-Location quality_checker
uv run quality-checker-smoke "C:\path\to\input.xlsx"
Pop-Location
```
