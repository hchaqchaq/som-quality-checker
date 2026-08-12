from __future__ import annotations

import importlib.util
import os
import re
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
from quality_checker.checkers.som import validator
from quality_checker.checkers.som.config import TEXT_COLUMNS, WANTED_COLUMNS, ScopeFilterDefinition
from quality_checker.checkers.som.loader import LoadError, load_excel
from quality_checker.checkers.som.runner import _build_export_target, export_result, run_analysis
from quality_checker.checkers.som.validator import build_default_rules, normalize
from quality_checker.db import repository
from quality_checker.db.repository import (
    ColumnRecord,
    RunRecord,
    delete_run,
    get_run_columns,
    initialize_schema,
    insert_run,
    list_runs,
    open_connection,
    update_run_exported_file,
    update_run_status,
)

AS_OF = date(2026, 7, 15)


def row(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "Manufacturer COFOR": "MFG001  01",
        "Manufacturer address": "1 Main Street",
        "Shipper COFOR2": "SHP001  01",
        "Shipper COFOR Address": "2 Main Street",
        "Quality contact": "quality@example.com",
        "Logistic contact": "logistic@example.com",
        "Contacted": "YES",
        "Info completed": "Completed",
        "NOTE": "Updated 15/07/2026",
        "Format check": "OK",
        "Status": "Complete",
        "Completion date": datetime(2026, 7, 15),
        "Plant": "149",
    }
    value.update(overrides)
    return value


def results(rows: list[dict[str, object]]):
    frame = normalize(pd.DataFrame(rows), TEXT_COLUMNS)
    return {rule.rule_name: rule.evaluate(frame) for rule in build_default_rules(AS_OF)}


class RuleTests(unittest.TestCase):
    def test_validator_helpers_cover_dates_empty_values_and_scope_options(self) -> None:
        self.assertTrue(validator.is_empty_value(None))
        self.assertEqual(validator.parse_completion_date(datetime(2026, 7, 15)), AS_OF)
        self.assertEqual(validator.parse_completion_date(AS_OF), AS_OF)
        self.assertIsNone(validator.parse_completion_date(""))
        self.assertEqual(validator.extract_note_dates("bad 31/02/2026 good 15/07/2026"), [AS_OF])

        class BadMissing:
            def __array__(self):
                raise ValueError("no array")

        self.assertFalse(validator.is_empty_value(BadMissing()))
        frame = pd.DataFrame({"Contacted": [" YES ", "no"], "Plant": [149, 200]})
        mask = validator.build_scope_mask(
            frame,
            (
                ScopeFilterDefinition("Contacted", ("yes",), casefold=True),
                ScopeFilterDefinition("Plant", (149,), normalize_text=False),
            ),
        )
        self.assertEqual(mask.tolist(), [True, False])

        with self.assertRaises(NotImplementedError):
            validator.ValidationRule.evaluate(object(), frame)

    def test_new_rule_set_is_exclusive(self) -> None:
        self.assertEqual(
            [rule.rule_name for rule in build_default_rules(AS_OF)],
            [
                "status_completed",
                "completion_date",
                "relance",
                "shipper_cofor_address",
                "manufacturer_cofor_address",
                "cofor_format",
                "quality_contact_email",
                "logistic_contact_email",
                "contacted_when_status_filled",
                "note_date_format",
            ],
        )

    def test_som_rule_documentation_matches_configuration(self) -> None:
        documentation = (
            Path(__file__).resolve().parents[2] / "docs" / "SOM_QUALITY_CHECKER.md"
        ).read_text(encoding="utf-8")
        inventory = documentation.split("## Configured column inventory", 1)[1].split(
            "## Validation rules", 1
        )[0]
        rules = documentation.split("## Validation rules", 1)[1].split("## Rule details", 1)[0]

        self.assertEqual(
            set(re.findall(r"^- `([^`]+)`$", inventory, re.MULTILINE)),
            set(WANTED_COLUMNS),
        )
        self.assertEqual(
            re.findall(r"^\|\s+`([^`]+)`\s+\|", rules, re.MULTILINE),
            [rule.rule_name for rule in build_default_rules(AS_OF)],
        )

    def test_completed_status_requires_completed_info(self) -> None:
        result = results(
            [row(**{"Info completed": " complete "}), row(**{"Info completed": "No"})]
        )["status_completed"]
        self.assertEqual(result.fail_counts.tolist(), [0, 1])
        self.assertEqual(result.row_messages.iloc[1], "INFO COMPLETED MUST BE COMPLETED")

    def test_completion_date_is_conditional_and_strict(self) -> None:
        result = results(
            [
                row(**{"Completion date": "15/07/2026"}),
                row(**{"Completion date": ""}),
                row(**{"Completion date": "2026-07-15"}),
                row(Contacted="NO", **{"Completion date": ""}),
            ]
        )["completion_date"]
        self.assertEqual(result.fail_counts.tolist(), [0, 1, 1, 0])
        self.assertEqual(result.row_messages.iloc[1], "COMPLETION DATE IS MISSING")
        self.assertEqual(result.row_messages.iloc[2], "COMPLETION DATE IS INVALID")

    def test_relance_uses_latest_note_date_and_three_day_window(self) -> None:
        result = results(
            [
                row(**{"Info completed": "", "NOTE": "12/07/2026"}),
                row(**{"Info completed": "", "NOTE": "11/07/2026"}),
                row(**{"Info completed": "", "NOTE": "10/07/2026 then 14/07/2026"}),
                row(**{"Info completed": "", "NOTE": "16/07/2026"}),
                row(**{"Info completed": "", "NOTE": "no date"}),
            ]
        )["relance"]
        self.assertEqual(result.fail_counts.tolist(), [0, 1, 0, 1, 1])
        self.assertEqual(result.row_messages.iloc[1], "RELANCE DATE IS OLDER THAN 3 DAYS")
        self.assertEqual(result.row_messages.iloc[3], "RELANCE DATE IS IN THE FUTURE")
        self.assertEqual(result.row_messages.iloc[4], "RELANCE DATE IS MISSING OR INVALID")

    def test_cofor_rules_flag_only_conflicting_nonblank_addresses(self) -> None:
        shipper = results(
            [
                row(**{"Shipper COFOR2": " ship-1 ", "Shipper COFOR Address": " 1 Main  Street "}),
                row(**{"Shipper COFOR2": "SHIP-1", "Shipper COFOR Address": "1 main street"}),
                row(**{"Shipper COFOR2": "SHIP-1", "Shipper COFOR Address": "2 Main Street"}),
                row(**{"Shipper COFOR2": "SHIP-1", "Shipper COFOR Address": ""}),
            ]
        )["shipper_cofor_address"]
        self.assertEqual(shipper.fail_counts.tolist(), [1, 1, 1, 0])
        self.assertIn("SHIPPER COFOR", shipper.row_messages.iloc[0])

        manufacturer = results(
            [
                row(**{"Manufacturer COFOR": "M-1", "Manufacturer address": "A"}),
                row(**{"Manufacturer COFOR": "m-1", "Manufacturer address": "B"}),
            ]
        )["manufacturer_cofor_address"]
        self.assertEqual(manufacturer.fail_counts.tolist(), [1, 1])

    def test_format_check_is_conditional_nok(self) -> None:
        result = results(
            [
                row(**{"Format check": " nok "}),
                row(**{"Format check": ""}),
                row(Contacted="NO", **{"Format check": "NOK"}),
                row(**{"Info completed": "", "Format check": "NOK"}),
            ]
        )["cofor_format"]
        self.assertEqual(result.fail_counts.tolist(), [1, 0, 0, 0])
        self.assertEqual(
            result.row_messages.iloc[0], "COFOR PATTERN (6 CHARS + 2 SPACES + 2 CHARS)"
        )

    def test_contact_columns_require_one_email_each(self) -> None:
        quality = results(
            [
                row(),
                row(**{"Quality contact": ""}),
                row(**{"Quality contact": "Name <a@example.com>"}),
            ]
        )["quality_contact_email"]
        logistic = results([row(), row(**{"Logistic contact": "a@example.com;b@example.com"})])[
            "logistic_contact_email"
        ]
        self.assertEqual(quality.fail_counts.tolist(), [0, 1, 1])
        self.assertEqual(logistic.fail_counts.tolist(), [0, 1])

    def test_status_requires_yes_contacted(self) -> None:
        result = results(
            [row(Contacted="yes"), row(Contacted="NO"), row(Status="", Contacted="NO")]
        )["contacted_when_status_filled"]
        self.assertEqual(result.fail_counts.tolist(), [0, 1, 0])

    def test_note_requires_real_strict_date(self) -> None:
        result = results(
            [
                row(NOTE="Called 15/07/2026"),
                row(NOTE="Called 5/7/2026"),
                row(NOTE="Called 31/02/2026"),
                row(NOTE=""),
            ]
        )["note_date_format"]
        self.assertEqual(result.fail_counts.tolist(), [0, 1, 1, 1])

    def test_note_rejects_any_invalid_date_when_another_date_is_valid(self) -> None:
        result = results(
            [
                row(NOTE="Called 15/07/2026 and again 16/07/2026"),
                row(NOTE="Called 15/07/2026 and again 2026-07-16"),
                row(NOTE="Called 15/07/2026 and again 5/7/2026"),
            ]
        )["note_date_format"]
        self.assertEqual(result.fail_counts.tolist(), [0, 1, 1])


class IntegrationTests(unittest.TestCase):
    def test_loader_reports_missing_and_unreadable_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.xlsx"
            with self.assertRaisesRegex(LoadError, "Input file not found"):
                load_excel(missing)
            unreadable = Path(directory) / "broken.xlsx"
            unreadable.write_text("not an Excel workbook", encoding="utf-8")
            with self.assertRaisesRegex(LoadError, "Unable to read Excel file"):
                load_excel(unreadable)

    def test_runner_checks_all_rows_and_aggregates_comments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.xlsx"
            pd.DataFrame(
                [
                    row(),
                    row(Status="Pending", Contacted="NO", NOTE="", **{"Quality contact": ""}),
                ]
            ).to_excel(input_path, index=False)
            with closing(sqlite3.connect(":memory:")) as connection:
                result = run_analysis(input_path, connection=connection, analysis_date=AS_OF)

        self.assertEqual(len(result.in_scope_df), 2)
        self.assertEqual(result.in_scope_df["Check"].tolist(), [0, 3])
        self.assertEqual(result.in_scope_df["Comment"].iloc[0], "Quality check passed")
        self.assertIn(
            "INVALID OR MISSING EMAIL: Quality contact", result.in_scope_df["Comment"].iloc[1]
        )
        self.assertIn(
            "CONTACTED MUST BE YES WHEN STATUS IS FILLED", result.in_scope_df["Comment"].iloc[1]
        )
        self.assertIn("NOTE DATE MUST USE DD/MM/YYYY", result.in_scope_df["Comment"].iloc[1])

    def test_completion_date_is_required_by_loader(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.xlsx"
            frame = pd.DataFrame([row()])
            frame.to_excel(input_path, index=False)
            self.assertEqual(list(load_excel(input_path).columns), list(frame.columns))
            frame.drop(columns=["Completion date"]).to_excel(input_path, index=False)
            with self.assertRaisesRegex(LoadError, "Completion date"):
                load_excel(input_path)
        self.assertNotIn("Seller COFOR2", WANTED_COLUMNS)
        self.assertNotIn("Location ID2", WANTED_COLUMNS)

    def test_history_migrates_existing_runs_to_som_and_filters_projects(self) -> None:
        with closing(sqlite3.connect(":memory:")) as connection:
            connection.row_factory = sqlite3.Row
            connection.execute(
                """
                CREATE TABLE runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    duration_s REAL NOT NULL,
                    input_file TEXT NOT NULL,
                    exported_file TEXT,
                    rows_total INTEGER NOT NULL,
                    rows_in_scope INTEGER NOT NULL,
                    rows_failed INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT
                )
                """
            )
            connection.execute(
                """
                INSERT INTO runs (
                    started_at, finished_at, duration_s, input_file, exported_file,
                    rows_total, rows_in_scope, rows_failed, status, error_message
                ) VALUES ('start', 'finish', 1, 'som.xlsx', NULL, 1, 1, 0, 'ok', NULL)
                """
            )
            initialize_schema(connection)
            insert_run(
                connection,
                RunRecord(
                    project="eDCT",
                    started_at="start",
                    finished_at="finish",
                    duration_s=1,
                    input_file="edct.xlsx",
                    exported_file=None,
                    rows_total=1,
                    rows_in_scope=1,
                    rows_failed=0,
                    status="ok",
                ),
                [],
            )

            self.assertEqual(
                [run["input_file"] for run in list_runs(connection, "SOM")], ["som.xlsx"]
            )
            self.assertEqual(
                [run["input_file"] for run in list_runs(connection, "eDCT")], ["edct.xlsx"]
            )

    def test_repository_run_lifecycle_and_nullable_export_migration(self) -> None:
        with closing(sqlite3.connect(":memory:")) as connection:
            connection.row_factory = sqlite3.Row
            connection.executescript(
                """
                CREATE TABLE runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, project TEXT NOT NULL DEFAULT 'SOM',
                    started_at TEXT NOT NULL, finished_at TEXT NOT NULL, duration_s REAL NOT NULL,
                    input_file TEXT NOT NULL, exported_file TEXT NOT NULL, rows_total INTEGER NOT NULL,
                    rows_in_scope INTEGER NOT NULL, rows_failed INTEGER NOT NULL, status TEXT NOT NULL,
                    error_message TEXT
                );
                CREATE TABLE run_columns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                    rule_name TEXT NOT NULL, column_name TEXT NOT NULL, fail_count INTEGER NOT NULL
                );
                INSERT INTO runs VALUES (1, 'SOM', 'start', 'finish', 1, 'input.xlsx', 'old.xlsx', 2, 2, 1, 'ok', NULL);
                INSERT INTO run_columns VALUES (1, 1, 'email', 'Quality contact', 1);
                """
            )
            initialize_schema(connection)
            self.assertEqual(
                connection.execute("SELECT exported_file FROM runs").fetchone()[0], "old.xlsx"
            )
            self.assertEqual(get_run_columns(connection, 1)[0]["fail_count"], 1)

            run_id = insert_run(
                connection,
                RunRecord("SOM", "s", "f", 0.5, "new.xlsx", None, 1, 1, 0, "ok"),
                [ColumnRecord("email", "Logistic contact", 2)],
            )
            update_run_exported_file(connection, run_id, "export.xlsx")
            update_run_status(connection, run_id, "failed", "boom")
            newest = list_runs(connection, limit=1)[0]
            self.assertEqual(
                (newest["exported_file"], newest["status"], newest["error_message"]),
                ("export.xlsx", "failed", "boom"),
            )
            self.assertEqual(
                get_run_columns(connection, run_id)[0]["column_name"], "Logistic contact"
            )
            delete_run(connection, run_id)
            self.assertEqual(list_runs(connection, limit=1)[0]["id"], 1)

    def test_runner_scope_export_and_automatic_connection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "unsafe name.xlsx"
            pd.DataFrame([row(Plant="149"), row(Plant="200")]).to_excel(input_path, index=False)
            filters = (ScopeFilterDefinition("Plant", ("149",)),)
            with patch("quality_checker.checkers.som.runner.DB_PATH", root / "history.db"):
                result = run_analysis(input_path, filters, analysis_date=AS_OF)
                target = export_result(result, root / "exports")
            self.assertEqual(len(result.in_scope_df), 1)
            self.assertEqual(result.out_of_scope_df["Comment"].tolist(), ["Out of filters"])
            self.assertTrue(target.exists())
            self.assertRegex(target.name, r"unsafe_name_\d{8}_\d{6}\.xlsx")
            self.assertEqual(_build_export_target(input_path, root / "named.xlsx").parent, root)

    def test_open_connection_initializes_sqlite_options(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.db"
            with patch("quality_checker.db.repository.ensure_data_dir") as ensure:
                with closing(open_connection(path)) as connection:
                    self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
                    self.assertIsInstance(connection.execute("SELECT 1").fetchone(), sqlite3.Row)
            ensure.assert_called_once_with()

    def test_repository_migration_edge_paths(self) -> None:
        with closing(sqlite3.connect(":memory:")) as connection:
            connection.execute("CREATE TABLE runs (id INTEGER PRIMARY KEY)")
            repository._migrate_runs_exported_file_nullable(connection)
            self.assertIn(
                "exported_file", {row[1] for row in connection.execute("PRAGMA table_info(runs)")}
            )

        with closing(sqlite3.connect(":memory:")) as connection:
            connection.execute(
                """CREATE TABLE runs (
                id INTEGER PRIMARY KEY, project TEXT NOT NULL DEFAULT 'SOM', started_at TEXT NOT NULL,
                finished_at TEXT NOT NULL, duration_s REAL NOT NULL, input_file TEXT NOT NULL,
                exported_file TEXT NOT NULL, rows_total INTEGER NOT NULL, rows_in_scope INTEGER NOT NULL,
                rows_failed INTEGER NOT NULL, status TEXT NOT NULL, error_message TEXT)"""
            )
            with self.assertRaisesRegex(sqlite3.OperationalError, "run_columns"):
                repository._migrate_runs_exported_file_nullable(connection)

        fake_connection = MagicMock()
        fake_connection.execute.return_value.lastrowid = None
        with self.assertRaisesRegex(RuntimeError, "Failed to persist"):
            insert_run(
                fake_connection,
                RunRecord("SOM", "s", "f", 0, "in", None, 0, 0, 0, "ok"),
                [],
            )

    def test_runner_without_database_and_export_without_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "input.xlsx"
            pd.DataFrame([row()]).to_excel(input_path, index=False)
            with patch("quality_checker.checkers.som.runner.open_connection", return_value=None):
                result = run_analysis(input_path, analysis_date=AS_OF)
            self.assertEqual(result.run_id, -1)
            self.assertTrue(export_result(result, root / "out").exists())

    def test_frozen_config_uses_local_app_data(self) -> None:
        config_path = Path(validator.__file__).parents[2] / "application.py"
        spec = importlib.util.spec_from_file_location("frozen_config_for_test", config_path)
        module = importlib.util.module_from_spec(spec)
        with (
            patch.object(sys, "frozen", True, create=True),
            patch.dict(os.environ, {"LOCALAPPDATA": "C:/Local"}),
            patch.dict(sys.modules, {"frozen_config_for_test": module}),
        ):
            assert spec.loader is not None
            spec.loader.exec_module(module)
        self.assertEqual(module.DATA_DIR, Path("C:/Local") / "Quality Checker")


if __name__ == "__main__":
    unittest.main()
