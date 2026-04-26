from __future__ import annotations

RUNS_DDL = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    duration_s REAL NOT NULL,
    input_file TEXT NOT NULL,
    exported_file TEXT NOt NULL,
    rows_total INTEGER NOT NULL,
    rows_in_scope INTEGER NOT NULL,
    rows_failed INTEGER NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT
);
"""

RUN_COLUMNS_DDL = """
CREATE TABLE IF NOT EXISTS run_columns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    rule_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    fail_count INTEGER NOT NULL,
    FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
);
"""

INDEX_DDL = """
CREATE INDEX IF NOT EXISTS idx_run_columns_run_id ON run_columns(run_id);
"""


def all_statements() -> list[str]:
    return [RUNS_DDL, RUN_COLUMNS_DDL, INDEX_DDL]

