from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

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
        self.assertEqual(window.pages.currentWidget(), window.edct_page)
        self.assertFalse(hasattr(window.edct_page, "plant_filter"))
        self.assertEqual(window.edct_page.run_button.text(), "Run Analysis")
        self.assertEqual(
            window.edct_page.preview_columns,
            ("Index", "Supplier Punch code", "Supplier name", "Check", "Comment"),
        )

        window.edct_page.back_button.click()
        self.assertEqual(window.pages.currentWidget(), window.project_page)
