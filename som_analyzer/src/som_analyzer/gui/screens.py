from __future__ import annotations

from pathlib import Path
from typing import cast

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..analysis.runner import RunResult, export_result, run_analysis
from ..config import DEFAULT_INPUT_FILE, DEFAULT_OUTPUT_FILE, PREVIEW_ROWS
from .app import SomAnalyzeController


class AnalysisWorker(QObject):
    finished = pyqtSignal(object, str, str)

    def __init__(self, input_path: str, output_path: str) -> None:
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path

    def run(self) -> None:
        try:
            result = run_analysis(self.input_path)
            exported_path = export_result(result, self.output_path)
            self.finished.emit(result, str(exported_path), "")
        except Exception as exc:  # pragma: no cover - worker error path
            self.finished.emit(None, "", str(exc))


class MainWindow(QMainWindow):
    def __init__(self, controller: SomAnalyzeController) -> None:
        super().__init__()
        self.controller = controller
        self.setWindowTitle("SOM Quality Checker")
        self.resize(1180, 760)
        self.setMinimumSize(980, 660)

        root = QWidget(self)
        root.setObjectName("appShell")
        self.setCentralWidget(root)

        layout = QHBoxLayout(root)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        sidebar = QFrame()
        sidebar.setObjectName("sidebarPanel")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 14, 12, 14)
        sidebar_layout.setSpacing(10)

        nav_title = QLabel("SOM Checker")
        nav_title.setObjectName("sectionTitle")
        nav_title.setStyleSheet("color: #ffffff;")
        sidebar_layout.addWidget(nav_title)

        self.menu = QListWidget()
        self.menu.addItem(QListWidgetItem("Welcome"))
        self.menu.addItem(QListWidgetItem("History"))
        self.menu.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sidebar_layout.addWidget(self.menu)
        sidebar_layout.addStretch(1)

        title_width = nav_title.sizeHint().width()
        menu_width = max(self.menu.sizeHintForColumn(0) + 34, 92)
        content_width = max(title_width, menu_width)
        self.menu.setFixedWidth(content_width)
        sidebar.setFixedWidth(content_width + sidebar_layout.contentsMargins().left() + sidebar_layout.contentsMargins().right())
        layout.addWidget(sidebar)

        self.pages = QStackedWidget()
        self.pages.setObjectName("pageSurface")
        self.welcome_page = WelcomePage(controller)
        self.history_page = HistoryPage(controller)
        self.pages.addWidget(self._wrap_page(self.welcome_page))
        self.pages.addWidget(self._wrap_page(self.history_page))
        layout.addWidget(self.pages)
        layout.setStretch(0, 0)
        layout.setStretch(1, 1)

        self.menu.currentRowChanged.connect(self._on_menu_changed)
        self.menu.setCurrentRow(0)

    def _wrap_page(self, page: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(page)
        return scroll

    def _on_menu_changed(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        if index == 1:
            self.history_page.refresh_runs()


class WelcomePage(QWidget):
    def __init__(self, controller: SomAnalyzeController) -> None:
        super().__init__()
        self.controller = controller
        self._run_thread: QThread | None = None
        self._run_worker: AnalysisWorker | None = None
        self.status_level = "info"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        hero_panel = QFrame()
        hero_panel.setObjectName("heroPanel")
        hero_layout = QVBoxLayout(hero_panel)
        hero_layout.setContentsMargins(16, 16, 16, 16)
        hero_layout.setSpacing(4)
        hero_title = QLabel("SOM Quality Review")
        hero_title.setObjectName("pageTitle")
        hero_subtitle = QLabel("Run workbook validation, review flagged rows, and export clean results.")
        hero_subtitle.setObjectName("pageSubtitle")
        hero_layout.addWidget(hero_title)
        hero_layout.addWidget(hero_subtitle)
        layout.addWidget(hero_panel)

        input_card = self._create_section_card("Workbook Selection", "Choose the source workbook and export folder.")
        input_card_layout = cast(QVBoxLayout, input_card.layout())

        input_card_layout.addWidget(QLabel("Input workbook:"))
        input_row = QHBoxLayout()
        self.input_file = QLineEdit("")
        self.input_file.setReadOnly(True)
        self.input_file.setPlaceholderText("Choose an input workbook or use the app default")
        self.pick_input_button = QPushButton("Choose Input File")
        self.pick_input_button.setObjectName("accentButton")
        input_row.addWidget(self.input_file)
        input_row.addWidget(self.pick_input_button)
        input_card_layout.addLayout(input_row)

        input_card_layout.addWidget(QLabel("Output folder:"))
        output_row = QHBoxLayout()
        self.output_dir = QLineEdit("")
        self.output_dir.setReadOnly(True)
        self.output_dir.setPlaceholderText("Choose an output folder or use the app default")
        self.pick_output_button = QPushButton("Choose Output Folder")
        self.pick_output_button.setObjectName("accentButton")
        output_row.addWidget(self.output_dir)
        output_row.addWidget(self.pick_output_button)
        input_card_layout.addLayout(output_row)

        self.run_button = QPushButton("Run Analysis")
        input_card_layout.addWidget(self.run_button)
        layout.addWidget(input_card)

        self.loading_label = QLabel("Analyzing... please wait")
        self.loading_label.setObjectName("sectionHint")
        self.loading_label.hide()
        layout.addWidget(self.loading_label)

        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)
        self.loading_bar.hide()
        layout.addWidget(self.loading_bar)

        self.status = QLabel("Ready")
        self.status.setObjectName("statusInfo")
        layout.addWidget(self.status)

        preview_card = self._create_section_card("Preview", "First five rows from the latest output workbook.")
        preview_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        preview_card_layout = cast(QVBoxLayout, preview_card.layout())
        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        self.preview_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.preview_table.setMinimumHeight(200)
        preview_card_layout.addWidget(self.preview_table)
        layout.addWidget(preview_card)

        result_card = self._create_section_card("Export", "Latest exported workbook path.")
        result_card_layout = cast(QVBoxLayout, result_card.layout())
        result_card_layout.addWidget(QLabel("Result stored at:"))
        self.result_path_value = QLineEdit("")
        self.result_path_value.setReadOnly(True)
        self.result_path_value.setPlaceholderText("The exported workbook path will appear here after a run")
        result_card_layout.addWidget(self.result_path_value)
        layout.addWidget(result_card)
        layout.setStretch(0, 0)
        layout.setStretch(1, 0)
        layout.setStretch(2, 0)
        layout.setStretch(3, 0)
        layout.setStretch(4, 1)
        layout.setStretch(5, 0)

        self.pick_input_button.clicked.connect(self._pick_input_file)
        self.pick_output_button.clicked.connect(self._pick_output_directory)
        self.run_button.clicked.connect(self._on_run)

    def _create_section_card(self, title: str, hint: str) -> QFrame:
        card = QFrame()
        card.setObjectName("sectionCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        hint_label = QLabel(hint)
        hint_label.setObjectName("sectionHint")

        card_layout.addWidget(title_label)
        card_layout.addWidget(hint_label)
        return card

    def _set_status(self, text: str, level: str = "info") -> None:
        self.status_level = level
        self.status.setText(text)
        self.status.setObjectName("statusWarning" if level == "warning" else "statusInfo")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        self.status.update()

    def _pick_input_file(self) -> None:
        selected_file, _ = QFileDialog.getOpenFileName(
            self,
            "Choose input workbook",
            str(Path(self.input_file.text().strip() or DEFAULT_INPUT_FILE).parent),
            "Excel files (*.xlsx *.xls *.xlsm)",
        )
        if selected_file:
            self.input_file.setText(selected_file)
            self._set_status(f"Selected input file: {selected_file}")

    def _pick_output_directory(self) -> None:
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "Choose output folder",
            self.output_dir.text().strip() or str(DEFAULT_OUTPUT_FILE.parent),
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

    def _on_run(self) -> None:
        if self._run_thread is not None:
            return

        input_path = self.input_file.text().strip() or str(DEFAULT_INPUT_FILE)
        output_dir = self.output_dir.text().strip() or str(DEFAULT_OUTPUT_FILE.parent)
        output_path = str(Path(output_dir) / DEFAULT_OUTPUT_FILE.name)

        self.result_path_value.clear()
        self._set_status("Analysis started...")
        self._set_busy_state(True)

        # Run heavy Excel + pandas work off the UI thread to avoid freezing.
        self._run_thread = QThread(self)
        self._run_worker = AnalysisWorker(input_path, output_path)
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
            self._set_status(f"Run failed: {error}", level="warning")
            return

        if result is None:
            self._set_status("Run failed: unknown error", level="warning")
            return

        run_result = cast(RunResult, result)
        self.controller.current_result = run_result
        self._fill_table_from_dataframe(self.preview_table, run_result.final_df)
        in_scope_failed = int((run_result.in_scope_df["Check"] > 0).sum())
        self.result_path_value.setText(exported_path)
        self._set_status(
            f"Run {run_result.run_id} finished in {run_result.duration_s:.2f}s | "
            f"rows: {len(run_result.final_df)} | failed in scope: {in_scope_failed}"
        )

    def _set_busy_state(self, busy: bool) -> None:
        self.run_button.setEnabled(not busy)
        self.pick_input_button.setEnabled(not busy)
        self.pick_output_button.setEnabled(not busy)
        self.loading_label.setVisible(busy)
        self.loading_bar.setVisible(busy)

    def _clear_worker_references(self) -> None:
        self._run_worker = None
        self._run_thread = None


class HistoryPage(QWidget):
    def __init__(self, controller: SomAnalyzeController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        hero_panel = QFrame()
        hero_panel.setObjectName("heroPanel")
        hero_layout = QVBoxLayout(hero_panel)
        hero_layout.setContentsMargins(16, 16, 16, 16)
        hero_layout.setSpacing(4)
        hero_title = QLabel("Run History")
        hero_title.setObjectName("pageTitle")
        hero_subtitle = QLabel("Review previous analyses, inspect rule totals, and remove obsolete runs.")
        hero_subtitle.setObjectName("pageSubtitle")
        hero_layout.addWidget(hero_title)
        hero_layout.addWidget(hero_subtitle)
        layout.addWidget(hero_panel)

        controls_card = QFrame()
        controls_card.setObjectName("sectionCard")
        controls_card_layout = QVBoxLayout(controls_card)
        controls_card_layout.setContentsMargins(14, 14, 14, 14)
        controls_card_layout.setSpacing(10)

        controls_title = QLabel("History Controls")
        controls_title.setObjectName("sectionTitle")
        controls_hint = QLabel("Refresh the history, delete a run, or load column totals for a specific run id.")
        controls_hint.setObjectName("sectionHint")
        controls_card_layout.addWidget(controls_title)
        controls_card_layout.addWidget(controls_hint)

        top_buttons = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("accentButton")
        top_buttons.addWidget(self.refresh_button)
        top_buttons.addStretch(1)
        controls_card_layout.addLayout(top_buttons)

        controls_card_layout.addWidget(QLabel("Run id:"))
        controls = QGridLayout()
        self.run_id_input = QLineEdit("")
        self.run_id_input.setPlaceholderText("run id")
        self.delete_button = QPushButton("Delete")
        self.delete_button.setObjectName("dangerButton")
        self.columns_button = QPushButton("Load Columns")

        controls.addWidget(self.run_id_input, 0, 0)
        controls.addWidget(self.delete_button, 0, 1)
        controls.addWidget(self.columns_button, 0, 2)
        controls_card_layout.addLayout(controls)

        self.history_status = QLabel("History")
        self.history_status.setObjectName("statusInfo")
        controls_card_layout.addWidget(self.history_status)
        layout.addWidget(controls_card)

        runs_card = QFrame()
        runs_card.setObjectName("sectionCard")
        runs_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        runs_card_layout = QVBoxLayout(runs_card)
        runs_card_layout.setContentsMargins(14, 14, 14, 14)
        runs_card_layout.setSpacing(8)
        runs_title = QLabel("Stored Runs")
        runs_title.setObjectName("sectionTitle")
        runs_card_layout.addWidget(runs_title)
        self.runs_table = QTableWidget()
        self.runs_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.runs_table.setAlternatingRowColors(True)
        self.runs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.runs_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.runs_table.setMinimumHeight(190)
        runs_card_layout.addWidget(self.runs_table)
        layout.addWidget(runs_card)

        columns_card = QFrame()
        columns_card.setObjectName("sectionCard")
        columns_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        columns_card_layout = QVBoxLayout(columns_card)
        columns_card_layout.setContentsMargins(14, 14, 14, 14)
        columns_card_layout.setSpacing(8)
        self.columns_status = QLabel("Rule and column fail totals")
        self.columns_status.setObjectName("sectionTitle")
        columns_card_layout.addWidget(self.columns_status)

        self.columns_table = QTableWidget()
        self.columns_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.columns_table.setAlternatingRowColors(True)
        self.columns_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.columns_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.columns_table.setMinimumHeight(170)
        columns_card_layout.addWidget(self.columns_table)
        layout.addWidget(columns_card)
        layout.setStretch(0, 0)
        layout.setStretch(1, 0)
        layout.setStretch(2, 2)
        layout.setStretch(3, 2)

        self.refresh_button.clicked.connect(self.refresh_runs)
        self.delete_button.clicked.connect(self._delete_run)
        self.columns_button.clicked.connect(self._load_columns)

        self.refresh_runs()

    def _set_cell(self, table: QTableWidget, row: int, column: int, value: object) -> None:
        item = QTableWidgetItem(str(value))
        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        table.setItem(row, column, item)

    def refresh_runs(self) -> None:
        rows = self.controller.history_runs()
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
            self._set_cell(self.runs_table, row_index, 0, run["id"])
            self._set_cell(self.runs_table, row_index, 1, run["started_at"])
            self._set_cell(self.runs_table, row_index, 2, f"{float(run['duration_s']):.2f}")
            self._set_cell(self.runs_table, row_index, 3, run["rows_total"])
            self._set_cell(self.runs_table, row_index, 4, run["rows_in_scope"])
            self._set_cell(self.runs_table, row_index, 5, run["rows_failed"])
            self._set_cell(self.runs_table, row_index, 6, run["status"])
            self._set_cell(self.runs_table, row_index, 7, run["input_file"])
            self._set_cell(self.runs_table, row_index, 8, run["exported_file"] or "")

        self.runs_table.resizeColumnsToContents()
        self.history_status.setText("History refreshed")

    def _selected_run_id(self) -> int | None:
        raw_value = self.run_id_input.text().strip()
        if not raw_value.isdigit():
            self.history_status.setText("Enter a numeric run id")
            return None
        return int(raw_value)

    def _delete_run(self) -> None:
        run_id = self._selected_run_id()
        if run_id is None:
            return
        self.controller.delete_history_run(run_id)
        self.refresh_runs()
        self.history_status.setText(f"Deleted run {run_id}")

    def _load_columns(self) -> None:
        run_id = self._selected_run_id()
        if run_id is None:
            return

        rows = self.controller.history_columns(run_id)
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
        self.columns_status.setText(f"Loaded columns for run {run_id}")
