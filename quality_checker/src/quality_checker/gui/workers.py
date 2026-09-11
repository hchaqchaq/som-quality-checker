from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from multiprocessing import Manager
from pathlib import Path
from queue import Empty

from PyQt6.QtCore import QObject, pyqtSignal

from ..application import PREVIEW_ROWS
from ..checkers.edct.export import export_edct_result
from ..checkers.edct.models import EdctRunResult
from ..checkers.edct.runner import run_edct_analysis
from ..checkers.edct.settings import EdctHeaderSettings, inspect_workbook_headers
from ..checkers.edct.workbook import EdctInspectionResult, inspect_edct_workbook
from ..checkers.som.config import ScopeFilterDefinition
from ..checkers.som.runner import RunResult, export_result, run_analysis


class AnalysisWorker(QObject):
    progress = pyqtSignal(str)
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


class InspectionWorker(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(object, str)

    def __init__(self, task: Callable[[], object]) -> None:
        super().__init__()
        self.task = task

    def run(self) -> None:
        try:
            result = self.task()
            self.finished.emit(result, "")
        except Exception as exc:  # pragma: no cover - worker error path
            self.finished.emit(None, str(exc))


def _inspect_edct_in_process(
    input_path: str,
    settings: EdctHeaderSettings,
    progress_queue,
) -> EdctInspectionResult:
    return inspect_edct_workbook(input_path, settings, progress=progress_queue.put)


def _inspect_edct(
    input_path: str,
    settings: EdctHeaderSettings,
    progress: Callable[[str], None] | None = None,
) -> EdctInspectionResult:
    report = progress or (lambda _message: None)
    with Manager() as manager, ProcessPoolExecutor(max_workers=1) as executor:
        progress_queue = manager.Queue()
        future = executor.submit(_inspect_edct_in_process, input_path, settings, progress_queue)
        while not future.done():
            try:
                report(progress_queue.get(timeout=0.1))
            except Empty:
                pass
        while True:
            try:
                report(progress_queue.get_nowait())
            except Empty:
                break
        return future.result()


def _inspect_sample_headers_in_process(input_path: str) -> dict[str, list[str]]:
    try:
        return inspect_workbook_headers(input_path)
    except Exception as exc:
        raise ValueError("Workbook is unreadable or password-protected") from exc


def _inspect_sample_headers(input_path: str) -> dict[str, list[str]]:
    with ProcessPoolExecutor(max_workers=1) as executor:
        return executor.submit(_inspect_sample_headers_in_process, input_path).result()


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


def _run_edct_in_process(
    input_path: str,
    output_path: str,
    progress_queue=None,
    settings: EdctHeaderSettings | None = None,
) -> tuple[EdctDisplayResult, Path]:
    if progress_queue is None:
        result = run_edct_analysis(input_path, settings=settings)
    else:
        result = run_edct_analysis(input_path, settings=settings, progress=progress_queue.put)
    try:
        if progress_queue is None:
            exported_path = export_edct_result(result, output_path)
        else:
            exported_path = export_edct_result(result, output_path, progress=progress_queue.put)
        return _build_edct_display_result(result), exported_path
    finally:
        result.workbook.close()


def _run_edct(
    input_path: str,
    output_path: str,
    progress: Callable[[str], None] | None = None,
    settings: EdctHeaderSettings | None = None,
) -> tuple[EdctDisplayResult, Path]:
    report = progress or (lambda _message: None)
    with Manager() as manager, ProcessPoolExecutor(max_workers=1) as executor:
        progress_queue = manager.Queue()
        future = executor.submit(
            _run_edct_in_process, input_path, output_path, progress_queue, settings
        )
        while not future.done():
            try:
                report(progress_queue.get(timeout=0.1))
            except Empty:
                pass
        while True:
            try:
                report(progress_queue.get_nowait())
            except Empty:
                break
        return future.result()


def _run_som(
    input_path: str,
    output_path: str,
    scope_filters: tuple[ScopeFilterDefinition, ...],
) -> tuple[RunResult, Path]:
    result = run_analysis(input_path, scope_filters=scope_filters)
    return result, export_result(result, output_path)
