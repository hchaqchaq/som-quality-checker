from __future__ import annotations

import sqlite3
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook


class EdctLoadError(Exception):
    """Raised when an eDCT workbook does not contain the required structure."""


@dataclass(frozen=True, slots=True)
class EdctRowResult:
    check: int
    comment: str


@dataclass(frozen=True, slots=True)
class EdctAssessedRow:
    sheet_name: str
    workbook_row: int
    index: object
    punch: object
    supplier_name: object
    triplet: object
    result: EdctRowResult


@dataclass(slots=True)
class EdctRunResult:
    run_id: int
    input_file: Path
    started_at: datetime
    finished_at: datetime
    duration_s: float
    workbook: Workbook
    assessed_rows: tuple[tuple[str, int], ...]
    row_results: dict[tuple[str, int], EdctRowResult]
    rule_totals: Counter[tuple[str, str]]
    uses_default_db: bool
    history_connection: sqlite3.Connection | None
    pn_values: dict[int, tuple[object, object]]
    assessed_row_details: tuple[EdctAssessedRow, ...] = ()
    supplier_headers: dict[str, str] = field(default_factory=dict)

    @property
    def rows_failed(self) -> int:
        return sum(result.check > 0 for result in self.row_results.values())
