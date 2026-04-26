from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Input, Static

from ..config import DEFAULT_INPUT_FILE, DEFAULT_OUTPUT_FILE, PREVIEW_ROWS


class DashboardScreen(Screen[None]):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            yield Static("Input file path (leave empty for default):")
            yield Input(str(DEFAULT_INPUT_FILE), id="input-file")
            yield Static("Output file path for export button:")
            yield Input(str(DEFAULT_OUTPUT_FILE), id="output-file")
            with Horizontal():
                yield Button("Run Analysis", id="run", variant="primary")
                yield Button("Export Current Result", id="export", variant="success")
                yield Button("History", id="history")
            yield Static("Ready", id="status")
            yield DataTable(id="preview")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#export", Button).disabled = True

    def _fill_preview(self, table: DataTable, dataframe) -> None:
        table.clear(columns=True)
        table.cursor_type = "row"

        columns = [str(column) for column in dataframe.columns]
        if not columns:
            return

        table.add_columns(*columns)
        preview = dataframe.head(PREVIEW_ROWS)
        for row in preview.itertuples(index=False):
            table.add_row(*[str(value) for value in row])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        status = self.query_one("#status", Static)

        if button_id == "history":
            self.app.open_history()
            return

        if button_id == "run":
            input_path = self.query_one("#input-file", Input).value.strip() or str(DEFAULT_INPUT_FILE)
            try:
                result = self.app.run_current_analysis(input_path)
            except Exception as exc:
                status.update(f"Run failed: {exc}")
                return

            table = self.query_one("#preview", DataTable)
            self._fill_preview(table, result.final_df)
            status.update(
                f"Run {result.run_id} finished in {result.duration_s:.2f}s | "
                f"rows: {len(result.final_df)} | failed in scope: {(result.in_scope_df['Check'] > 0).sum()}"
            )
            self.query_one("#export", Button).disabled = False
            return

        if button_id == "export":
            output_path = self.query_one("#output-file", Input).value.strip() or str(DEFAULT_OUTPUT_FILE)
            try:
                exported = self.app.export_current_result(output_path)
            except Exception as exc:
                status.update(f"Export failed: {exc}")
                return
            status.update(f"Exported to {Path(exported)}")


class HistoryScreen(Screen[None]):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            with Horizontal():
                yield Button("Refresh", id="refresh", variant="primary")
                yield Button("Back", id="back")
            yield Static("Delete run id:")
            with Horizontal():
                yield Input("", placeholder="run id", id="run-id")
                yield Button("Delete", id="delete", variant="error")
                yield Button("Load Columns", id="columns")
            yield Static("History", id="history-status")
            yield DataTable(id="runs-table")
            yield Static("Rule/column fail totals", id="columns-status")
            yield DataTable(id="columns-table")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_runs()

    def _refresh_runs(self) -> None:
        runs_table = self.query_one("#runs-table", DataTable)
        runs_table.clear(columns=True)
        runs_table.add_columns(
            "id",
            "started_at",
            "duration_s",
            "rows_total",
            "rows_in_scope",
            "rows_failed",
            "status",
            "input_file",
        )

        for run in self.app.history_runs():
            runs_table.add_row(
                str(run["id"]),
                str(run["started_at"]),
                f"{float(run['duration_s']):.2f}",
                str(run["rows_total"]),
                str(run["rows_in_scope"]),
                str(run["rows_failed"]),
                str(run["status"]),
                str(run["input_file"]),
            )

        self.query_one("#history-status", Static).update("History refreshed")

    def _refresh_columns(self, run_id: int) -> None:
        columns_table = self.query_one("#columns-table", DataTable)
        columns_table.clear(columns=True)
        columns_table.add_columns("rule_name", "column_name", "fail_count")
        for row in self.app.history_columns(run_id):
            columns_table.add_row(str(row["rule_name"]), str(row["column_name"]), str(row["fail_count"]))
        self.query_one("#columns-status", Static).update(f"Loaded columns for run {run_id}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "back":
            self.app.pop_screen()
            return

        if button_id == "refresh":
            self._refresh_runs()
            return

        run_id_input = self.query_one("#run-id", Input).value.strip()
        if not run_id_input.isdigit():
            self.query_one("#history-status", Static).update("Enter a numeric run id")
            return

        run_id = int(run_id_input)

        if button_id == "delete":
            self.app.delete_history_run(run_id)
            self._refresh_runs()
            self.query_one("#history-status", Static).update(f"Deleted run {run_id}")
            return

        if button_id == "columns":
            self._refresh_columns(run_id)


