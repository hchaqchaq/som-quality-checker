from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from quality_checker.checkers.edct.settings import (
    EdctHeaderSettings,
    load_edct_settings,
    save_edct_settings,
)


class TestEdctSettings(unittest.TestCase):
    def test_default_settings_contains_canonical_headers(self) -> None:
        settings = EdctHeaderSettings.default()
        self.assertEqual(settings.get_header("Supplier Level", "Index"), "Index")
        self.assertEqual(
            settings.get_header("Supplier Level", "Supplier Punch code"),
            "Supplier Punch code",
        )
        self.assertEqual(settings.get_header("PN Level", "Punch seller"), "Punch seller")
        self.assertEqual(settings.get_header("Open Task", "Punch Code"), "Punch Code")
        self.assertEqual(
            settings.get_header("Template-Cofor-Creation", "Punch Code"),
            "Punch Code",
        )
        self.assertEqual(settings.validate(), [])

    def test_save_and_load_round_trip(self) -> None:
        with TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "edct_header_mappings.json"
            settings = EdctHeaderSettings.default()
            settings.supplier_level["Supplier Punch code"] = "Code Fournisseur"
            settings.pn_level["Punch seller"] = "Vendeur Punch"

            save_edct_settings(settings, settings_path)
            self.assertTrue(settings_path.exists())

            loaded = load_edct_settings(settings_path)
            self.assertEqual(
                loaded.get_header("Supplier Level", "Supplier Punch code"),
                "Code Fournisseur",
            )
            self.assertEqual(loaded.get_header("PN Level", "Punch seller"), "Vendeur Punch")
            # Unmodified fields should retain canonical values
            self.assertEqual(loaded.get_header("Supplier Level", "Index"), "Index")

    def test_load_nonexistent_returns_default(self) -> None:
        with TemporaryDirectory() as temp_dir:
            nonexistent = Path(temp_dir) / "nonexistent.json"
            settings = load_edct_settings(nonexistent)
            self.assertEqual(settings.get_header("Supplier Level", "Index"), "Index")
            self.assertEqual(settings.validate(), [])

    def test_load_corrupted_json_falls_back_to_default(self) -> None:
        with TemporaryDirectory() as temp_dir:
            corrupted = Path(temp_dir) / "corrupted.json"
            corrupted.write_text("{invalid json", encoding="utf-8")
            settings = load_edct_settings(corrupted)
            self.assertEqual(settings.get_header("Supplier Level", "Index"), "Index")
            self.assertEqual(settings.validate(), [])

    def test_load_missing_fields_merges_with_defaults(self) -> None:
        with TemporaryDirectory() as temp_dir:
            partial_path = Path(temp_dir) / "partial.json"
            partial_path.write_text(
                json.dumps({"Supplier Level": {"Supplier Punch code": "Punch Code Custom"}}),
                encoding="utf-8",
            )
            settings = load_edct_settings(partial_path)
            self.assertEqual(
                settings.get_header("Supplier Level", "Supplier Punch code"),
                "Punch Code Custom",
            )
            # Other fields should have been merged from defaults
            self.assertEqual(settings.get_header("Supplier Level", "Index"), "Index")
            self.assertEqual(settings.get_header("PN Level", "Punch seller"), "Punch seller")

    def test_validation_rejects_empty_headers(self) -> None:
        settings = EdctHeaderSettings.default()
        settings.supplier_level["Index"] = "   "
        errors = settings.validate()
        self.assertTrue(any("empty" in err.lower() for err in errors))

    def test_validation_rejects_duplicate_headers_on_same_sheet(self) -> None:
        settings = EdctHeaderSettings.default()
        settings.supplier_level["Supplier name"] = "Index"  # Same as Index
        errors = settings.validate()
        self.assertTrue(any("duplicate" in err.lower() for err in errors))

    def test_validation_allows_same_header_on_different_sheets(self) -> None:
        settings = EdctHeaderSettings.default()
        # "Punch Code" exists in both Open Task and Template-Cofor-Creation by default
        self.assertEqual(settings.validate(), [])

    def test_inspect_workbook_headers(self) -> None:
        from openpyxl import Workbook
        from quality_checker.checkers.edct.settings import inspect_workbook_headers

        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.xlsx"
            wb = Workbook()
            ws_sup = wb.active
            ws_sup.title = "Supplier Level"
            ws_sup.append(["meta1", "meta2"])
            ws_sup.append(["Header1", "Header2", "Header3"])

            ws_pn = wb.create_sheet("PN Level")
            ws_pn.append(["PN_ColA", "PN_ColB"])

            wb.save(path)
            wb.close()

            detected = inspect_workbook_headers(path)
            self.assertEqual(detected["Supplier Level"], ["Header1", "Header2", "Header3"])
            self.assertEqual(detected["PN Level"], ["PN_ColA", "PN_ColB"])
            self.assertEqual(detected["Open Task"], [])


if __name__ == "__main__":
    unittest.main()
