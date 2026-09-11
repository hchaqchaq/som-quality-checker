from __future__ import annotations

import sqlite3
from collections import Counter
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path
from time import perf_counter

from ...application import DB_PATH
from ...db.repository import (
    ColumnRecord,
    RunRecord,
    initialize_schema,
    insert_run,
    open_connection,
)
from .config import EDCT_PN_SHEET, EDCT_PROJECT, EDCT_REQUIRED_COLUMNS
from .models import EdctAssessedRow, EdctRunResult
from .pn_validator import validate_pn
from .settings import EdctHeaderSettings, load_edct_settings
from .validator import validate_suppliers
from .workbook import load_edct_workbook


def _open_history(connection: sqlite3.Connection | None) -> tuple[sqlite3.Connection, bool]:
    if connection is not None:
        initialize_schema(connection)
        return connection, False
    own_connection = open_connection(DB_PATH)
    initialize_schema(own_connection)
    return own_connection, True


def _insert_history(
    connection: sqlite3.Connection,
    *,
    started_at: datetime,
    finished_at: datetime,
    duration_s: float,
    input_file: Path,
    rows_total: int,
    rows_failed: int,
    status: str,
    error_message: str | None,
    rule_totals: Counter[tuple[str, str]] | None = None,
) -> int:
    columns = [
        ColumnRecord(rule_name=rule, column_name=column, fail_count=count)
        for (rule, column), count in (rule_totals or {}).items()
    ]
    return insert_run(
        connection,
        RunRecord(
            project=EDCT_PROJECT,
            started_at=started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            duration_s=duration_s,
            input_file=str(input_file),
            exported_file=None,
            rows_total=rows_total,
            rows_in_scope=rows_total,
            rows_failed=rows_failed,
            status=status,
            error_message=error_message,
        ),
        columns,
    )


def run_edct_analysis(
    input_path: Path | str,
    connection: sqlite3.Connection | None = None,
    *,
    analysis_date: date | None = None,
    settings: EdctHeaderSettings | None = None,
    progress: Callable[[str], None] | None = None,
) -> EdctRunResult:
    report = progress or (lambda _message: None)
    active_settings = settings if settings is not None else load_edct_settings()
    resolved_input = Path(input_path)
    started_at = datetime.now(UTC)
    started_perf = perf_counter()
    history, own_connection = _open_history(connection)

    try:
        report("Loading workbook…")
        source = load_edct_workbook(resolved_input, active_settings)
        workbook = source.workbook
        headers = source.supplier_headers
        pn_headers = source.pn_headers
        supplier_rows = source.supplier_rows
        cofor_template_column = source.cofor_template_column
        report("Checking PN Level…")
        pn_results, pn_values = validate_pn(source)
        report("Checking Supplier Level…")
        supplier_results, rule_totals = validate_suppliers(
            source,
            analysis_date or date.today(),
        )
        report("Preparing results…")
        row_results = {
            ("Supplier Level", row): row_result for row, row_result in supplier_results.items()
        }
        row_results.update(pn_results)
        pn_failures = sum(row_result.check for row_result in pn_results.values())
        if pn_failures:
            configured_pn_triplet = active_settings.get_header(EDCT_PN_SHEET, "Triplet COFOR")
            rule_totals[("pn_triplet_cofor", configured_pn_triplet)] = pn_failures
        assessed_rows = tuple(row_results)
        assessed_row_details: list[EdctAssessedRow] = []
        supplier_sheet = workbook["Supplier Level"]
        index_column = headers[source.supplier_index_header]
        for sheet_name, workbook_row in assessed_rows:
            if sheet_name == EDCT_PN_SHEET:
                punch, triplet = pn_values[workbook_row]
                index = supplier_name = ""
            else:
                index = supplier_sheet.cell(workbook_row, index_column).value
                punch = source.supplier_value(workbook_row, "Supplier Punch code")
                supplier_name = source.supplier_value(workbook_row, "Supplier name")
                triplet = source.supplier_value(workbook_row, "Triplet COFOR")
            assessed_row_details.append(
                EdctAssessedRow(
                    sheet_name=sheet_name,
                    workbook_row=workbook_row,
                    index=index,
                    punch=punch,
                    supplier_name=supplier_name,
                    triplet=triplet,
                    result=row_results[(sheet_name, workbook_row)],
                )
            )
        finished_at = datetime.now(UTC)
        duration_s = perf_counter() - started_perf
        run_id = _insert_history(
            history,
            started_at=started_at,
            finished_at=finished_at,
            duration_s=duration_s,
            input_file=resolved_input,
            rows_total=len(assessed_rows),
            rows_failed=sum(result.check > 0 for result in row_results.values()),
            status="ok",
            error_message=None,
            rule_totals=rule_totals,
        )
        return EdctRunResult(
            run_id=run_id,
            input_file=resolved_input,
            started_at=started_at,
            finished_at=finished_at,
            duration_s=duration_s,
            workbook=workbook,
            assessed_rows=assessed_rows,
            row_results=row_results,
            rule_totals=rule_totals,
            uses_default_db=own_connection,
            history_connection=None if own_connection else history,
            pn_values=pn_values,
            assessed_row_details=tuple(assessed_row_details),
            supplier_headers={
                column: active_settings.get_header("Supplier Level", column)
                for column in EDCT_REQUIRED_COLUMNS
            },
        )
    except Exception as exc:
        if "workbook" in locals():
            workbook.close()
        finished_at = datetime.now(UTC)
        _insert_history(
            history,
            started_at=started_at,
            finished_at=finished_at,
            duration_s=perf_counter() - started_perf,
            input_file=resolved_input,
            rows_total=0,
            rows_failed=0,
            status="failed",
            error_message=str(exc),
        )
        raise
    finally:
        if own_connection:
            history.close()
