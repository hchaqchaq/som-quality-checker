from __future__ import annotations

from pathlib import Path
from typing import cast

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...checkers.edct.config import EDCT_COFOR_TEMPLATE_SHEET, EDCT_PN_SHEET
from ...checkers.edct.models import EdctLoadError
from ...checkers.edct.settings import (
    OPEN_TASK_SHEET,
    SUPPLIER_LEVEL_SHEET,
    EdctHeaderSettings,
    inspect_workbook_headers,
    load_edct_settings,
    save_edct_settings,
)
from ...checkers.edct.workbook import load_edct_workbook
from ..app import QualityCheckerController
from ..widgets import ResponsiveColumns, _create_section_card
from ..workers import AnalysisWorker, EdctDisplayResult, _run_edct
from .history import HistoryPage


def _show_file_loaded_popup(parent: QWidget, path: Path | str) -> None:
    popup = QMessageBox(parent)
    popup.setWindowTitle("Workbook loaded")
    popup.setText(f"{Path(path).name} loaded successfully.")
    popup.setIcon(QMessageBox.Icon.Information)
    popup.setStandardButtons(QMessageBox.StandardButton.Ok)
    popup.setStyleSheet(
        """
        QMessageBox { background-color: #f0fdf4; }
        QMessageBox QLabel { color: #166534; font-weight: 600; }
        QMessageBox QPushButton {
            background-color: #15803d;
            color: white;
            border: 0;
            border-radius: 4px;
            min-width: 84px;
            padding: 7px 14px;
        }
        QMessageBox QPushButton:hover { background-color: #166534; }
        """
    )
    popup.exec()


def _edct_structure_error(path: Path | str) -> str | None:
    settings = load_edct_settings()
    try:
        source = load_edct_workbook(path, settings)
    except EdctLoadError as exc:
        return f"Workbook rejected — {exc}"
    except Exception as exc:
        return f"Workbook rejected — unable to read Excel file: {exc}"
    source.close()
    return None


class EdctPage(QWidget):
    status_changed = pyqtSignal(str)
    preview_columns = (
        "Worksheet",
        "Source row",
        "Index",
        "Supplier Punch code / Punch seller",
        "Supplier name",
        "Triplet COFOR",
        "Check",
        "Comment",
    )

    def __init__(self, controller: QualityCheckerController, history_page: HistoryPage) -> None:
        super().__init__()
        self.controller = controller
        self.history_page = history_page
        self._run_thread: QThread | None = None
        self._run_worker: AnalysisWorker | None = None
        self._busy = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        input_card = _create_section_card(
            "Workbook Selection", "Choose the source workbook and export folder."
        )
        input_card_layout = cast(QVBoxLayout, input_card.layout())

        input_card_layout.addWidget(QLabel("Input workbook:"))
        input_row = QHBoxLayout()
        self.input_file = QLineEdit()
        self.input_file.setMinimumWidth(0)
        self.input_file.setReadOnly(True)
        self.input_file.setPlaceholderText("Choose an eDCT input workbook")
        self.pick_input_button = QPushButton("Choose Input File")
        self.pick_input_button.setObjectName("accentButton")
        input_row.addWidget(self.input_file)
        input_row.addWidget(self.pick_input_button)
        input_card_layout.addLayout(input_row)

        input_card_layout.addWidget(QLabel("Output folder:"))
        output_row = QHBoxLayout()
        self.output_dir = QLineEdit()
        self.output_dir.setMinimumWidth(0)
        self.output_dir.setReadOnly(True)
        self.output_dir.setPlaceholderText("Choose an output folder")
        self.pick_output_button = QPushButton("Choose Output Folder")
        self.pick_output_button.setObjectName("accentButton")
        output_row.addWidget(self.output_dir)
        output_row.addWidget(self.pick_output_button)
        input_card_layout.addLayout(output_row)
        analysis_card = _create_section_card(
            "Analysis", "Assess the workbook and export an annotated copy."
        )
        analysis_layout = cast(QVBoxLayout, analysis_card.layout())
        self.run_button = QPushButton("Run Analysis")
        self.run_button.setObjectName("primaryButton")
        analysis_layout.addWidget(self.run_button)
        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)
        self.loading_bar.hide()
        analysis_layout.addWidget(self.loading_bar)
        self.status = QLabel("Choose an input workbook and output folder to begin.")
        self.status.setObjectName("statusNeutral")
        analysis_layout.addWidget(self.status)

        analysis_layout.addWidget(QLabel("Exported workbook:"))
        self.result_path = QLineEdit()
        self.result_path.setReadOnly(True)
        self.result_path.setPlaceholderText("The exported workbook path will appear here")
        analysis_layout.addWidget(self.result_path)

        self.workspace_columns = ResponsiveColumns(input_card, analysis_card)
        layout.addWidget(self.workspace_columns)

        preview_card = _create_section_card(
            "Preview", "First rows from the latest analysis workbook."
        )
        preview_layout = cast(QVBoxLayout, preview_card.layout())
        self.preview_empty = QLabel("Preview rows will appear here after an analysis run.")
        self.preview_empty.setObjectName("emptyState")
        preview_layout.addWidget(self.preview_empty)
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(len(self.preview_columns))
        self.preview_table.setHorizontalHeaderLabels(self.preview_columns)
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        self.preview_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.preview_table.setMinimumHeight(200)
        preview_layout.addWidget(self.preview_table)
        layout.addWidget(preview_card)
        layout.setStretch(1, 1)

        self.pick_input_button.clicked.connect(self._pick_input)
        self.pick_output_button.clicked.connect(self._pick_output)
        self.run_button.clicked.connect(self._run)
        self.input_file.textChanged.connect(self._update_run_enabled)
        self.output_dir.textChanged.connect(self._update_run_enabled)
        self._update_run_enabled()

    def _update_run_enabled(self) -> None:
        ready = bool(self.input_file.text().strip() and self.output_dir.text().strip())
        self.run_button.setEnabled(ready and not self._busy)

    def _set_status(self, text: str, level: str = "neutral") -> None:
        object_names = {
            "neutral": "statusNeutral",
            "progress": "statusProgress",
            "success": "statusSuccess",
            "error": "statusError",
        }
        self.status.setText(text)
        self.status.setObjectName(object_names[level])
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        self.status_changed.emit(text)

    def _set_busy_state(self, busy: bool) -> None:
        self._busy = busy
        self.pick_input_button.setEnabled(not busy)
        self.pick_output_button.setEnabled(not busy)
        self.loading_bar.setVisible(busy)
        self._update_run_enabled()

    def _pick_input(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Choose eDCT input workbook",
            str(Path.home()),
            "Excel files (*.xlsx *.xlsm)",
        )
        if selected:
            error = _edct_structure_error(selected)
            if error:
                self._set_status(error, "error")
                return
            self.input_file.setText(selected)
            self._set_status(f"Workbook loaded successfully: {Path(selected).name}", "success")
            _show_file_loaded_popup(self, selected)

    def _pick_output(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Choose output folder",
            self.output_dir.text().strip() or str(Path.home()),
        )
        if selected:
            self.output_dir.setText(selected)

    def _run(self) -> None:
        if self._run_thread is not None:
            return
        input_path = self.input_file.text().strip()
        output_path = self.output_dir.text().strip()
        if not input_path or not output_path:
            self._set_status("Choose an input workbook and output folder.", "error")
            return
        self._set_busy_state(True)
        self._set_status("Analysis in progress", "progress")
        self._run_thread = QThread(self)
        self._run_worker = AnalysisWorker(lambda: _run_edct(input_path, output_path))
        self._run_worker.moveToThread(self._run_thread)
        self._run_thread.started.connect(self._run_worker.run)
        self._run_worker.finished.connect(self._finished)
        self._run_worker.finished.connect(self._run_thread.quit)
        self._run_worker.finished.connect(self._run_worker.deleteLater)
        self._run_thread.finished.connect(self._run_thread.deleteLater)
        self._run_thread.finished.connect(self._clear_worker)
        self._run_thread.start()

    def _finished(self, result: object, exported_path: str, error: str) -> None:
        self._set_busy_state(False)
        if error or result is None:
            self._set_status(f"Analysis failed: {error or 'unknown error'}", "error")
            return
        run_result = cast(EdctDisplayResult, result)
        self.result_path.setText(exported_path)
        self._set_status(
            f"Run {run_result.run_id} finished | rows: {run_result.rows_total} | "
            f"failed: {run_result.rows_failed}",
            "success",
        )
        self._fill_preview(run_result)
        self.preview_empty.hide()
        self.history_page.refresh_runs()

    def _fill_preview(self, result: EdctDisplayResult) -> None:
        self.preview_table.setRowCount(len(result.preview_rows))
        for display_row, values in enumerate(result.preview_rows):
            for column, value in enumerate(values):
                self.preview_table.setItem(
                    display_row, column, QTableWidgetItem("" if value is None else str(value))
                )
        self.preview_table.resizeColumnsToContents()

    def _clear_worker(self) -> None:
        self._run_worker = None
        self._run_thread = None


class EdctSettingsPage(QWidget):
    status_changed = pyqtSignal(str)

    headers = ("Worksheet", "Default Field", "Configured Excel Header")

    def __init__(
        self,
        settings_path: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.settings_path = settings_path
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        heading = QLabel("eDCT Settings")
        heading.setObjectName("pageTitle")
        description = QLabel(
            "Configure required Excel column header names across worksheets. "
            "Analysis will locate columns using these configured names."
        )
        description.setObjectName("supportingText")
        description.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(description)

        card = _create_section_card(
            "Column Header Mappings",
            "Edit the header names expected in your workbook. Leave blank or duplicate headers will be flagged.",
        )
        card_layout = cast(QVBoxLayout, card.layout())

        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)
        self.load_file_button = QPushButton("Load Headers from File")
        self.load_file_button.setObjectName("accentButton")
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.setObjectName("secondaryButton")
        self.save_button = QPushButton("Save Settings")
        self.save_button.setObjectName("primaryButton")

        actions_row.addWidget(self.load_file_button)
        actions_row.addWidget(self.reset_button)
        actions_row.addStretch(1)
        actions_row.addWidget(self.save_button)
        card_layout.addLayout(actions_row)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.setMinimumHeight(350)
        card_layout.addWidget(self.table)

        self.status_label = QLabel("Settings ready")
        self.status_label.setObjectName("statusNeutral")
        card_layout.addWidget(self.status_label)

        layout.addWidget(card, 1)

        self.save_button.clicked.connect(self._save)
        self.reset_button.clicked.connect(self._reset_to_defaults)
        self.load_file_button.clicked.connect(self._load_from_file)

        self._populate_table(load_edct_settings(self.settings_path))

    def _populate_table(self, settings: EdctHeaderSettings) -> None:
        sheets = (
            (SUPPLIER_LEVEL_SHEET, settings.supplier_level),
            (EDCT_PN_SHEET, settings.pn_level),
            (OPEN_TASK_SHEET, settings.open_task),
            (EDCT_COFOR_TEMPLATE_SHEET, settings.cofor_template),
        )
        total_rows = sum(len(mapping) for _, mapping in sheets)
        self.table.setRowCount(total_rows)

        current_row = 0
        for sheet_name, mapping in sheets:
            for canonical, configured in mapping.items():
                self.table.setCellWidget(current_row, 2, None)

                sheet_item = QTableWidgetItem(sheet_name)
                sheet_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.table.setItem(current_row, 0, sheet_item)

                field_item = QTableWidgetItem(canonical)
                field_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.table.setItem(current_row, 1, field_item)

                config_item = QTableWidgetItem(configured)
                config_item.setFlags(
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                    | Qt.ItemFlag.ItemIsEditable
                )
                self.table.setItem(current_row, 2, config_item)
                current_row += 1

    def _get_row_value(self, row: int) -> str:
        cell_widget = self.table.cellWidget(row, 2)
        if isinstance(cell_widget, QComboBox):
            return cell_widget.currentText().strip()
        item = self.table.item(row, 2)
        return item.text().strip() if item else ""

    @staticmethod
    def _find_best_match(canonical: str, current_val: str, options: list[str]) -> str:
        if canonical in options:
            return canonical
        if current_val in options:
            return current_val
        canonical_cf = canonical.casefold()
        for opt in options:
            if opt.casefold() == canonical_cf:
                return opt
        current_cf = current_val.casefold()
        for opt in options:
            if opt.casefold() == current_cf:
                return opt
        return current_val

    def apply_sample_workbook_headers(self, file_path: Path | str) -> None:
        try:
            detected = inspect_workbook_headers(file_path)
        except Exception as exc:
            self._set_status(f"Failed to inspect headers: {exc}", level="error")
            return

        total_detected = sum(len(headers) for headers in detected.values())
        if total_detected == 0:
            self._set_status("No headers found in the selected workbook.", level="error")
            return

        for row in range(self.table.rowCount()):
            sheet = self.table.item(row, 0).text()
            canonical = self.table.item(row, 1).text()
            current_val = self._get_row_value(row)
            sheet_headers = detected.get(sheet, [])
            if not sheet_headers:
                continue

            best_match = self._find_best_match(canonical, current_val, sheet_headers)
            combo = QComboBox()
            combo.setEditable(True)
            combo.addItems(sheet_headers)
            if best_match and best_match not in sheet_headers:
                combo.addItem(best_match)
            combo.setCurrentText(best_match or current_val)
            self.table.setCellWidget(row, 2, combo)

        self._set_status(
            f"Loaded headers from {Path(file_path).name}. Review dropdowns and click Save Settings.",
            level="success",
        )

    def get_table_mapping(self) -> dict[str, dict[str, str]]:
        result: dict[str, dict[str, str]] = {
            SUPPLIER_LEVEL_SHEET: {},
            EDCT_PN_SHEET: {},
            OPEN_TASK_SHEET: {},
            EDCT_COFOR_TEMPLATE_SHEET: {},
        }
        for row in range(self.table.rowCount()):
            sheet = self.table.item(row, 0).text()
            canonical = self.table.item(row, 1).text()
            configured = self._get_row_value(row)
            if sheet in result:
                result[sheet][canonical] = configured
        return result

    def _save(self) -> None:
        data = self.get_table_mapping()
        settings = EdctHeaderSettings.from_dict(data)
        errors = settings.validate()
        if errors:
            self._set_status(f"Validation failed: {errors[0]}", level="error")
            return
        save_edct_settings(settings, self.settings_path)
        self._set_status("Settings saved successfully.", level="success")

    def _reset_to_defaults(self) -> None:
        defaults = EdctHeaderSettings.default()
        self._populate_table(defaults)
        self._set_status(
            "Headers reset to defaults. Click Save Settings to persist.", level="neutral"
        )

    def _set_status(self, text: str, level: str = "neutral") -> None:
        object_names = {
            "neutral": "statusNeutral",
            "progress": "statusProgress",
            "success": "statusSuccess",
            "error": "statusError",
        }
        self.status_label.setText(text)
        self.status_label.setObjectName(object_names.get(level, "statusNeutral"))
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self.status_label.update()
        self.status_changed.emit(text)

    def _load_from_file(self) -> None:
        selected_file, _ = QFileDialog.getOpenFileName(
            self,
            "Choose sample Excel file",
            str(Path.home()),
            "Excel files (*.xlsx *.xlsm *.xls)",
        )
        if selected_file:
            self.apply_sample_workbook_headers(selected_file)
