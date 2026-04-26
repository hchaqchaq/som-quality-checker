# SOM Quality Checker

This repository now includes a modular analyzer package in `som_analyze/`.

## Run the new TUI

```powershell
uv run python main.py
```

## Package-local workflow

```powershell
Push-Location som_analyze
uv sync
uv run som-analyze
Pop-Location
```

## Smoke test for analysis + DB history

```powershell
Push-Location som_analyze
uv run som-analyze-smoke
Pop-Location
```

