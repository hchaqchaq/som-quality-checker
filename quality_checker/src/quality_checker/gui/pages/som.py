from __future__ import annotations

from pathlib import Path
from typing import cast

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...application import PREVIEW_ROWS
from ...checkers.som.config import ScopeFilterDefinition
from ...checkers.som.loader import load_excel
from ...checkers.som.runner import RunResult
from ..app import QualityCheckerController
from ..widgets import CheckableComboBox, ResponsiveColumns, _create_section_card
from ..workers import AnalysisWorker, _run_som
from .edct import _show_file_loaded_popup


class WelcomePage(QWidget):
    status_changed = pyqtSignal(str)

    def __init__(self, controller: QualityCheckerController) -> None:
        super().__init__()
        self.controller = controller
        self._run_thread: QThread | None = None
        self._run_worker: AnalysisWorker | None = None
        self._busy = False
        self.filter_columns = ("Plant", "Contacted", "Info completed")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        input_card = _create_section_card(
            "Workbook Selection", "Choose the source workbook and export folder."
        )
        input_card_layout = cast(QVBoxLayout, input_card.layout())

        input_card_layout.addWidget(QLabel("Input workbook:"))
        input_row = QHBoxLayout()
        self.input_file = QLineEdit("")
        self.input_file.setMinimumWidth(0)
        self.input_file.setReadOnly(True)
        self.input_file.setPlaceholderText("Choose an input workbook")
        self.pick_input_button = QPushButton("Choose Input File")
        self.pick_input_button.setObjectName("accentButton")
        input_row.addWidget(self.input_file)
        input_row.addWidget(self.pick_input_button)
        input_card_layout.addLayout(input_row)

        input_card_layout.addWidget(QLabel("Output folder:"))
        output_row = QHBoxLayout()
        self.output_dir = QLineEdit("")
        self.output_dir.setMinimumWidth(0)
        self.output_dir.setReadOnly(True)
        self.output_dir.setPlaceholderText("Choose an output folder")
        self.pick_output_button = QPushButton("Choose Output Folder")
        self.pick_output_button.setObjectName("accentButton")
        output_row.addWidget(self.output_dir)
        output_row.addWidget(self.pick_output_button)
        input_card_layout.addLayout(output_row)

        filters_card = _create_section_card(
            "Filters",
            "Quality checks run only on rows matching these selected values.",
        )
        filters_layout = cast(QVBoxLayout, filters_card.layout())
        filters_grid = QGridLayout()
        filters_grid.setHorizontalSpacing(12)
        filters_grid.setVerticalSpacing(8)

        self.plant_filter = self._create_filter_combo("Choose a workbook first")
        self.contacted_filter = self._create_filter_combo("Choose a workbook first")
        self.info_completed_filter = self._create_filter_combo("Choose a workbook first")
        self.filter_combos = {
            "Plant": self.plant_filter,
            "Contacted": self.contacted_filter,
            "Info completed": self.info_completed_filter,
        }

        for column_index, (label, combo) in enumerate(
            (
                ("Plant", self.plant_filter),
                ("Contacted", self.contacted_filter),
                ("Info completed", self.info_completed_filter),
            )
        ):
            label_widget = QLabel(label)
            filters_grid.addWidget(label_widget, 0, column_index)
            filters_grid.addWidget(combo, 1, column_index)

        filters_layout.addLayout(filters_grid)

        setup = QWidget()
        setup_layout = QVBoxLayout(setup)
        setup_layout.setContentsMargins(0, 0, 0, 0)
        setup_layout.setSpacing(12)
        setup_layout.addWidget(input_card)
        setup_layout.addWidget(filters_card)

        run_card = _create_section_card(
            "Analysis", "Assess the selected rows and export an analysis workbook."
        )
        run_layout = cast(QVBoxLayout, run_card.layout())
        self.run_button = QPushButton("Run Analysis")
        self.run_button.setObjectName("primaryButton")
        run_layout.addWidget(self.run_button)

        self.loading_label = QLabel("Analysis in progress")
        self.loading_label.setObjectName("sectionHint")
        self.loading_label.hide()
        run_layout.addWidget(self.loading_label)

        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)
        self.loading_bar.hide()
        run_layout.addWidget(self.loading_bar)

        self.status = QLabel("Choose an input workbook and output folder to begin.")
        self.status.setObjectName("statusNeutral")
        run_layout.addWidget(self.status)

        run_layout.addWidget(QLabel("Exported workbook:"))
        self.result_path_value = QLineEdit("")
        self.result_path_value.setReadOnly(True)
        self.result_path_value.setPlaceholderText(
            "The exported workbook path will appear here after a run"
        )
        run_layout.addWidget(self.result_path_value)

        self.workspace_columns = ResponsiveColumns(setup, run_card)
        layout.addWidget(self.workspace_columns)

        preview_card = _create_section_card(
            "Preview", "First five rows from the latest output workbook."
        )
        preview_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        preview_card_layout = cast(QVBoxLayout, preview_card.layout())
        self.preview_empty = QLabel("Preview rows will appear here after an analysis run.")
        self.preview_empty.setObjectName("emptyState")
        preview_card_layout.addWidget(self.preview_empty)
        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setMinimumHeight(200)
        preview_card_layout.addWidget(self.preview_table)
        layout.addWidget(preview_card)
        layout.setStretch(1, 1)

        self.pick_input_button.clicked.connect(self._pick_input_file)
        self.pick_output_button.clicked.connect(self._pick_output_directory)
        self.run_button.clicked.connect(self._on_run)
        self.input_file.textChanged.connect(self._update_run_enabled)
        self.output_dir.textChanged.connect(self._update_run_enabled)
        self._update_run_enabled()

    def _create_filter_combo(self, placeholder: str) -> CheckableComboBox:
        combo = CheckableComboBox(placeholder)
        combo.setMinimumWidth(0)
        combo.setEnabled(False)
        combo.reset(placeholder)
        return combo

    def _update_run_enabled(self) -> None:
        ready = bool(self.input_file.text().strip() and self.output_dir.text().strip())
        self.run_button.setEnabled(ready and not self._busy)

    def _set_status(self, text: str, level: str = "neutral") -> None:
        object_names = {
            "neutral": "statusNeutral",
            "info": "statusNeutral",
            "progress": "statusProgress",
            "success": "statusSuccess",
            "warning": "statusError",
            "error": "statusError",
        }
        self.status.setText(text)
        self.status.setObjectName(object_names[level])
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        self.status.update()
        self.status_changed.emit(text)

    def _pick_input_file(self) -> None:
        selected_file, _ = QFileDialog.getOpenFileName(
            self,
            "Choose input workbook",
            str(
                Path(self.input_file.text().strip()).parent
                if self.input_file.text().strip()
                else Path.home()
            ),
            "Excel files (*.xlsx *.xls *.xlsm)",
        )
        if selected_file:
            try:
                dataframe = load_excel(selected_file)
            except Exception as exc:
                self._reset_filter_values(f"Workbook rejected: {exc}")
                self.input_file.clear()
                self._set_status(f"Workbook rejected — {exc}", level="error")
                return
            self.input_file.setText(selected_file)
            self._set_filter_values(dataframe)
            self._set_status(
                f"Workbook loaded successfully: {Path(selected_file).name} | filters loaded",
                level="success",
            )
            _show_file_loaded_popup(self, selected_file)

    def _pick_output_directory(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "Choose output folder",
            self.output_dir.text().strip() or str(Path.home()),
        )
        if selected_dir:
            self.output_dir.setText(selected_dir)
            self._set_status(f"Selected output folder: {selected_dir}")

    def _fill_table_from_dataframe(self, table: QTableWidget, dataframe) -> None:
        table.clear()
        columns = [str(column) for column in dataframe.columns]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)

        preview = dataframe.head(min(5, PREVIEW_ROWS))
        table.setRowCount(len(preview))

        for row_index, row_values in enumerate(preview.itertuples(index=False)):
            for column_index, value in enumerate(row_values):
                table.setItem(row_index, column_index, QTableWidgetItem(str(value)))

        table.resizeColumnsToContents()

    def _load_filter_values(self, input_path: str) -> None:
        try:
            dataframe = load_excel(input_path)
        except Exception as exc:
            self._reset_filter_values(f"Unable to load filters: {exc}")
            self._set_status(
                f"Selected input file, but filters could not be loaded: {exc}", level="warning"
            )
            return
        self._set_filter_values(dataframe)
        self._set_status(f"Selected input file: {input_path} | filters loaded")

    def _set_filter_values(self, dataframe) -> None:
        for column in self.filter_columns:
            combo = self.filter_combos[column]
            values = self._distinct_column_values(dataframe, column)
            combo.set_values(values)

    def _reset_filter_values(self, message: str) -> None:
        for combo in self.filter_combos.values():
            combo.reset(message)

    def _distinct_column_values(self, dataframe, column: str) -> list[str]:
        if column not in dataframe.columns:
            return []
        values = dataframe[column].dropna().astype("string").str.strip()
        values = values[values.ne("")]
        return sorted(values.unique().tolist(), key=str.lower)

    def _selected_scope_filters(self) -> tuple[ScopeFilterDefinition, ...]:
        filters: list[ScopeFilterDefinition] = []
        for column in self.filter_columns:
            selected_values = self.filter_combos[column].checked_values()
            if not selected_values:
                continue
            filters.append(
                ScopeFilterDefinition(
                    column=column,
                    allowed_values=tuple(selected_values),
                    casefold=column == "Contacted",
                )
            )
        return tuple(filters)

    def _on_run(self) -> None:
        if self._run_thread is not None:
            return

        input_path = self.input_file.text().strip()
        output_path = self.output_dir.text().strip()
        if not input_path:
            self._set_status("Choose an input workbook before running analysis.", level="warning")
            return
        if not output_path:
            self._set_status("Choose an output folder before running analysis.", level="warning")
            return

        self.result_path_value.clear()
        self._set_status("Analysis in progress", "progress")
        self._set_busy_state(True)

        # Run heavy Excel + pandas work off the UI thread to avoid freezing.
        self._run_thread = QThread(self)
        scope_filters = self._selected_scope_filters()
        self._run_worker = AnalysisWorker(lambda: _run_som(input_path, output_path, scope_filters))
        self._run_worker.moveToThread(self._run_thread)

        self._run_thread.started.connect(self._run_worker.run)
        self._run_worker.finished.connect(self._on_run_finished)
        self._run_worker.finished.connect(self._run_thread.quit)
        self._run_worker.finished.connect(self._run_worker.deleteLater)
        self._run_thread.finished.connect(self._run_thread.deleteLater)
        self._run_thread.finished.connect(self._clear_worker_references)
        self._run_thread.start()

    def _on_run_finished(self, result: object, exported_path: str, error: str) -> None:
        self._set_busy_state(False)

        if error:
            self._set_status(f"Analysis failed: {error}", level="error")
            return

        if result is None:
            self._set_status("Analysis failed: unknown error", level="error")
            return

        run_result = cast(RunResult, result)
        self._fill_table_from_dataframe(self.preview_table, run_result.final_df)
        self.preview_empty.hide()
        in_scope_failed = int((run_result.in_scope_df["Check"] > 0).sum())
        self.result_path_value.setText(exported_path)
        self._set_status(
            f"Run {run_result.run_id} finished in {run_result.duration_s:.2f}s | "
            f"rows: {len(run_result.final_df)} | failed in scope: {in_scope_failed}",
            "success",
        )

    def _set_busy_state(self, busy: bool) -> None:
        self._busy = busy
        self.pick_input_button.setEnabled(not busy)
        self.pick_output_button.setEnabled(not busy)
        for combo in self.filter_combos.values():
            combo.setEnabled(not busy and combo.has_loaded_values())
        self.loading_label.setVisible(busy)
        self.loading_bar.setVisible(busy)
        self._update_run_enabled()

    def _clear_worker_references(self) -> None:
        self._run_worker = None
        self._run_thread = None
