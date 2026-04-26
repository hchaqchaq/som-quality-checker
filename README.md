# SOM Quality Checker

This repository includes a modular analyzer package in `som_analyzer/`.

## Run the PyQt app

```powershell
uv run python main.py
```

The desktop app requires the user to choose an input workbook and an output folder before analysis starts.

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
