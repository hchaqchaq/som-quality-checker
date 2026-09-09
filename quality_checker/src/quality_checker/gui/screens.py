from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from PyQt6.QtCore import QObject, QSize, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QBoxLayout,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLayout,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
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

from ..application import APP_LOGO_PATH, PREVIEW_ROWS
from ..checkers.edct.config import EDCT_HEADER_ROW, EDCT_INDEX_COLUMNS, EDCT_PN_SHEET
from ..checkers.edct.runner import EdctRunResult, export_edct_result, run_edct_analysis
from ..checkers.edct.settings import (
    EDCT_COFOR_TEMPLATE_SHEET,
    OPEN_TASK_SHEET,
    SUPPLIER_LEVEL_SHEET,
    EdctHeaderSettings,
    inspect_workbook_headers,
    load_edct_settings,
    save_edct_settings,
)
from ..checkers.som.config import ScopeFilterDefinition
from ..checkers.som.loader import load_excel
from ..checkers.som.runner import RunResult, export_result, run_analysis
from .app import QualityCheckerController


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
        next_state = (
            Qt.CheckState.Unchecked
            if item.checkState() == Qt.CheckState.Checked
            else Qt.CheckState.Checked
        )
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

        any_checked = any(
            model.item(row).checkState() == Qt.CheckState.Checked
            for row in range(1, model.rowCount())
        )
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


class ResponsiveColumns(QWidget):
    def __init__(
        self,
        left: QWidget,
        right: QWidget,
        breakpoint: int = 900,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.breakpoint = breakpoint
        layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        left.setMinimumWidth(0)
        right.setMinimumWidth(0)
        layout.addWidget(left, 3)
        layout.addWidget(right, 2)

    def minimumSizeHint(self) -> QSize:
        return QSize(0, 0)

    def resizeEvent(self, event) -> None:
        direction = (
            QBoxLayout.Direction.TopToBottom
            if event.size().width() < self.breakpoint
            else QBoxLayout.Direction.LeftToRight
        )
        cast(QBoxLayout, self.layout()).setDirection(direction)
        super().resizeEvent(event)


@dataclass(frozen=True, slots=True)
class EdctDisplayResult:
    run_id: int
    rows_total: int
    rows_failed: int
    preview_rows: tuple[tuple[object, ...], ...]


def _build_edct_display_result(result: EdctRunResult) -> EdctDisplayResult:
    supplier = result.workbook["Supplier Level"]
    headers = {
        str(cell.value).strip(): cell.column
        for cell in supplier[EDCT_HEADER_ROW]
        if cell.value is not None
    }
    index_header = next(column for column in EDCT_INDEX_COLUMNS if column in headers)
    preview_rows: list[tuple[object, ...]] = []
    for sheet_name, workbook_row in result.assessed_rows[:PREVIEW_ROWS]:
        if sheet_name == EDCT_PN_SHEET:
            punch, triplet = result.pn_values[workbook_row]
            index = supplier_name = ""
        else:
            index = supplier.cell(workbook_row, headers[index_header]).value
            punch = supplier.cell(workbook_row, headers["Supplier Punch code"]).value
            supplier_name = supplier.cell(workbook_row, headers["Supplier name"]).value
            triplet = supplier.cell(workbook_row, headers["Triplet COFOR"]).value
        row_result = result.row_results[(sheet_name, workbook_row)]
        preview_rows.append(
            (
                sheet_name,
                workbook_row,
                index,
                punch,
                supplier_name,
                triplet,
                row_result.check,
                row_result.comment,
            )
        )
    return EdctDisplayResult(
        run_id=result.run_id,
        rows_total=len(result.assessed_rows),
        rows_failed=result.rows_failed,
        preview_rows=tuple(preview_rows),
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


def _create_section_card(title: str, hint: str) -> QFrame:
    card = QFrame()
    card.setObjectName("sectionPanel")
    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(14, 14, 14, 14)
    card_layout.setSpacing(8)

    title_label = QLabel(title)
    title_label.setObjectName("sectionTitle")
    hint_label = QLabel(hint)
    hint_label.setObjectName("sectionHint")
    hint_label.setWordWrap(True)
    card_layout.addWidget(title_label)
    card_layout.addWidget(hint_label)
    return card


def _create_sidebar(
    title: str,
    menu_items: tuple[str, ...] = ("Analysis", "History"),
) -> tuple[QFrame, QListWidget, QPushButton]:
    sidebar = QFrame()
    sidebar.setObjectName("sidebarPanel")
    layout = QVBoxLayout(sidebar)
    layout.setContentsMargins(12, 14, 12, 14)
    layout.setSpacing(10)

    if APP_LOGO_PATH.exists():
        logo_frame = QFrame()
        logo_frame.setObjectName("sidebarLogoFrame")
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(10, 10, 10, 10)
        logo_layout.setSpacing(0)
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
        logo_layout.addWidget(logo)
        layout.addWidget(logo_frame)

    title_label = QLabel(title)
    title_label.setObjectName("sidebarTitle")
    title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    layout.addWidget(title_label)

    menu = QListWidget()
    menu.addItems(menu_items)
    menu.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    menu.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    layout.addWidget(menu, 1)

    back_button = QPushButton("Switch checker")
    back_button.setObjectName("quietButton")
    layout.addWidget(back_button)

    content_width = max(
        title_label.sizeHint().width(),
        menu.sizeHintForColumn(0) + 34,
        back_button.sizeHint().width(),
        146,
    )
    menu.setFixedWidth(content_width)
    sidebar.setFixedWidth(
        content_width + layout.contentsMargins().left() + layout.contentsMargins().right()
    )
    return sidebar, menu, back_button


def _wrap_page(page: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setWidget(page)
    return scroll


def _create_workspace_header(checker: str) -> tuple[QFrame, QLabel, QLabel]:
    header = QFrame()
    header.setObjectName("workspaceHeader")
    layout = QHBoxLayout(header)
    layout.setContentsMargins(18, 14, 18, 14)
    layout.setSpacing(10)

    title = QLabel(checker)
    title.setObjectName("workspaceTitle")
    destination = QLabel("Analysis")
    destination.setObjectName("supportingText")
    state = QLabel("Ready")
    state.setObjectName("statusNeutral")

    layout.addWidget(title)
    layout.addWidget(destination)
    layout.addStretch(1)
    layout.addWidget(state)
    return header, destination, state


def _create_checker_shell(
    title: str,
    analysis_page: QWidget,
    history_page: QWidget,
    settings_page: QWidget | None = None,
) -> tuple[QWidget, QListWidget, QStackedWidget, QPushButton, QLabel, QLabel]:
    shell = QWidget()
    shell_layout = QHBoxLayout(shell)
    shell_layout.setContentsMargins(0, 0, 0, 0)
    shell_layout.setSpacing(14)

    menu_items = (
        ("Analysis", "History", "Settings")
        if settings_page is not None
        else ("Analysis", "History")
    )
    sidebar, menu, back_button = _create_sidebar(title, menu_items)
    shell_layout.addWidget(sidebar)

    content = QWidget()
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(0, 0, 0, 0)
    content_layout.setSpacing(12)
    header, destination, state = _create_workspace_header(title)
    content_layout.addWidget(header)

    pages = QStackedWidget()
    pages.setObjectName("pageSurface")
    pages.addWidget(_wrap_page(analysis_page))
    pages.addWidget(_wrap_page(history_page))
    if settings_page is not None:
        pages.addWidget(_wrap_page(settings_page))
    content_layout.addWidget(pages)
    shell_layout.addWidget(content)
    shell_layout.setStretch(0, 0)
    shell_layout.setStretch(1, 1)
    return shell, menu, pages, back_button, destination, state


class ProjectSelectionPage(QWidget):
    def __init__(self, controller: QualityCheckerController) -> None:
        super().__init__()
        self.setObjectName("projectLaunch")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(36)

        identity = QVBoxLayout()
        identity.addStretch(1)
        title = QLabel("Quality Checker")
        title.setObjectName("pageTitle")
        purpose = QLabel("Select a checker to assess workbook quality and review analysis history.")
        purpose.setObjectName("supportingText")
        purpose.setWordWrap(True)
        purpose.setMaximumWidth(380)
        identity.addWidget(title)
        identity.addWidget(purpose)
        identity.addStretch(1)
        layout.addLayout(identity, 2)

        choices = QVBoxLayout()
        choices.setSpacing(16)

        som_panel = QFrame()
        som_panel.setObjectName("projectChoicePanel")
        som_layout = QVBoxLayout(som_panel)
        som_layout.setContentsMargins(22, 22, 22, 22)
        som_layout.setSpacing(10)
        self.som_button = QPushButton("Open SOM checker")
        self.som_button.setObjectName("projectChoice")
        self.som_description = QLabel(
            "SOM analysis applies selected scope filters, reports validation failures, and exports an analysis workbook."
        )
        self.som_description.setObjectName("supportingText")
        self.som_description.setWordWrap(True)
        self.som_recent = QLabel(self._recent_text(controller.history_runs("SOM")))
        self.som_recent.setObjectName("supportingText")
        som_layout.addWidget(self.som_button)
        som_layout.addWidget(self.som_description)
        som_layout.addWidget(self.som_recent)

        edct_panel = QFrame()
        edct_panel.setObjectName("projectChoicePanel")
        edct_layout = QVBoxLayout(edct_panel)
        edct_layout.setContentsMargins(22, 22, 22, 22)
        edct_layout.setSpacing(10)
        self.edct_button = QPushButton("Open eDCT checker")
        self.edct_button.setObjectName("projectChoice")
        self.edct_description = QLabel(
            "eDCT analysis validates Supplier Level and PN Level rows, reports failures, "
            "and exports a preserved workbook copy."
        )
        self.edct_description.setObjectName("supportingText")
        self.edct_description.setWordWrap(True)
        self.edct_recent = QLabel(self._recent_text(controller.history_runs("eDCT")))
        self.edct_recent.setObjectName("supportingText")
        edct_layout.addWidget(self.edct_button)
        edct_layout.addWidget(self.edct_description)
        edct_layout.addWidget(self.edct_recent)

        choices.addStretch(1)
        choices.addWidget(som_panel)
        choices.addWidget(edct_panel)
        choices.addStretch(1)
        layout.addLayout(choices, 3)

    @staticmethod
    def _recent_text(rows) -> str:
        if not rows:
            return "No analysis runs yet"
        return f"Latest run: {rows[0]['started_at']}"


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
        preview_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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


class MainWindow(QMainWindow):
    def __init__(self, controller: QualityCheckerController) -> None:
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

        self.project_page = ProjectSelectionPage(controller)
        self.welcome_page = WelcomePage(controller)
        self.history_page = HistoryPage(controller, "SOM")
        self.edct_history_page = HistoryPage(controller, "eDCT")
        self.edct_settings_page = EdctSettingsPage()
        self.edct_page = EdctPage(controller, self.edct_history_page)
        (
            self.som_shell,
            self.menu,
            self.som_pages,
            self.som_back_button,
            self.som_destination_label,
            self.som_state_label,
        ) = _create_checker_shell("SOM Checker", self.welcome_page, self.history_page)
        (
            self.edct_shell,
            self.edct_menu,
            self.edct_pages,
            self.edct_back_button,
            self.edct_destination_label,
            self.edct_state_label,
        ) = _create_checker_shell(
            "eDCT Checker",
            self.edct_page,
            self.edct_history_page,
            self.edct_settings_page,
        )
        self.welcome_page.status_changed.connect(self.som_state_label.setText)
        self.edct_page.status_changed.connect(self.edct_state_label.setText)
        self.edct_settings_page.status_changed.connect(self.edct_state_label.setText)
        self.pages.addWidget(self.project_page)
        self.pages.addWidget(self.som_shell)
        self.pages.addWidget(self.edct_shell)

        self.menu.currentRowChanged.connect(self._on_menu_changed)
        self.menu.setCurrentRow(0)
        self.project_page.som_button.clicked.connect(self._show_som)
        self.project_page.edct_button.clicked.connect(self._show_edct)
        self.edct_menu.currentRowChanged.connect(self._on_edct_menu_changed)
        self.edct_menu.setCurrentRow(0)
        self.edct_back_button.clicked.connect(
            lambda: self.pages.setCurrentWidget(self.project_page)
        )
        self.som_back_button.clicked.connect(lambda: self.pages.setCurrentWidget(self.project_page))
        self.pages.setCurrentWidget(self.project_page)

    def _on_menu_changed(self, index: int) -> None:
        self.som_pages.setCurrentIndex(index)
        if index >= 0:
            self.som_destination_label.setText(self.menu.item(index).text())
        if index == 1:
            self.history_page.refresh_runs()

    def _show_som(self) -> None:
        self.menu.setCurrentRow(0)
        self.pages.setCurrentWidget(self.som_shell)

    def _show_edct(self) -> None:
        self.edct_menu.setCurrentRow(0)
        self.pages.setCurrentWidget(self.edct_shell)

    def _on_edct_menu_changed(self, index: int) -> None:
        self.edct_pages.setCurrentIndex(index)
        if index >= 0:
            self.edct_destination_label.setText(self.edct_menu.item(index).text())
        if index == 1:
            self.edct_history_page.refresh_runs()


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
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        self.preview_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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
            self._set_status(
                f"Selected input file, but filters could not be loaded: {exc}", level="warning"
            )
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
