from __future__ import annotations

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from ..application import APP_LOGO_PATH
from .app import QualityCheckerController
from .pages.edct import EdctPage, EdctSettingsPage
from .pages.history import HistoryPage
from .pages.project_selection import ProjectSelectionPage
from .pages.som import WelcomePage
from .widgets import _create_checker_shell


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
