from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from ..application import PREVIEW_ROWS
from ..checkers.edct.export import export_edct_result
from ..checkers.edct.models import EdctRunResult
from ..checkers.edct.runner import run_edct_analysis
from ..checkers.som.config import ScopeFilterDefinition
from ..checkers.som.runner import RunResult, export_result, run_analysis


class AnalysisWorker(QObject):
    finished = pyqtSignal(object, str, str)

    def __init__(self, task: Callable[[], tuple[object, Path]]) -> None:
        super().__init__()
        self.task = task

    def run(self) -> None:
        try:
            result, exported_path = self.task()
            self.finished.emit(result, str(exported_path), "")
        except Exception as exc:  # pragma: no cover - worker error path
            self.finished.emit(None, "", str(exc))


@dataclass(frozen=True, slots=True)
class EdctDisplayResult:
    run_id: int
    rows_total: int
    rows_failed: int
    preview_rows: tuple[tuple[object, ...], ...]


def _build_edct_display_result(result: EdctRunResult) -> EdctDisplayResult:
    preview_rows = tuple(
        (
            row.sheet_name,
            row.workbook_row,
            row.index,
            row.punch,
            row.supplier_name,
            row.triplet,
            row.result.check,
            row.result.comment,
        )
        for row in result.assessed_row_details[:PREVIEW_ROWS]
    )
    return EdctDisplayResult(
        run_id=result.run_id,
        rows_total=len(result.assessed_rows),
        rows_failed=result.rows_failed,
        preview_rows=preview_rows,
    )


def _run_edct_in_process(input_path: str, output_path: str) -> tuple[EdctDisplayResult, Path]:
    result = run_edct_analysis(input_path)
    try:
        exported_path = export_edct_result(result, output_path)
        return _build_edct_display_result(result), exported_path
    finally:
        result.workbook.close()


def _run_edct(input_path: str, output_path: str) -> tuple[EdctDisplayResult, Path]:
    with ProcessPoolExecutor(max_workers=1) as executor:
        return executor.submit(_run_edct_in_process, input_path, output_path).result()


def _run_som(
    input_path: str,
    output_path: str,
    scope_filters: tuple[ScopeFilterDefinition, ...],
) -> tuple[RunResult, Path]:
    result = run_analysis(input_path, scope_filters=scope_filters)
    return result, export_result(result, output_path)
