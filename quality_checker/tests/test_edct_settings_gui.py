from __future__ import annotations

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication
from quality_checker.checkers.edct.settings import (
    EdctHeaderSettings,
    load_edct_settings,
    save_edct_settings,
)
from quality_checker.gui.app import QualityCheckerController
from quality_checker.gui.screens import EdctSettingsPage, MainWindow


class TestEdctSettingsGui(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_settings_page_navigation_in_main_window(self) -> None:
        window = MainWindow(QualityCheckerController())
        window.project_page.edct_button.click()
        self.assertEqual(
            [window.edct_menu.item(index).text() for index in range(window.edct_menu.count())],
            ["Analysis", "History", "Settings"],
        )
        # Navigate to Settings
        window.edct_menu.setCurrentRow(2)
        self.assertEqual(window.edct_destination_label.text(), "Settings")
        settings_page = window.edct_pages.currentWidget().widget()
        self.assertIsInstance(settings_page, EdctSettingsPage)

    def test_settings_page_table_population_and_save(self) -> None:
        with TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "test_settings.json"
            page = EdctSettingsPage(settings_path=settings_path)
            self.assertGreater(page.table.rowCount(), 30)

            # Find row for "Supplier Punch code"
            punch_row = -1
            for row in range(page.table.rowCount()):
                if (
                    page.table.item(row, 0).text() == "Supplier Level"
                    and page.table.item(row, 1).text() == "Supplier Punch code"
                ):
                    punch_row = row
                    break
            self.assertNotEqual(punch_row, -1)
            self.assertEqual(page.table.item(punch_row, 2).text(), "Supplier Punch code")

            # Edit the header
            page.table.item(punch_row, 2).setText("Code Fournisseur")
            page.save_button.click()

            self.assertIn("saved", page.status_label.text().lower())
            loaded = load_edct_settings(settings_path)
            self.assertEqual(
                loaded.get_header("Supplier Level", "Supplier Punch code"),
                "Code Fournisseur",
            )

    def test_settings_page_validation_errors(self) -> None:
        with TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "test_settings.json"
            page = EdctSettingsPage(settings_path=settings_path)

            # Set an empty header
            page.table.item(0, 2).setText("   ")
            page.save_button.click()
            self.assertIn("cannot be empty", page.status_label.text().lower())

            # Set duplicate headers on the same sheet
            page.table.item(0, 2).setText("DuplicateHeader")
            page.table.item(1, 2).setText("DuplicateHeader")
            page.save_button.click()
            self.assertIn("duplicate", page.status_label.text().lower())

    def test_settings_page_reset_to_defaults(self) -> None:
        with TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "test_settings.json"
            custom_settings = EdctHeaderSettings.default()
            custom_settings.supplier_level["Supplier Punch code"] = "Custom Punch"
            save_edct_settings(custom_settings, settings_path)

            page = EdctSettingsPage(settings_path=settings_path)
            self.assertEqual(
                page.get_table_mapping()["Supplier Level"]["Supplier Punch code"],
                "Custom Punch",
            )

            # Click Reset to Defaults
            page.reset_button.click()
            self.assertEqual(
                page.get_table_mapping()["Supplier Level"]["Supplier Punch code"],
                "Supplier Punch code",
            )
            self.assertIn("reset", page.status_label.text().lower())

    def test_settings_page_load_from_sample_file(self) -> None:
        from openpyxl import Workbook
        from PyQt6.QtWidgets import QComboBox

        with TemporaryDirectory() as temp_dir:
            sample_path = Path(temp_dir) / "sample_edct.xlsx"
            wb = Workbook()
            ws_sup = wb.active
            ws_sup.title = "Supplier Level"
            ws_sup.append(["meta"])
            ws_sup.append(["Index", "Code Fournisseur", "Supplier name"])

            wb.save(sample_path)
            wb.close()

            settings_path = Path(temp_dir) / "test_settings.json"
            page = EdctSettingsPage(settings_path=settings_path)
            page.apply_sample_workbook_headers(sample_path)

            # Check that row 0 (Index) has a QComboBox
            widget = page.table.cellWidget(0, 2)
            self.assertIsInstance(widget, QComboBox)
            self.assertEqual(widget.currentText(), "Index")

            # Check that row for Supplier Punch code matched "Code Fournisseur" or options contain it
            for row in range(page.table.rowCount()):
                if page.table.item(row, 1).text() == "Supplier Punch code":
                    punch_widget = page.table.cellWidget(row, 2)
                    self.assertIsInstance(punch_widget, QComboBox)
                    self.assertIn(
                        "Code Fournisseur",
                        [punch_widget.itemText(i) for i in range(punch_widget.count())],
                    )
                    # Select "Code Fournisseur"
                    punch_widget.setCurrentText("Code Fournisseur")
                    break

            page.save_button.click()
            self.assertIn("saved", page.status_label.text().lower())
            loaded = load_edct_settings(settings_path)
            self.assertEqual(
                loaded.get_header("Supplier Level", "Supplier Punch code"),
                "Code Fournisseur",
            )


if __name__ == "__main__":
    unittest.main()
