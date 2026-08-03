from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QLabel, QScrollArea

from som_analyzer.gui.app import SomAnalyzeController
from som_analyzer.gui.screens import MainWindow


class ProjectNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_user_can_select_projects_and_return(self) -> None:
        window = MainWindow(SomAnalyzeController())
        self.assertEqual(window.pages.currentWidget(), window.project_page)
        self.assertEqual(window.project_page.som_button.text(), "SOM Quality Checker")
        self.assertEqual(window.project_page.edct_button.text(), "eDCT Quality Checker")

        window.project_page.edct_button.click()
        self.assertEqual(window.pages.currentWidget(), window.edct_shell)
        self.assertEqual(
            [window.edct_menu.item(index).text() for index in range(window.edct_menu.count())],
            ["Welcome", "History"],
        )
        self.assertEqual(window.edct_menu.currentRow(), 0)
        self.assertEqual(window.edct_pages.currentWidget().widget(), window.edct_page)
        self.assertFalse(hasattr(window.edct_page, "plant_filter"))
        self.assertEqual(window.edct_page.pick_input_button.text(), "Choose Input File")
        self.assertEqual(window.edct_page.pick_output_button.text(), "Choose Output Folder")
        self.assertEqual(window.edct_page.run_button.text(), "Run Analysis")
        self.assertEqual(window.edct_page.status.text(), "Ready")
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

    def test_edct_uses_som_page_presentation(self) -> None:
        window = MainWindow(SomAnalyzeController())

        window.project_page.edct_button.click()

        visible_labels = {label.text() for label in window.edct_shell.findChildren(QLabel)}
        self.assertIn("eDCT Checker", visible_labels)
        self.assertEqual(window.edct_back_button.text(), "Back to projects")
        self.assertTrue(
            all(isinstance(window.edct_pages.widget(index), QScrollArea) for index in range(2))
        )
        self.assertEqual(
            window.edct_page.preview_columns,
            ("Index", "Supplier Punch code", "Supplier name", "Check", "Comment"),
        )
