from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ..config import DB_PATH, ensure_data_dir
from .schema import all_statements


@dataclass(slots=True)
class RunRecord:
    started_at: str
    finished_at: str
    duration_s: float
    input_file: str
    rows_total: int
    rows_in_scope: int
    rows_failed: int
    status: str
    error_message: str | None = None


@dataclass(slots=True)
class ColumnRecord:
    rule_name: str
    column_name: str
    fail_count: int


def open_connection(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    ensure_data_dir()
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_schema(connection: sqlite3.Connection) -> None:
    for statement in all_statements():
        connection.execute(statement)
    connection.commit()


def insert_run(
    connection: sqlite3.Connection,
    run_record: RunRecord,
    column_records: Iterable[ColumnRecord],
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO runs (
            started_at,
            finished_at,
            duration_s,
            input_file,
            rows_total,
            rows_in_scope,
            rows_failed,
            status,
            error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_record.started_at,
            run_record.finished_at,
            run_record.duration_s,
            run_record.input_file,
            run_record.rows_total,
            run_record.rows_in_scope,
            run_record.rows_failed,
            run_record.status,
            run_record.error_message,
        ),
    )
    if cursor.lastrowid is None:
        raise RuntimeError("Failed to persist run metadata")
    run_id = int(cursor.lastrowid)

    for column_record in column_records:
        connection.execute(
            """
            INSERT INTO run_columns (run_id, rule_name, column_name, fail_count)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, column_record.rule_name, column_record.column_name, column_record.fail_count),
        )

    connection.commit()
    return run_id


def list_runs(connection: sqlite3.Connection, limit: int = 200) -> list[sqlite3.Row]:
    cursor = connection.execute(
        """
        SELECT
            id,
            started_at,
            finished_at,
            duration_s,
            input_file,
            rows_total,
            rows_in_scope,
            rows_failed,
            status,
            error_message
        FROM runs
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    return list(cursor.fetchall())


def get_run_columns(connection: sqlite3.Connection, run_id: int) -> list[sqlite3.Row]:
    cursor = connection.execute(
        """
        SELECT
            rule_name,
            column_name,
            fail_count
        FROM run_columns
        WHERE run_id = ?
        ORDER BY rule_name, column_name
        """,
        (run_id,),
    )
    return list(cursor.fetchall())


def delete_run(connection: sqlite3.Connection, run_id: int) -> None:
    connection.execute("DELETE FROM runs WHERE id = ?", (run_id,))
    connection.commit()



