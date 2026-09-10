from __future__ import annotations

from typing import cast

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..app import QualityCheckerController
from ..widgets import ResponsiveColumns, _create_section_card


class HistoryPage(QWidget):
    def __init__(
        self,
        controller: QualityCheckerController,
        project: str = "SOM",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.controller = controller
        self.project = project

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        heading = QLabel("Analysis history")
        heading.setObjectName("pageTitle")
        description = QLabel("Select an analysis run to inspect its validation failure totals.")
        description.setObjectName("supportingText")
        description.setWordWrap(True)
        description.setMinimumWidth(0)
        layout.addWidget(heading)
        layout.addWidget(description)

        runs_panel = _create_section_card(
            "Stored runs", "Select one row to inspect its recorded totals."
        )
        runs_layout = cast(QVBoxLayout, runs_panel.layout())
        self.refresh_button = QPushButton("Refresh")
        runs_layout.addWidget(self.refresh_button)
        self.runs_table = QTableWidget()
        self.runs_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.runs_table.setAlternatingRowColors(True)
        self.runs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.runs_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.runs_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.runs_table.setMinimumHeight(260)
        runs_layout.addWidget(self.runs_table)

        details_panel = _create_section_card(
            "Validation failure totals",
            "Rule and column totals for the selected analysis run.",
        )
        details_layout = cast(QVBoxLayout, details_panel.layout())
        self.columns_status = QLabel("Select an analysis run to inspect validation failure totals.")
        self.columns_status.setObjectName("emptyState")
        self.columns_status.setWordWrap(True)
        details_layout.addWidget(self.columns_status)
        self.columns_table = QTableWidget()
        self.columns_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.columns_table.setAlternatingRowColors(True)
        self.columns_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.columns_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.columns_table.setMinimumHeight(220)
        details_layout.addWidget(self.columns_table)
        self.delete_button = QPushButton("Delete analysis run")
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.setEnabled(False)
        details_layout.addWidget(self.delete_button)

        self.workspace_columns = ResponsiveColumns(runs_panel, details_panel)
        layout.addWidget(self.workspace_columns, 1)
        self.history_status = QLabel("History ready")
        self.history_status.setObjectName("statusNeutral")
        layout.addWidget(self.history_status)

        self.refresh_button.clicked.connect(self.refresh_runs)
        self.delete_button.clicked.connect(self._delete_run)
        self.runs_table.itemSelectionChanged.connect(self._load_selected_run)
        self.refresh_runs()

    def _set_cell(self, table: QTableWidget, row: int, column: int, value: object) -> None:
        item = QTableWidgetItem(str(value))
        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        table.setItem(row, column, item)

    def refresh_runs(self) -> None:
        rows = self.controller.history_runs(self.project)
        headers = [
            "id",
            "started_at",
            "duration_s",
            "rows_total",
            "rows_in_scope",
            "rows_failed",
            "status",
            "input_file",
            "exported_file",
        ]
        self.runs_table.clear()
        self.runs_table.setColumnCount(len(headers))
        self.runs_table.setHorizontalHeaderLabels(headers)
        self.runs_table.setRowCount(len(rows))
        for row_index, run in enumerate(rows):
            id_item = QTableWidgetItem(str(run["id"]))
            id_item.setData(Qt.ItemDataRole.UserRole, int(run["id"]))
            self.runs_table.setItem(row_index, 0, id_item)
            self._set_cell(self.runs_table, row_index, 1, run["started_at"])
            self._set_cell(self.runs_table, row_index, 2, f"{float(run['duration_s']):.2f}")
            self._set_cell(self.runs_table, row_index, 3, run["rows_total"])
            self._set_cell(self.runs_table, row_index, 4, run["rows_in_scope"])
            self._set_cell(self.runs_table, row_index, 5, run["rows_failed"])
            self._set_cell(self.runs_table, row_index, 6, run["status"])
            self._set_cell(self.runs_table, row_index, 7, run["input_file"])
            self._set_cell(self.runs_table, row_index, 8, run["exported_file"] or "")
        self.runs_table.resizeColumnsToContents()
        self.runs_table.clearSelection()
        self.runs_table.setCurrentCell(-1, -1)
        self.delete_button.setEnabled(False)
        self.columns_table.setRowCount(0)
        self.columns_status.setText(
            "Select an analysis run to inspect validation failure totals."
            if rows
            else "No analysis runs yet. Completed runs will appear here."
        )
        self.history_status.setText("History refreshed")

    def _selected_run_id(self) -> int | None:
        row = self.runs_table.currentRow()
        if row < 0:
            return None
        item = self.runs_table.item(row, 0)
        return int(item.data(Qt.ItemDataRole.UserRole)) if item is not None else None

    def _fill_columns(self, rows) -> None:
        headers = ["rule_name", "column_name", "fail_count"]
        self.columns_table.clear()
        self.columns_table.setColumnCount(len(headers))
        self.columns_table.setHorizontalHeaderLabels(headers)
        self.columns_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            self._set_cell(self.columns_table, row_index, 0, row["rule_name"])
            self._set_cell(self.columns_table, row_index, 1, row["column_name"])
            self._set_cell(self.columns_table, row_index, 2, row["fail_count"])
        self.columns_table.resizeColumnsToContents()

    def _load_selected_run(self) -> None:
        run_id = self._selected_run_id()
        self.delete_button.setEnabled(run_id is not None)
        if run_id is None:
            self.columns_table.setRowCount(0)
            self.columns_status.setText(
                "Select an analysis run to inspect validation failure totals."
            )
            return
        rows = self.controller.history_columns(run_id)
        self._fill_columns(rows)
        self.columns_status.setText(
            f"Validation failure totals for run {run_id}"
            if rows
            else f"Run {run_id} has no recorded validation failures."
        )

    def _delete_run(self) -> None:
        run_id = self._selected_run_id()
        if run_id is None:
            return
        answer = QMessageBox.question(
            self,
            "Delete analysis run",
            f"Delete analysis run {run_id} from history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.controller.delete_history_run(run_id)
        self.refresh_runs()
        self.history_status.setText(f"Deleted analysis run {run_id}")
