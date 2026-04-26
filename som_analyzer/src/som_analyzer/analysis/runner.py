from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from time import perf_counter

import pandas as pd
import sqlite3

from .loader import load_excel
from .validator import RuleResult, build_default_rules, build_scope_mask, normalize
from ..config import (
    DB_PATH,
    SCOPE_FILTERS,
    WANTED_COLUMNS,
)
from ..db.repository import (
    ColumnRecord,
    RunRecord,
    initialize_schema,
    insert_run,
    open_connection,
    update_run_exported_file,
)


@dataclass(slots=True)
class RunResult:
    run_id: int
    input_file: Path
    started_at: datetime
    finished_at: datetime
    duration_s: float
    final_df: pd.DataFrame
    in_scope_df: pd.DataFrame
    out_of_scope_df: pd.DataFrame
    rule_results: list[RuleResult]


def run_analysis(
    input_path: Path | str,
    connection: sqlite3.Connection | None = None,
) -> RunResult:
    resolved_input = Path(input_path)
    started_perf = perf_counter()
    started_at = datetime.now(timezone.utc)

    source_df = load_excel(resolved_input)
    source_df = source_df.copy()
    source_df["Check"] = pd.Series(dtype="boolean")
    source_df["Comment"] = pd.Series(dtype="string")

    df_normalized = normalize(source_df, WANTED_COLUMNS)
    mask_selected = build_scope_mask(df_normalized, SCOPE_FILTERS)

    df_filtered = df_normalized[mask_selected].copy()
    df_rest = df_normalized[~mask_selected].copy()
    df_rest["Comment"] = "No comment || Out of scope"
    df_rest["Check"] = "Out of scope"

    rule_results = [rule.evaluate(df_filtered) for rule in build_default_rules()]

    total_check = sum(result.fail_counts for result in rule_results)
    df_filtered["Check"] = total_check.astype(int)

    def build_comment(index) -> str:
        reasons = [
            str(result.row_messages.at[index])
            for result in rule_results
            if str(result.row_messages.at[index]).strip()
        ]
        return " | ".join(reasons)

    df_filtered["Comment"] = df_filtered.index.to_series().apply(build_comment).astype("string")
    df_filtered.loc[df_filtered["Check"] == 0, "Comment"] = "Quality check passed"

    final_df = pd.concat([df_filtered, df_rest], ignore_index=True)

    finished_at = datetime.now(timezone.utc)
    duration_s = perf_counter() - started_perf

    own_connection = connection is None
    if own_connection:
        connection = open_connection(DB_PATH)

    run_id = -1
    if connection is not None:
        initialize_schema(connection)
        run_record = RunRecord(
            started_at=started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            duration_s=duration_s,
            input_file=str(resolved_input),
            exported_file=None,
            rows_total=int(len(final_df)),
            rows_in_scope=int(len(df_filtered)),
            rows_failed=int((df_filtered["Check"] > 0).sum()),
            status="ok",
            error_message=None,
        )

        column_records: list[ColumnRecord] = []
        for result in rule_results:
            for column_name, fail_count in result.column_fail_counts.items():
                column_records.append(
                    ColumnRecord(rule_name=result.rule_name, column_name=column_name, fail_count=int(fail_count))
                )

        run_id = insert_run(connection, run_record, column_records)

    if own_connection and connection is not None:
        connection.close()

    return RunResult(
        run_id=run_id,
        input_file=resolved_input,
        started_at=started_at,
        finished_at=finished_at,
        duration_s=duration_s,
        final_df=final_df,
        in_scope_df=df_filtered,
        out_of_scope_df=df_rest,
        rule_results=rule_results,
    )


def export_result(result: RunResult, output_path: Path | str) -> Path:
    target = _build_export_target(result.input_file, output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    result.final_df.to_excel(target, index=False, engine="xlsxwriter", merge_cells=False)

    if result.run_id >= 0:
        connection = open_connection(DB_PATH)
        try:
            initialize_schema(connection)
            update_run_exported_file(connection, result.run_id, str(target))
        finally:
            connection.close()

    return target


def _build_export_target(input_file: Path, output_path: Path | str) -> Path:
    requested = Path(output_path)
    output_dir = requested if requested.suffix == "" else requested.parent

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", input_file.stem).strip("._") or "analysis"
    return output_dir / f"{safe_stem}_{timestamp}.xlsx"



