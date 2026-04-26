from __future__ import annotations

import sqlite3
from pathlib import Path

from textual.app import App

from ..analysis.runner import RunResult, export_result, run_analysis
from ..config import DB_PATH, DEFAULT_INPUT_FILE, DEFAULT_OUTPUT_FILE
from ..db.repository import delete_run, get_run_columns, initialize_schema, list_runs, open_connection
from .screens import DashboardScreen, HistoryScreen


class SomAnalyzeApp(App[None]):
    TITLE = "SOM Analyze"

    def __init__(self) -> None:
        super().__init__()
        self.connection: sqlite3.Connection | None = None
        self.current_result: RunResult | None = None

    def on_mount(self) -> None:
        self.connection = open_connection(DB_PATH)
        initialize_schema(self.connection)
        self.push_screen(DashboardScreen())

    def on_unmount(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def open_history(self) -> None:
        self.push_screen(HistoryScreen())

    def run_current_analysis(self, input_file: str | None = None) -> RunResult:
        resolved_input = input_file or str(DEFAULT_INPUT_FILE)
        result = run_analysis(resolved_input) if not self.connection else run_analysis(resolved_input, self.connection)
        self.current_result = result
        return result

    def export_current_result(self, output_file: str | None = None) -> Path:
        if self.current_result is None:
            raise RuntimeError("No analysis result to export")
        return export_result(self.current_result, output_file or DEFAULT_OUTPUT_FILE)

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
    SomAnalyzeApp().run()



