from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from ..analysis.runner import RunResult, export_result, run_analysis
from ..config import DB_PATH
from ..db.repository import delete_run, get_run_columns, initialize_schema, list_runs, open_connection
from .styles import APP_STYLESHEET


class SomAnalyzeController:
    """Application controller that keeps analysis and history operations framework-agnostic."""

    def __init__(self) -> None:
        self.connection: sqlite3.Connection | None = None
        self.current_result: RunResult | None = None

    def startup(self) -> None:
        self.connection = open_connection(DB_PATH)
        if self.connection is None:
            raise RuntimeError("Failed to open database connection")
        initialize_schema(self.connection)

    def shutdown(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def run_current_analysis(self, input_file: str) -> RunResult:
        result = run_analysis(input_file) if not self.connection else run_analysis(input_file, self.connection)
        self.current_result = result
        return result

    def export_current_result(self, output_file: str) -> Path:
        if self.current_result is None:
            raise RuntimeError("No analysis result to export")
        return export_result(self.current_result, output_file)

    def history_runs(self):
        if self.connection is None:
            return []
        return list_runs(self.connection)

    def history_columns(self, run_id: int):
        if self.connection is None:
            return []
        return get_run_columns(self.connection, run_id)

    def delete_history_run(self, run_id: int) -> None:
        if self.connection is None:
            return
        delete_run(self.connection, run_id)


def run_app() -> None:
    from PyQt6.QtWidgets import QApplication

    from .screens import MainWindow

    qt_app = QApplication(sys.argv)
    qt_app.setStyleSheet(APP_STYLESHEET)
    controller = SomAnalyzeController()
    controller.startup()

    main_window = MainWindow(controller)
    main_window.show()

    try:
        qt_app.exec()
    finally:
        controller.shutdown()
