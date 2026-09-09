from __future__ import annotations

import sqlite3
import sys
from multiprocessing import freeze_support

from ..application import APP_LOGO_PATH, DB_PATH
from ..db.repository import (
    delete_run,
    get_run_columns,
    initialize_schema,
    list_runs,
    open_connection,
)
from .styles import APP_STYLESHEET


class QualityCheckerController:
    """Application controller that keeps analysis and history operations framework-agnostic."""

    def __init__(self) -> None:
        self.connection: sqlite3.Connection | None = None

    def startup(self) -> None:
        self.connection = open_connection(DB_PATH)
        if self.connection is None:
            raise RuntimeError("Failed to open database connection")
        initialize_schema(self.connection)

    def shutdown(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def history_runs(self, project: str = "SOM"):
        if self.connection is None:
            return []
        return list_runs(self.connection, project)

    def history_columns(self, run_id: int):
        if self.connection is None:
            return []
        return get_run_columns(self.connection, run_id)

    def delete_history_run(self, run_id: int) -> None:
        if self.connection is None:
            return
        delete_run(self.connection, run_id)


def run_app() -> None:
    freeze_support()
    from PyQt6.QtGui import QIcon
    from PyQt6.QtWidgets import QApplication

    from .screens import MainWindow

    qt_app = QApplication(sys.argv)
    if APP_LOGO_PATH.exists():
        qt_app.setWindowIcon(QIcon(str(APP_LOGO_PATH)))
    qt_app.setStyleSheet(APP_STYLESHEET)
    controller = QualityCheckerController()
    controller.startup()

    main_window = MainWindow(controller)
    main_window.show()

    try:
        qt_app.exec()
    finally:
        controller.shutdown()
