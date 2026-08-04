from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QBoxLayout, QLabel, QMessageBox, QScrollArea, QWidget

from som_analyzer.gui.app import SomAnalyzeController
from som_analyzer.gui.screens import MainWindow, ResponsiveColumns
from som_analyzer.gui import styles


class HistoryController(SomAnalyzeController):
    def __init__(self) -> None:
        super().__init__()
        self.deleted: list[int] = []

    def history_runs(self, project: str = "SOM"):
        return [
            {
                "id": 17,
                "started_at": "2026-08-04 10:00:00",
                "duration_s": 1.25,
                "rows_total": 40,
                "rows_in_scope": 32,
                "rows_failed": 6,
                "status": "completed",
                "input_file": "input.xlsx",
                "exported_file": "output.xlsx",
            }
        ]

    def history_columns(self, run_id: int):
        return [{"rule_name": "email", "column_name": "Owner email", "fail_count": 3}]

    def delete_history_run(self, run_id: int) -> None:
        self.deleted.append(run_id)


class ProjectNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_user_can_select_projects_and_return(self) -> None:
        window = MainWindow(SomAnalyzeController())
        self.assertEqual(window.pages.currentWidget(), window.project_page)
        self.assertEqual(window.project_page.som_button.text(), "Open SOM checker")
        self.assertEqual(window.project_page.edct_button.text(), "Open eDCT checker")

        window.project_page.edct_button.click()
        self.assertEqual(window.pages.currentWidget(), window.edct_shell)
        self.assertEqual(
            [window.edct_menu.item(index).text() for index in range(window.edct_menu.count())],
            ["Analysis", "History"],
        )
        self.assertEqual(window.edct_menu.currentRow(), 0)
        self.assertEqual(window.edct_pages.currentWidget().widget(), window.edct_page)
        self.assertFalse(hasattr(window.edct_page, "plant_filter"))
        self.assertEqual(window.edct_page.pick_input_button.text(), "Choose Input File")
        self.assertEqual(window.edct_page.pick_output_button.text(), "Choose Output Folder")
        self.assertEqual(window.edct_page.run_button.text(), "Run Analysis")
        self.assertTrue(window.edct_page.result_path.isReadOnly())
        self.assertEqual(window.edct_page.preview_table.columnCount(), 5)
        self.assertTrue(window.edct_page.loading_bar.isHidden())
        self.assertEqual(
            window.edct_page.preview_columns,
            ("Index", "Supplier Punch code", "Supplier name", "Check", "Comment"),
        )

        window.edct_menu.setCurrentRow(1)
        self.assertEqual(window.edct_pages.currentWidget().widget(), window.edct_history_page)
        window.edct_menu.setCurrentRow(0)
        self.assertEqual(window.edct_pages.currentWidget().widget(), window.edct_page)

        window.edct_back_button.click()
        self.assertEqual(window.pages.currentWidget(), window.project_page)

        window.project_page.edct_button.click()
        self.assertEqual(window.edct_menu.currentRow(), 0)

    def test_theme_uses_operational_palette(self) -> None:
        self.assertEqual(getattr(styles, "COLORS", {}).get("accent"), "#0f766e")
        self.assertIn("'Segoe UI'", styles.APP_STYLESHEET)
        self.assertIn("QPushButton:focus", styles.APP_STYLESHEET)
        self.assertIn("QTableWidget::item:selected", styles.APP_STYLESHEET)
        self.assertNotIn("#f0c23b", styles.APP_STYLESHEET.lower())

    def test_project_selection_explains_both_checkers(self) -> None:
        window = MainWindow(SomAnalyzeController())

        self.assertEqual(window.project_page.objectName(), "projectLaunch")
        self.assertEqual(window.project_page.som_button.objectName(), "projectChoice")
        self.assertEqual(window.project_page.edct_button.objectName(), "projectChoice")
        self.assertIn("SOM", window.project_page.som_description.text())
        self.assertIn("eDCT", window.project_page.edct_description.text())
        self.assertEqual(window.project_page.som_recent.text(), "No analysis runs yet")
        self.assertEqual(window.project_page.edct_recent.text(), "No analysis runs yet")

    def test_both_checkers_use_the_shared_workspace_shell(self) -> None:
        window = MainWindow(SomAnalyzeController())
        self.assertTrue(hasattr(window, "som_destination_label"))
        self.assertTrue(hasattr(window, "edct_destination_label"))

        for open_button, shell, menu, pages, destination in (
            (
                window.project_page.som_button,
                window.som_shell,
                window.menu,
                window.som_pages,
                window.som_destination_label,
            ),
            (
                window.project_page.edct_button,
                window.edct_shell,
                window.edct_menu,
                window.edct_pages,
                window.edct_destination_label,
            ),
        ):
            open_button.click()
            self.assertEqual(window.pages.currentWidget(), shell)
            self.assertEqual(
                [menu.item(index).text() for index in range(menu.count())],
                ["Analysis", "History"],
            )
            self.assertEqual(destination.text(), "Analysis")
            menu.setCurrentRow(1)
            self.assertEqual(pages.currentIndex(), 1)
            self.assertEqual(destination.text(), "History")

    def test_switch_checker_returns_to_launch_screen(self) -> None:
        window = MainWindow(SomAnalyzeController())

        window.project_page.som_button.click()
        window.som_back_button.click()
        self.assertEqual(window.pages.currentWidget(), window.project_page)

        window.project_page.edct_button.click()
        window.edct_back_button.click()
        self.assertEqual(window.pages.currentWidget(), window.project_page)

    def test_analysis_requires_input_and_output_before_run(self) -> None:
        window = MainWindow(SomAnalyzeController())

        for page in (window.welcome_page, window.edct_page):
            self.assertFalse(page.run_button.isEnabled())
            page.input_file.setText("C:/input.xlsx")
            self.assertFalse(page.run_button.isEnabled())
            page.output_dir.setText("C:/output")
            self.assertTrue(page.run_button.isEnabled())

    def test_analysis_columns_collapse_at_narrow_width(self) -> None:
        columns = ResponsiveColumns(QWidget(), QWidget())
        self.addCleanup(columns.close)
        columns.show()
        self.app.processEvents()

        columns.resize(760, 500)
        self.app.processEvents()
        self.assertEqual(columns.layout().direction(), QBoxLayout.Direction.TopToBottom)

        columns.resize(1000, 500)
        self.app.processEvents()
        self.assertEqual(columns.layout().direction(), QBoxLayout.Direction.LeftToRight)

    def test_analysis_pages_expose_empty_and_semantic_status_states(self) -> None:
        window = MainWindow(SomAnalyzeController())

        for page in (window.welcome_page, window.edct_page):
            self.assertTrue(hasattr(page, "_set_status"))
            self.assertTrue(hasattr(page, "preview_empty"))
            self.assertEqual(page.status.objectName(), "statusNeutral")
            self.assertIn("after an analysis run", page.preview_empty.text())
            page._set_status("Analysis started", "progress")
            self.assertEqual(page.status.objectName(), "statusProgress")
            page._set_status("Analysis completed", "success")
            self.assertEqual(page.status.objectName(), "statusSuccess")
            page._set_status("Analysis failed", "error")
            self.assertEqual(page.status.objectName(), "statusError")

    def test_history_selection_loads_rule_totals(self) -> None:
        controller = HistoryController()
        window = MainWindow(controller)
        history = window.history_page

        self.assertFalse(hasattr(history, "run_id_input"))
        self.assertFalse(history.delete_button.isEnabled())
        self.assertIn("Select an analysis run", history.columns_status.text())

        history.runs_table.selectRow(0)
        self.app.processEvents()

        self.assertEqual(history._selected_run_id(), 17)
        self.assertTrue(history.delete_button.isEnabled())
        self.assertEqual(history.columns_table.rowCount(), 1)
        self.assertEqual(history.columns_table.item(0, 2).text(), "3")

    def test_history_delete_requires_confirmation(self) -> None:
        controller = HistoryController()
        window = MainWindow(controller)
        history = window.history_page
        history.runs_table.selectRow(0)

        with patch.object(
            QMessageBox,
            "question",
            return_value=QMessageBox.StandardButton.No,
        ):
            history.delete_button.click()
        self.assertEqual(controller.deleted, [])

        with patch.object(
            QMessageBox,
            "question",
            return_value=QMessageBox.StandardButton.Yes,
        ):
            history.delete_button.click()
        self.assertEqual(controller.deleted, [17])

    def test_edct_uses_som_page_presentation(self) -> None:
        window = MainWindow(SomAnalyzeController())

        window.project_page.edct_button.click()

        visible_labels = {label.text() for label in window.edct_shell.findChildren(QLabel)}
        self.assertIn("eDCT Checker", visible_labels)
        self.assertEqual(window.edct_back_button.text(), "Switch checker")
        self.assertTrue(
            all(isinstance(window.edct_pages.widget(index), QScrollArea) for index in range(2))
        )
        self.assertEqual(
            window.edct_page.preview_columns,
            ("Index", "Supplier Punch code", "Supplier name", "Check", "Comment"),
        )
