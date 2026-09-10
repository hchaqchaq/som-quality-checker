from __future__ import annotations

import os
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pandas as pd
from openpyxl import Workbook
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QStandardItemModel
from PyQt6.QtWidgets import QApplication, QBoxLayout, QLabel, QMessageBox, QScrollArea, QWidget
from quality_checker.checkers.edct.runner import EdctRowResult
from quality_checker.gui import app as gui_app
from quality_checker.gui import screens, styles
from quality_checker.gui.app import QualityCheckerController
from quality_checker.gui.screens import (
    AnalysisWorker,
    CheckableComboBox,
    MainWindow,
    ResponsiveColumns,
)


class HistoryController(QualityCheckerController):
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
        window = MainWindow(QualityCheckerController())
        self.assertEqual(window.pages.currentWidget(), window.project_page)
        self.assertEqual(window.project_page.som_button.text(), "Open SOM checker")
        self.assertEqual(window.project_page.edct_button.text(), "Open eDCT checker")

        window.project_page.edct_button.click()
        self.assertEqual(window.pages.currentWidget(), window.edct_shell)
        self.assertEqual(
            [window.edct_menu.item(index).text() for index in range(window.edct_menu.count())],
            ["Analysis", "History", "Settings"],
        )
        self.assertEqual(window.edct_menu.currentRow(), 0)
        self.assertEqual(window.edct_pages.currentWidget().widget(), window.edct_page)
        self.assertFalse(hasattr(window.edct_page, "plant_filter"))
        self.assertEqual(window.edct_page.pick_input_button.text(), "Choose Input File")
        self.assertEqual(window.edct_page.pick_output_button.text(), "Choose Output Folder")
        self.assertEqual(window.edct_page.run_button.text(), "Run Analysis")
        self.assertTrue(window.edct_page.result_path.isReadOnly())
        self.assertTrue(window.edct_page.loading_bar.isHidden())

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
        window = MainWindow(QualityCheckerController())

        self.assertEqual(window.project_page.objectName(), "projectLaunch")
        self.assertEqual(window.project_page.som_button.objectName(), "projectChoice")
        self.assertEqual(window.project_page.edct_button.objectName(), "projectChoice")
        self.assertIn("SOM", window.project_page.som_description.text())
        self.assertIn("eDCT", window.project_page.edct_description.text())
        self.assertEqual(window.project_page.som_recent.text(), "No analysis runs yet")
        self.assertEqual(window.project_page.edct_recent.text(), "No analysis runs yet")

    def test_both_checkers_use_the_shared_workspace_shell(self) -> None:
        window = MainWindow(QualityCheckerController())
        self.assertTrue(hasattr(window, "som_destination_label"))
        self.assertTrue(hasattr(window, "edct_destination_label"))

        for open_button, shell, menu, pages, destination, expected_items in (
            (
                window.project_page.som_button,
                window.som_shell,
                window.menu,
                window.som_pages,
                window.som_destination_label,
                ["Analysis", "History"],
            ),
            (
                window.project_page.edct_button,
                window.edct_shell,
                window.edct_menu,
                window.edct_pages,
                window.edct_destination_label,
                ["Analysis", "History", "Settings"],
            ),
        ):
            open_button.click()
            self.assertEqual(window.pages.currentWidget(), shell)
            self.assertEqual(
                [menu.item(index).text() for index in range(menu.count())],
                expected_items,
            )
            self.assertEqual(destination.text(), "Analysis")
            menu.setCurrentRow(1)
            self.assertEqual(pages.currentIndex(), 1)
            self.assertEqual(destination.text(), "History")

    def test_switch_checker_returns_to_launch_screen(self) -> None:
        window = MainWindow(QualityCheckerController())

        window.project_page.som_button.click()
        window.som_back_button.click()
        self.assertEqual(window.pages.currentWidget(), window.project_page)

        window.project_page.edct_button.click()
        window.edct_back_button.click()
        self.assertEqual(window.pages.currentWidget(), window.project_page)

    def test_analysis_requires_input_and_output_before_run(self) -> None:
        window = MainWindow(QualityCheckerController())

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

    def test_workspace_content_fits_minimum_window_width(self) -> None:
        window = MainWindow(QualityCheckerController())
        self.addCleanup(window.close)
        window.resize(980, 660)
        window.show()
        window.project_page.som_button.click()
        self.app.processEvents()

        analysis_scroll = window.som_pages.currentWidget()
        self.assertLessEqual(
            window.welcome_page.minimumSizeHint().width(),
            analysis_scroll.viewport().width(),
        )
        self.assertEqual(
            window.welcome_page.workspace_columns.layout().direction(),
            QBoxLayout.Direction.TopToBottom,
        )

        window.menu.setCurrentRow(1)
        self.app.processEvents()
        history_scroll = window.som_pages.currentWidget()
        self.assertLessEqual(
            window.history_page.minimumSizeHint().width(),
            history_scroll.viewport().width(),
        )
        self.assertEqual(
            window.history_page.workspace_columns.layout().direction(),
            QBoxLayout.Direction.TopToBottom,
        )

    def test_analysis_pages_expose_empty_and_semantic_status_states(self) -> None:
        window = MainWindow(QualityCheckerController())

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
        window = MainWindow(QualityCheckerController())

        window.project_page.edct_button.click()

        visible_labels = {label.text() for label in window.edct_shell.findChildren(QLabel)}
        self.assertIn("eDCT Checker", visible_labels)
        self.assertEqual(window.edct_back_button.text(), "Switch checker")
        self.assertTrue(
            all(isinstance(window.edct_pages.widget(index), QScrollArea) for index in range(2))
        )

    def test_edct_preview_accepts_line_as_index_header(self) -> None:
        window = MainWindow(QualityCheckerController())
        display_result = screens.EdctDisplayResult(
            run_id=1,
            rows_total=1,
            rows_failed=0,
            preview_rows=(
                (("Supplier Level", 3, 7, "1003", "Supplier", "001-A", 0, "Quality check passed")),
            ),
        )

        window.edct_page._fill_preview(display_result)

        self.assertEqual(window.edct_page.preview_table.item(0, 2).text(), "7")

    def test_checkable_combo_selection_and_reset(self) -> None:
        combo = CheckableComboBox("Choose")
        combo.set_values(["Alpha", "Beta", "Gamma"])
        model = combo.model()
        self.assertIsInstance(model, QStandardItemModel)
        self.assertTrue(combo.has_loaded_values())
        combo._toggle_item(model.index(1, 0))
        self.assertEqual(combo.checked_values(), ["Alpha"])
        self.assertEqual(combo.lineEdit().text(), "Alpha")
        combo._toggle_item(model.index(2, 0))
        combo._toggle_item(model.index(3, 0))
        self.assertEqual(combo.lineEdit().text(), "3 selected")
        combo._toggle_item(model.index(1, 0))
        combo._toggle_item(model.index(2, 0))
        combo._toggle_item(model.index(3, 0))
        self.assertEqual(combo.lineEdit().text(), "All")
        combo._keep_popup_open = True
        combo.hidePopup()
        self.assertFalse(combo._keep_popup_open)
        combo.reset("Unavailable")
        self.assertFalse(combo.isEnabled())
        self.assertFalse(combo.has_loaded_values())
        combo._toggle_item(model.index(-1, -1))
        combo._toggle_item(combo.model().index(0, 0))

        combo.set_values(["Alpha", "Beta"])
        model = combo.model()
        model.item(1).setCheckState(Qt.CheckState.Checked)
        model.item(0).setCheckState(Qt.CheckState.Unchecked)
        combo._toggle_item(model.index(0, 0))
        self.assertEqual(combo.checked_values(), [])

    def test_analysis_worker_emits_success_and_error(self) -> None:
        success: list[tuple[object, str, str]] = []
        worker = AnalysisWorker(lambda: ({"ok": True}, Path("out.xlsx")))
        worker.finished.connect(lambda *values: success.append(values))
        worker.run()
        self.assertEqual(success, [({"ok": True}, "out.xlsx", "")])

        failure: list[tuple[object, str, str]] = []
        worker = AnalysisWorker(lambda: (_ for _ in ()).throw(ValueError("boom")))
        worker.finished.connect(lambda *values: failure.append(values))
        worker.run()
        self.assertEqual(failure, [(None, "", "boom")])

    def test_controller_lifecycle_and_disconnected_defaults(self) -> None:
        controller = QualityCheckerController()
        controller.shutdown()
        self.assertEqual(controller.history_runs(), [])
        self.assertEqual(controller.history_columns(1), [])
        controller.delete_history_run(1)

        with closing(sqlite3.connect(":memory:")) as connection:
            connection.row_factory = sqlite3.Row
            with patch.object(gui_app, "open_connection", return_value=connection):
                controller.startup()
                self.assertEqual(controller.history_runs(), [])
                self.assertEqual(controller.history_columns(1), [])
                controller.delete_history_run(1)
                controller.shutdown()
                self.assertIsNone(controller.connection)

        with patch.object(gui_app, "open_connection", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "Failed to open"):
                QualityCheckerController().startup()

    def test_som_file_filters_and_completion_callbacks(self) -> None:
        window = MainWindow(HistoryController())
        page = window.welcome_page
        frame = pd.DataFrame({"Plant": [" b ", "A", "", None], "Contacted": ["YES"] * 4})
        self.assertEqual(page._distinct_column_values(frame, "Plant"), ["A", "b"])
        self.assertEqual(page._distinct_column_values(frame, "missing"), [])

        with (
            patch(
                "quality_checker.gui.screens.QFileDialog.getOpenFileName",
                return_value=("input.xlsx", ""),
            ),
            patch("quality_checker.gui.screens.load_excel", return_value=frame),
            patch("quality_checker.gui.screens._show_file_loaded_popup") as popup,
        ):
            page._pick_input_file()
        self.assertEqual(page.input_file.text(), "input.xlsx")
        self.assertIn("successfully", page.status.text())
        popup.assert_called_once_with(page, "input.xlsx")
        with patch(
            "quality_checker.gui.screens.QFileDialog.getExistingDirectory", return_value="C:/output"
        ):
            page._pick_output_directory()
        self.assertEqual(page.output_dir.text(), "C:/output")

        with patch("quality_checker.gui.screens.load_excel", return_value=frame):
            page._load_filter_values("input.xlsx")
        page.filter_combos["Plant"]._toggle_item(page.filter_combos["Plant"].model().index(1, 0))
        filters = page._selected_scope_filters()
        self.assertEqual(filters[0].allowed_values, ("A",))
        with patch(
            "quality_checker.gui.screens.load_excel", side_effect=ValueError("bad workbook")
        ):
            page._load_filter_values("bad.xlsx")
        self.assertIn("could not be loaded", page.status.text())

        page._on_run_finished(None, "", "boom")
        self.assertIn("boom", page.status.text())
        page._on_run_finished(None, "", "")
        self.assertIn("unknown error", page.status.text())
        result = SimpleNamespace(
            run_id=3,
            duration_s=0.25,
            final_df=pd.DataFrame({"Check": [0, 1], "Comment": ["ok", "bad"]}),
            in_scope_df=pd.DataFrame({"Check": [0, 1]}),
        )
        page._on_run_finished(result, "result.xlsx", "")
        self.assertEqual(page.result_path_value.text(), "result.xlsx")
        self.assertEqual(page.preview_table.rowCount(), 2)
        page._clear_worker_references()
        self.assertIsNone(page._run_thread)

    def test_history_empty_selection_and_edct_dialog_callbacks(self) -> None:
        window = MainWindow(HistoryController())
        history = window.history_page
        history.runs_table.setCurrentCell(-1, -1)
        history._load_selected_run()
        history._delete_run()
        self.assertIn("Select an analysis run", history.columns_status.text())

        page = window.edct_page
        with (
            patch(
                "quality_checker.gui.screens.QFileDialog.getOpenFileName",
                return_value=("edct.xlsx", ""),
            ),
            patch("quality_checker.gui.screens._edct_structure_error", return_value=None),
            patch("quality_checker.gui.screens._show_file_loaded_popup") as popup,
        ):
            page._pick_input()
        popup.assert_called_once_with(page, "edct.xlsx")
        with patch(
            "quality_checker.gui.screens.QFileDialog.getExistingDirectory", return_value="C:/out"
        ):
            page._pick_output()
        self.assertEqual((page.input_file.text(), page.output_dir.text()), ("edct.xlsx", "C:/out"))
        page._finished(None, "", "boom")
        self.assertIn("boom", page.status.text())
        page._clear_worker()
        self.assertIsNone(page._run_worker)

    def test_analysis_helpers_delegate_and_dialog_cancellation_is_safe(self) -> None:
        som_result = object()
        edct_result = MagicMock()
        edct_display_result = object()
        with (
            patch.object(screens, "run_analysis", return_value=som_result),
            patch.object(screens, "export_result", return_value=Path("som.xlsx")),
        ):
            self.assertEqual(screens._run_som("in.xlsx", "out", ()), (som_result, Path("som.xlsx")))
        with (
            patch.object(screens, "run_edct_analysis", return_value=edct_result),
            patch.object(screens, "export_edct_result", return_value=Path("edct.xlsx")),
            patch.object(screens, "_build_edct_display_result", return_value=edct_display_result),
        ):
            self.assertEqual(
                screens._run_edct_in_process("in.xlsx", "out"),
                (edct_display_result, Path("edct.xlsx")),
            )
            edct_result.workbook.close.assert_called_once_with()

        window = MainWindow(QualityCheckerController())
        with patch.object(screens.QFileDialog, "getOpenFileName", return_value=("", "")):
            window.welcome_page._pick_input_file()
            window.edct_page._pick_input()
        with patch.object(screens.QFileDialog, "getExistingDirectory", return_value=""):
            window.welcome_page._pick_output_directory()
            window.edct_page._pick_output()

    def test_run_callbacks_create_one_worker_and_guard_reentry(self) -> None:
        class Signal:
            def connect(self, callback) -> None:
                pass

        class Thread:
            def __init__(self, parent=None) -> None:
                self.started = Signal()
                self.finished = Signal()
                self.started_count = 0

            def start(self) -> None:
                self.started_count += 1

            def quit(self) -> None:
                pass

            def deleteLater(self) -> None:
                pass

        window = MainWindow(QualityCheckerController())
        with patch.object(screens, "QThread", Thread), patch.object(AnalysisWorker, "moveToThread"):
            page = window.welcome_page
            page.input_file.setText("input.xlsx")
            page.output_dir.setText("out")
            page._on_run()
            thread = page._run_thread
            page._on_run()
            self.assertEqual(thread.started_count, 1)

            edct = window.edct_page
            edct.input_file.setText("input.xlsx")
            edct.output_dir.setText("out")
            edct._run()
            edct_thread = edct._run_thread
            edct._run()
            self.assertEqual(edct_thread.started_count, 1)

    def test_run_callbacks_report_missing_paths(self) -> None:
        window = MainWindow(QualityCheckerController())
        som = window.welcome_page
        som._on_run()
        self.assertIn("input workbook", som.status.text())
        som.input_file.setText("input.xlsx")
        som._on_run()
        self.assertIn("output folder", som.status.text())

        edct = window.edct_page
        edct._run()
        self.assertIn("Choose an input", edct.status.text())

    def test_negative_navigation_indices_and_logo_paths(self) -> None:
        window = MainWindow(QualityCheckerController())
        window._on_menu_changed(-1)
        window._on_edct_menu_changed(-1)
        with patch.object(screens, "APP_LOGO_PATH", MagicMock(**{"exists.return_value": True})):
            with patch.object(screens, "QPixmap", return_value=QPixmap(1, 1)):
                screens._create_sidebar("Test")
                MainWindow(QualityCheckerController())
        with patch.object(screens, "APP_LOGO_PATH", MagicMock(**{"exists.return_value": False})):
            screens._create_sidebar("Test")
            MainWindow(QualityCheckerController())

    def test_edct_success_previews_overlapping_sheet_rows_and_combined_totals(self) -> None:
        from collections import Counter
        from datetime import datetime

        workbook = Workbook()
        self.addCleanup(workbook.close)
        supplier = workbook.active
        supplier.title = "Supplier Level"
        supplier.append(["metadata"] * 4)
        supplier.append(["Index", "Supplier Punch code", "Supplier name", "Triplet COFOR"])
        supplier.append(["I-1", "1001", "Supplier", "001-A"])
        pn = workbook.create_sheet("PN Level")
        pn.append(["Punch seller", "Triplet COFOR"])
        pn.append(["unknown-seller", "not assessed"])
        pn.append(['="1001"', '="wrong-triplet"'])
        pn.append(["1001", "001-A"])
        result = screens.EdctRunResult(
            5,
            Path("input.xlsx"),
            datetime.now(),
            datetime.now(),
            0.1,
            workbook,
            (("Supplier Level", 3), ("PN Level", 3), ("PN Level", 4)),
            {
                ("Supplier Level", 3): EdctRowResult(0, "Quality check passed"),
                ("PN Level", 3): EdctRowResult(1, "Triplet COFOR wrong-triplet not allowed"),
                ("PN Level", 4): EdctRowResult(0, "Quality check passed"),
            },
            Counter(),
            False,
            None,
            pn_values={3: ("1001", "wrong-triplet"), 4: ("1001", "001-A")},
        )
        window = MainWindow(HistoryController())
        self.addCleanup(window.close)
        display_result = screens._build_edct_display_result(result)
        with patch.object(window.edct_history_page, "refresh_runs") as refresh:
            window.edct_page._finished(display_result, "output.xlsx", "")

        table = window.edct_page.preview_table
        self.assertEqual(
            [
                [table.item(row, column).text() for column in range(table.columnCount())]
                for row in range(table.rowCount())
            ],
            [
                [
                    "Supplier Level",
                    "3",
                    "I-1",
                    "1001",
                    "Supplier",
                    "001-A",
                    "0",
                    "Quality check passed",
                ],
                [
                    "PN Level",
                    "3",
                    "",
                    "1001",
                    "",
                    "wrong-triplet",
                    "1",
                    "Triplet COFOR wrong-triplet not allowed",
                ],
                ["PN Level", "4", "", "1001", "", "001-A", "0", "Quality check passed"],
            ],
        )
        self.assertIn("rows: 3", window.edct_page.status.text())
        self.assertIn("failed: 1", window.edct_page.status.text())
        self.assertEqual(window.edct_page.result_path.text(), "output.xlsx")
        self.assertTrue(window.edct_page.preview_empty.isHidden())
        refresh.assert_called_once_with()

        with patch.object(screens, "PREVIEW_ROWS", 2):
            limited_result = screens._build_edct_display_result(result)
            window.edct_page._fill_preview(limited_result)
        self.assertEqual(table.rowCount(), 2)
        self.assertEqual(table.item(1, 0).text(), "PN Level")
        self.assertEqual(table.item(1, 1).text(), "3")

    def test_run_app_bootstrap_always_shuts_down(self) -> None:
        fake_qt = MagicMock()
        fake_controller = MagicMock()
        fake_window = MagicMock()
        with (
            patch("PyQt6.QtWidgets.QApplication", return_value=fake_qt),
            patch.object(gui_app, "QualityCheckerController", return_value=fake_controller),
            patch.object(screens, "MainWindow", return_value=fake_window),
            patch.object(gui_app, "APP_LOGO_PATH", MagicMock(**{"exists.return_value": False})),
        ):
            gui_app.run_app()
        fake_controller.startup.assert_called_once_with()
        fake_window.show.assert_called_once_with()
        fake_qt.exec.assert_called_once_with()
        fake_controller.shutdown.assert_called_once_with()

        fake_qt.reset_mock()
        with (
            patch("PyQt6.QtWidgets.QApplication", return_value=fake_qt),
            patch("PyQt6.QtGui.QIcon", return_value=MagicMock()),
            patch.object(gui_app, "QualityCheckerController", return_value=fake_controller),
            patch.object(screens, "MainWindow", return_value=fake_window),
            patch.object(gui_app, "APP_LOGO_PATH", MagicMock(**{"exists.return_value": True})),
        ):
            gui_app.run_app()
        fake_qt.setWindowIcon.assert_called_once()
