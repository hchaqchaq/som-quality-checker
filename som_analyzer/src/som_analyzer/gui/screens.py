from __future__ import annotations

from pathlib import Path
from typing import Callable, cast

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QComboBox,
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

from .app import SomAnalyzeController
from ..analysis.edct import EdctRunResult, export_edct_result, run_edct_analysis
from ..analysis.loader import load_excel
from ..analysis.runner import RunResult, export_result, run_analysis
from ..config import APP_LOGO_PATH, PREVIEW_ROWS, ScopeFilterDefinition


class CheckableComboBox(QComboBox):
    def __init__(self, placeholder: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setModel(QStandardItemModel(self))
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText(placeholder)
        self._keep_popup_open = False
        self.view().pressed.connect(self._toggle_item)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def hidePopup(self) -> None:
        if self._keep_popup_open:
            self._keep_popup_open = False
            return
        super().hidePopup()

    def set_values(self, values: list[str]) -> None:
        model = cast(QStandardItemModel, self.model())
        model.clear()
        self._append_item("All", None, checked=True)
        for value in values:
            self._append_item(value, value, checked=False)
        self.setEnabled(True)
        self._update_display_text()

    def reset(self, message: str) -> None:
        model = cast(QStandardItemModel, self.model())
        model.clear()
        self._append_item(message, None, checked=False, checkable=False)
        self.setEnabled(False)
        self.lineEdit().setText(message)

    def checked_values(self) -> list[str]:
        model = cast(QStandardItemModel, self.model())
        selected: list[str] = []
        for row in range(model.rowCount()):
            item = model.item(row)
            if item.data(Qt.ItemDataRole.UserRole) is None:
                continue
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(str(item.data(Qt.ItemDataRole.UserRole)))
        return selected

    def has_loaded_values(self) -> bool:
        model = cast(QStandardItemModel, self.model())
        return model.rowCount() > 0 and model.item(0).text() == "All"

    def _append_item(
            self,
            text: str,
            value: str | None,
            checked: bool,
            checkable: bool = True,
    ) -> None:
        item = QStandardItem(text)
        flags = Qt.ItemFlag.ItemIsEnabled
        if checkable:
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        item.setFlags(flags)
        item.setData(value, Qt.ItemDataRole.UserRole)
        item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        cast(QStandardItemModel, self.model()).appendRow(item)

    def _toggle_item(self, index) -> None:
        item = cast(QStandardItemModel, self.model()).itemFromIndex(index)
        if not item or not item.isCheckable():
            return

        self._keep_popup_open = True
        next_state = Qt.CheckState.Unchecked if item.checkState() == Qt.CheckState.Checked else Qt.CheckState.Checked
        item.setCheckState(next_state)
        self._sync_all_item(item)
        self._update_display_text()

    def _sync_all_item(self, changed_item: QStandardItem) -> None:
        model = cast(QStandardItemModel, self.model())
        all_item = model.item(0)
        if changed_item is all_item and changed_item.checkState() == Qt.CheckState.Checked:
            for row in range(1, model.rowCount()):
                model.item(row).setCheckState(Qt.CheckState.Unchecked)
            return

        if changed_item is not all_item and changed_item.checkState() == Qt.CheckState.Checked:
            all_item.setCheckState(Qt.CheckState.Unchecked)
            return

        any_checked = any(model.item(row).checkState() == Qt.CheckState.Checked for row in range(1, model.rowCount()))
        if not any_checked:
            all_item.setCheckState(Qt.CheckState.Checked)

    def _update_display_text(self) -> None:
        values = self.checked_values()
        if not values:
            self.lineEdit().setText("All")
            return
        if len(values) <= 2:
            self.lineEdit().setText(", ".join(values))
            return
        self.lineEdit().setText(f"{len(values)} selected")


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


def _run_edct(input_path: str, output_path: str) -> tuple[EdctRunResult, Path]:
    result = run_edct_analysis(input_path)
    return result, export_edct_result(result, output_path)


def _run_som(
    input_path: str,
    output_path: str,
    scope_filters: tuple[ScopeFilterDefinition, ...],
) -> tuple[RunResult, Path]:
    result = run_analysis(input_path, scope_filters=scope_filters)
    return result, export_result(result, output_path)


def _create_section_card(title: str, hint: str) -> QFrame:
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


class ProjectSelectionPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addStretch(1)
        title = QLabel("Choose a Quality Checker")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        self.som_button = QPushButton("SOM Quality Checker")
        self.som_button.setObjectName("accentButton")
        self.edct_button = QPushButton("eDCT Quality Checker")
        self.edct_button.setObjectName("accentButton")
        layout.addWidget(self.som_button)
        layout.addWidget(self.edct_button)
        layout.addStretch(1)


class EdctPage(QWidget):
    preview_columns = ("Index", "Supplier Punch code", "Supplier name", "Check", "Comment")

    def __init__(self, controller: SomAnalyzeController, history_page: HistoryPage) -> None:
        super().__init__()
        self.controller = controller
        self.history_page = history_page
        self._run_thread: QThread | None = None
        self._run_worker: AnalysisWorker | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        hero_panel = QFrame()
        hero_panel.setObjectName("heroPanel")
        hero_layout = QVBoxLayout(hero_panel)
        hero_layout.setContentsMargins(16, 16, 16, 16)
        hero_layout.setSpacing(4)
        title = QLabel("eDCT Quality Review")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Run workbook validation, review flagged rows, and export clean results.")
        subtitle.setObjectName("pageSubtitle")
        hero_layout.addWidget(title)
        hero_layout.addWidget(subtitle)
        layout.addWidget(hero_panel)

        input_card = _create_section_card("Workbook Selection", "Choose the source workbook and export folder.")
        input_card_layout = cast(QVBoxLayout, input_card.layout())

        input_card_layout.addWidget(QLabel("Input workbook:"))
        input_row = QHBoxLayout()
        self.input_file = QLineEdit()
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
        self.output_dir.setReadOnly(True)
        self.output_dir.setPlaceholderText("Choose an output folder")
        self.pick_output_button = QPushButton("Choose Output Folder")
        self.pick_output_button.setObjectName("accentButton")
        output_row.addWidget(self.output_dir)
        output_row.addWidget(self.pick_output_button)
        input_card_layout.addLayout(output_row)
        layout.addWidget(input_card)

        analysis_card = _create_section_card("Analysis", "Assess the workbook and export an annotated copy.")
        analysis_layout = cast(QVBoxLayout, analysis_card.layout())
        self.run_button = QPushButton("Run Analysis")
        self.run_button.setObjectName("accentButton")
        analysis_layout.addWidget(self.run_button)
        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)
        self.loading_bar.hide()
        analysis_layout.addWidget(self.loading_bar)
        self.status = QLabel("Ready")
        self.status.setObjectName("statusInfo")
        analysis_layout.addWidget(self.status)
        layout.addWidget(analysis_card)

        preview_card = _create_section_card("Preview", "First rows from the latest analysis workbook.")
        preview_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        preview_layout = cast(QVBoxLayout, preview_card.layout())
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

        result_card = _create_section_card("Export", "Latest exported workbook path.")
        result_layout = cast(QVBoxLayout, result_card.layout())
        result_layout.addWidget(QLabel("Result stored at:"))
        self.result_path = QLineEdit()
        self.result_path.setReadOnly(True)
        self.result_path.setPlaceholderText("The exported workbook path will appear here")
        result_layout.addWidget(self.result_path)
        layout.addWidget(result_card)
        layout.setStretch(3, 1)

        self.pick_input_button.clicked.connect(self._pick_input)
        self.pick_output_button.clicked.connect(self._pick_output)
        self.run_button.clicked.connect(self._run)

    def _pick_input(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Choose eDCT input workbook",
            str(Path.home()),
            "Excel files (*.xlsx *.xlsm)",
        )
        if selected:
            self.input_file.setText(selected)

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
            self.status.setText("Choose an input workbook and output folder.")
            return
        self.run_button.setEnabled(False)
        self.loading_bar.show()
        self.status.setText("Analysis started...")
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
        self.run_button.setEnabled(True)
        self.loading_bar.hide()
        if error or result is None:
            self.status.setText(f"Run failed: {error or 'unknown error'}")
            return
        run_result = cast(EdctRunResult, result)
        self.result_path.setText(exported_path)
        self.status.setText(
            f"Run {run_result.run_id} finished | rows: {len(run_result.assessed_rows)} | "
            f"failed: {run_result.rows_failed}"
        )
        self._fill_preview(run_result)
        self.history_page.refresh_runs()

    def _fill_preview(self, result: EdctRunResult) -> None:
        worksheet = result.workbook["Supplier Level"]
        headers = {
            str(cell.value).strip(): cell.column
            for cell in worksheet[2]
            if cell.value is not None
        }
        rows = result.assessed_rows[:PREVIEW_ROWS]
        self.preview_table.setRowCount(len(rows))
        for display_row, workbook_row in enumerate(rows):
            values = (
                worksheet.cell(workbook_row, headers["Index"]).value,
                worksheet.cell(workbook_row, headers["Supplier Punch code"]).value,
                worksheet.cell(workbook_row, headers["Supplier name"]).value,
                result.row_results[workbook_row].check,
                result.row_results[workbook_row].comment,
            )
            for column, value in enumerate(values):
                self.preview_table.setItem(display_row, column, QTableWidgetItem(str(value)))
        self.preview_table.resizeColumnsToContents()

    def _clear_worker(self) -> None:
        self._run_worker = None
        self._run_thread = None


class MainWindow(QMainWindow):
    def __init__(self, controller: SomAnalyzeController) -> None:
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Quality Checker")
        if APP_LOGO_PATH.exists():
            self.setWindowIcon(QIcon(str(APP_LOGO_PATH)))
        self.resize(1180, 760)
        self.setMinimumSize(980, 660)

        root = QWidget(self)
        root.setObjectName("appShell")
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(16, 16, 16, 16)
        self.pages = QStackedWidget()
        layout.addWidget(self.pages)

        self.project_page = ProjectSelectionPage()
        self.som_shell = QWidget()
        self.edct_shell = QWidget()
        self.edct_history_page = HistoryPage(controller, "eDCT")
        self.edct_page = EdctPage(controller, self.edct_history_page)
        self.pages.addWidget(self.project_page)
        self.pages.addWidget(self.som_shell)
        self.pages.addWidget(self.edct_shell)

        som_layout = QHBoxLayout(self.som_shell)
        som_layout.setContentsMargins(0, 0, 0, 0)
        som_layout.setSpacing(14)

        sidebar = QFrame()
        sidebar.setObjectName("sidebarPanel")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 14, 12, 14)
        sidebar_layout.setSpacing(10)

        if APP_LOGO_PATH.exists():
            logo_frame = QFrame()
            logo_frame.setObjectName("sidebarLogoFrame")
            logo_frame_layout = QVBoxLayout(logo_frame)
            logo_frame_layout.setContentsMargins(10, 10, 10, 10)
            logo_frame_layout.setSpacing(0)

            logo = QLabel()
            logo.setObjectName("sidebarLogo")
            logo.setPixmap(
                QPixmap(str(APP_LOGO_PATH)).scaled(
                    126,
                    126,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            logo.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            logo_frame_layout.addWidget(logo)
            sidebar_layout.addWidget(logo_frame)

        nav_title = QLabel("SOM Checker")
        nav_title.setObjectName("sectionTitle")
        nav_title.setStyleSheet("color: #ffffff;")
        nav_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        sidebar_layout.addWidget(nav_title)

        self.menu = QListWidget()
        self.menu.addItem(QListWidgetItem("Welcome"))
        self.menu.addItem(QListWidgetItem("History"))
        self.menu.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sidebar_layout.addWidget(self.menu)
        self.som_back_button = QPushButton("Back to projects")
        sidebar_layout.addWidget(self.som_back_button)
        sidebar_layout.addStretch(1)

        title_width = nav_title.sizeHint().width()
        menu_width = max(self.menu.sizeHintForColumn(0) + 34, 92)
        content_width = max(title_width, menu_width, 142)
        self.menu.setFixedWidth(content_width)
        sidebar.setFixedWidth(
            content_width + sidebar_layout.contentsMargins().left() + sidebar_layout.contentsMargins().right())
        som_layout.addWidget(sidebar)

        self.som_pages = QStackedWidget()
        self.som_pages.setObjectName("pageSurface")
        self.welcome_page = WelcomePage(controller)
        self.history_page = HistoryPage(controller, "SOM")
        self.som_pages.addWidget(self._wrap_page(self.welcome_page))
        self.som_pages.addWidget(self._wrap_page(self.history_page))
        som_layout.addWidget(self.som_pages)
        som_layout.setStretch(0, 0)
        som_layout.setStretch(1, 1)

        edct_layout = QHBoxLayout(self.edct_shell)
        edct_layout.setContentsMargins(0, 0, 0, 0)
        edct_layout.setSpacing(14)

        self.edct_sidebar = QFrame()
        self.edct_sidebar.setObjectName("sidebarPanel")
        edct_sidebar_layout = QVBoxLayout(self.edct_sidebar)
        edct_sidebar_layout.setContentsMargins(12, 14, 12, 14)
        edct_sidebar_layout.setSpacing(10)

        if APP_LOGO_PATH.exists():
            edct_logo_frame = QFrame()
            edct_logo_frame.setObjectName("sidebarLogoFrame")
            edct_logo_layout = QVBoxLayout(edct_logo_frame)
            edct_logo_layout.setContentsMargins(10, 10, 10, 10)
            edct_logo_layout.setSpacing(0)

            edct_logo = QLabel()
            edct_logo.setObjectName("sidebarLogo")
            edct_logo.setPixmap(
                QPixmap(str(APP_LOGO_PATH)).scaled(
                    126,
                    126,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            edct_logo.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            edct_logo_layout.addWidget(edct_logo)
            edct_sidebar_layout.addWidget(edct_logo_frame)

        edct_title = QLabel("eDCT Checker")
        edct_title.setObjectName("sectionTitle")
        edct_title.setStyleSheet("color: #ffffff;")
        edct_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        edct_sidebar_layout.addWidget(edct_title)

        self.edct_menu = QListWidget()
        self.edct_menu.addItem(QListWidgetItem("Welcome"))
        self.edct_menu.addItem(QListWidgetItem("History"))
        self.edct_menu.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        edct_sidebar_layout.addWidget(self.edct_menu)
        self.edct_back_button = QPushButton("Back to projects")
        edct_sidebar_layout.addWidget(self.edct_back_button)
        edct_sidebar_layout.addStretch(1)

        edct_content_width = max(edct_title.sizeHint().width(), self.edct_menu.sizeHintForColumn(0) + 34, 142)
        self.edct_menu.setFixedWidth(edct_content_width)
        self.edct_sidebar.setFixedWidth(
            edct_content_width
            + edct_sidebar_layout.contentsMargins().left()
            + edct_sidebar_layout.contentsMargins().right()
        )
        edct_layout.addWidget(self.edct_sidebar)

        self.edct_pages = QStackedWidget()
        self.edct_pages.setObjectName("pageSurface")
        self.edct_pages.addWidget(self._wrap_page(self.edct_page))
        self.edct_pages.addWidget(self._wrap_page(self.edct_history_page))
        edct_layout.addWidget(self.edct_pages)
        edct_layout.setStretch(0, 0)
        edct_layout.setStretch(1, 1)

        self.menu.currentRowChanged.connect(self._on_menu_changed)
        self.menu.setCurrentRow(0)
        self.project_page.som_button.clicked.connect(lambda: self.pages.setCurrentWidget(self.som_shell))
        self.project_page.edct_button.clicked.connect(self._show_edct)
        self.edct_menu.currentRowChanged.connect(self._on_edct_menu_changed)
        self.edct_menu.setCurrentRow(0)
        self.edct_back_button.clicked.connect(lambda: self.pages.setCurrentWidget(self.project_page))
        self.som_back_button.clicked.connect(lambda: self.pages.setCurrentWidget(self.project_page))
        self.pages.setCurrentWidget(self.project_page)

    def _wrap_page(self, page: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(page)
        return scroll

    def _on_menu_changed(self, index: int) -> None:
        self.som_pages.setCurrentIndex(index)
        if index == 1:
            self.history_page.refresh_runs()

    def _show_edct(self) -> None:
        self.edct_menu.setCurrentRow(0)
        self.pages.setCurrentWidget(self.edct_shell)

    def _on_edct_menu_changed(self, index: int) -> None:
        self.edct_pages.setCurrentIndex(index)
        if index == 1:
            self.edct_history_page.refresh_runs()


class WelcomePage(QWidget):
    def __init__(self, controller: SomAnalyzeController) -> None:
        super().__init__()
        self.controller = controller
        self._run_thread: QThread | None = None
        self._run_worker: AnalysisWorker | None = None
        self.status_level = "info"
        self.filter_columns = ("Plant", "Contacted", "Info completed")

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

        input_card = _create_section_card("Workbook Selection", "Choose the source workbook and export folder.")
        input_card_layout = cast(QVBoxLayout, input_card.layout())

        input_card_layout.addWidget(QLabel("Input workbook:"))
        input_row = QHBoxLayout()
        self.input_file = QLineEdit("")
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
        self.output_dir.setReadOnly(True)
        self.output_dir.setPlaceholderText("Choose an output folder")
        self.pick_output_button = QPushButton("Choose Output Folder")
        self.pick_output_button.setObjectName("accentButton")
        output_row.addWidget(self.output_dir)
        output_row.addWidget(self.pick_output_button)
        input_card_layout.addLayout(output_row)

        layout.addWidget(input_card)

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
        self.run_button = QPushButton("Run Analysis")
        filters_layout.addWidget(self.run_button)
        layout.addWidget(filters_card)

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

        preview_card = _create_section_card("Preview", "First five rows from the latest output workbook.")
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

        result_card = _create_section_card("Export", "Latest exported workbook path.")
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
        layout.setStretch(4, 0)
        layout.setStretch(5, 1)
        layout.setStretch(6, 0)

        self.pick_input_button.clicked.connect(self._pick_input_file)
        self.pick_output_button.clicked.connect(self._pick_output_directory)
        self.run_button.clicked.connect(self._on_run)

    def _create_filter_combo(self, placeholder: str) -> CheckableComboBox:
        combo = CheckableComboBox(placeholder)
        combo.setEnabled(False)
        combo.reset(placeholder)
        return combo

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
            str(Path(self.input_file.text().strip()).parent if self.input_file.text().strip() else Path.home()),
            "Excel files (*.xlsx *.xls *.xlsm)",
        )
        if selected_file:
            self.input_file.setText(selected_file)
            self._load_filter_values(selected_file)

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
            self._set_status(f"Selected input file, but filters could not be loaded: {exc}", level="warning")
            return

        for column in self.filter_columns:
            combo = self.filter_combos[column]
            values = self._distinct_column_values(dataframe, column)
            combo.set_values(values)

        self._set_status(f"Selected input file: {input_path} | filters loaded")

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
        self._set_status("Analysis started...")
        self._set_busy_state(True)

        # Run heavy Excel + pandas work off the UI thread to avoid freezing.
        self._run_thread = QThread(self)
        scope_filters = self._selected_scope_filters()
        self._run_worker = AnalysisWorker(
            lambda: _run_som(input_path, output_path, scope_filters)
        )
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
        for combo in self.filter_combos.values():
            combo.setEnabled(not busy and combo.has_loaded_values())
        self.loading_label.setVisible(busy)
        self.loading_bar.setVisible(busy)

    def _clear_worker_references(self) -> None:
        self._run_worker = None
        self._run_thread = None


class HistoryPage(QWidget):
    def __init__(self, controller: SomAnalyzeController, project: str = "SOM", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.project = project

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
