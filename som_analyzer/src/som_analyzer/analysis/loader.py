from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..config import WANTED_COLUMNS


class LoadError(Exception):
    """Raised when an input workbook cannot be loaded or validated."""


def load_excel(path: Path | str) -> pd.DataFrame:
    file_path = Path(path)
    if not file_path.exists():
        raise LoadError(f"Input file not found: {file_path}")

    try:
        dataframe = pd.read_excel(file_path)
    except Exception as exc:  # pragma: no cover - pass through for UI display
        raise LoadError(f"Unable to read Excel file: {file_path} ({exc})") from exc

    missing_columns = [column for column in WANTED_COLUMNS if column not in dataframe.columns]
    if missing_columns:
        raise LoadError(f"Missing required columns: {', '.join(missing_columns)}")

    return dataframe


