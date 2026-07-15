from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from som_analyzer.analysis.loader import LoadError, load_excel
from som_analyzer.analysis.runner import run_analysis
from som_analyzer.analysis.validator import build_default_rules, normalize
from som_analyzer.config import TEXT_COLUMNS, WANTED_COLUMNS


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
        self.assertEqual(result.row_messages.iloc[0], "COFOR PATTERN (6 CHARS + 2 SPACES + 2 CHARS)")

    def test_contact_columns_require_one_email_each(self) -> None:
        quality = results(
            [row(), row(**{"Quality contact": ""}), row(**{"Quality contact": "Name <a@example.com>"})]
        )["quality_contact_email"]
        logistic = results([row(), row(**{"Logistic contact": "a@example.com;b@example.com"})])[
            "logistic_contact_email"
        ]
        self.assertEqual(quality.fail_counts.tolist(), [0, 1, 1])
        self.assertEqual(logistic.fail_counts.tolist(), [0, 1])

    def test_status_requires_yes_contacted(self) -> None:
        result = results([row(Contacted="yes"), row(Contacted="NO"), row(Status="", Contacted="NO")])[
            "contacted_when_status_filled"
        ]
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
    def test_runner_checks_all_rows_and_aggregates_comments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.xlsx"
            pd.DataFrame(
                [
                    row(),
                    row(Status="Pending", Contacted="NO", NOTE="", **{"Quality contact": ""}),
                ]
            ).to_excel(input_path, index=False)
            with sqlite3.connect(":memory:") as connection:
                result = run_analysis(input_path, connection=connection, analysis_date=AS_OF)

        self.assertEqual(len(result.in_scope_df), 2)
        self.assertEqual(result.in_scope_df["Check"].tolist(), [0, 3])
        self.assertEqual(result.in_scope_df["Comment"].iloc[0], "Quality check passed")
        self.assertIn("INVALID OR MISSING EMAIL: Quality contact", result.in_scope_df["Comment"].iloc[1])
        self.assertIn("CONTACTED MUST BE YES WHEN STATUS IS FILLED", result.in_scope_df["Comment"].iloc[1])
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


if __name__ == "__main__":
    unittest.main()
