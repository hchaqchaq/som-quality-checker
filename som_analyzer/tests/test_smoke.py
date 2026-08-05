from __future__ import annotations

import io
import runpy
import sys
import unittest
import warnings
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

from som_analyzer import smoke


class SmokeTests(unittest.TestCase):
    def test_main_prints_analysis_summary(self) -> None:
        result = SimpleNamespace(
            run_id=7,
            duration_s=1.234,
            final_df=pd.DataFrame({"Check": [0, 1, "Out of filters"]}),
            in_scope_df=pd.DataFrame({"Check": [0, 2]}),
        )
        output = io.StringIO()
        with (
            patch.object(sys, "argv", ["som-analyze-smoke", "input.xlsx"]),
            patch.object(smoke, "run_analysis", return_value=result),
            redirect_stdout(output),
        ):
            smoke.main()

        self.assertEqual(
            output.getvalue().splitlines(),
            ["run_id=7", "duration_s=1.23", "rows_total=3", "rows_in_scope=2", "rows_failed=1"],
        )

    def test_module_entrypoint_calls_main(self) -> None:
        result = SimpleNamespace(
            run_id=1,
            duration_s=0.0,
            final_df=pd.DataFrame({"Check": []}),
            in_scope_df=pd.DataFrame({"Check": []}),
        )
        with (
            patch.object(sys, "argv", ["som_analyzer.smoke", str(Path("input.xlsx"))]),
            patch("som_analyzer.analysis.runner.run_analysis", return_value=result),
            redirect_stdout(io.StringIO()),
            warnings.catch_warnings(),
        ):
            warnings.simplefilter("ignore", RuntimeWarning)
            runpy.run_module("som_analyzer.smoke", run_name="__main__")

    def test_main_requires_input_argument(self) -> None:
        with patch.object(sys, "argv", ["som-analyze-smoke"]), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                smoke.main()
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
