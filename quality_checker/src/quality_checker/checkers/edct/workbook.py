from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from .config import (
    EDCT_COFOR_TEMPLATE_HEADER_ROW,
    EDCT_COFOR_TEMPLATE_PUNCH_HEADER,
    EDCT_COFOR_TEMPLATE_SHEET,
    EDCT_HEADER_ROW,
    EDCT_INDEX_COLUMN,
    EDCT_INDEX_COLUMNS,
    EDCT_PN_HEADER_ROW,
    EDCT_PN_REQUIRED_COLUMNS,
    EDCT_PN_SHEET,
    EDCT_REQUIRED_COLUMNS,
    EDCT_REQUIRED_SHEETS,
)
from .models import EdctLoadError
from .settings import EdctHeaderSettings

OPEN_TASK_SHEET = "Open Task"
SUPPLIER_LEVEL_SHEET = "Supplier Level"
OPEN_TASK_PUNCH_HEADER = "Punch Code"


def normalized_text(value: object) -> str:
    return "" if value is None else str(value).strip()


def normalized_choice(value: object) -> str:
    return normalized_text(value).casefold()


def normalized_punch(value: object) -> str:
    text = normalized_text(value)
    return text[:-2] if re.fullmatch(r"\d+\.0", text) else text


def header_map(worksheet: Worksheet, row: int = EDCT_HEADER_ROW) -> dict[str, int]:
    return {
        normalized_text(cell.value): cell.column
        for cell in worksheet[row]
        if normalized_text(cell.value)
    }


@dataclass(slots=True)
class LoadedEdctWorkbook:
    path: Path
    workbook: Workbook
    settings: EdctHeaderSettings
    supplier_headers: dict[str, int]
    pn_headers: dict[str, int]
    supplier_rows: tuple[int, ...]
    supplier_index_header: str
    cofor_template_column: int

    def supplier_header(self, canonical: str) -> str:
        return self.settings.get_header(SUPPLIER_LEVEL_SHEET, canonical)

    def supplier_value(self, row: int, canonical: str) -> object:
        configured = self.supplier_header(canonical)
        return (
            self.workbook[SUPPLIER_LEVEL_SHEET].cell(row, self.supplier_headers[configured]).value
        )

    def open_task_punches(self) -> set[str]:
        worksheet = self.workbook[OPEN_TASK_SHEET]
        configured = self.settings.get_header(OPEN_TASK_SHEET, OPEN_TASK_PUNCH_HEADER)
        column = header_map(worksheet, EDCT_HEADER_ROW)[configured]
        return {
            punch
            for row in range(EDCT_HEADER_ROW + 1, worksheet.max_row + 1)
            if (punch := normalized_punch(worksheet.cell(row, column).value))
        }

    def cofor_template_punches(self) -> set[str]:
        worksheet = self.workbook[EDCT_COFOR_TEMPLATE_SHEET]
        return {
            punch
            for row in range(EDCT_COFOR_TEMPLATE_HEADER_ROW + 1, worksheet.max_row + 1)
            if (punch := normalized_choice(worksheet.cell(row, self.cofor_template_column).value))
        }

    def close(self) -> None:
        self.workbook.close()


def load_edct_workbook(
    input_path: Path | str,
    settings: EdctHeaderSettings,
) -> LoadedEdctWorkbook:
    path = Path(input_path)
    if not path.exists():
        raise EdctLoadError(f"Input file not found: {path}")

    workbook = load_workbook(path, data_only=False)
    try:
        missing_sheets = [
            sheet for sheet in EDCT_REQUIRED_SHEETS if sheet not in workbook.sheetnames
        ]
        missing_columns: list[str] = []
        supplier_headers: dict[str, int] = {}
        pn_headers: dict[str, int] = {}
        supplier_index_header = settings.get_header(SUPPLIER_LEVEL_SHEET, EDCT_INDEX_COLUMN)

        if SUPPLIER_LEVEL_SHEET in workbook.sheetnames:
            supplier_headers = header_map(workbook[SUPPLIER_LEVEL_SHEET], EDCT_HEADER_ROW)
            for column in EDCT_REQUIRED_COLUMNS:
                if column == EDCT_INDEX_COLUMN:
                    continue
                configured = settings.get_header(SUPPLIER_LEVEL_SHEET, column)
                if configured not in supplier_headers:
                    missing_columns.append(configured)
            if supplier_index_header == EDCT_INDEX_COLUMN:
                if not any(column in supplier_headers for column in EDCT_INDEX_COLUMNS):
                    missing_columns.append("Index or Line")
            elif supplier_index_header not in supplier_headers:
                missing_columns.append(supplier_index_header)

        if EDCT_PN_SHEET in workbook.sheetnames:
            pn_headers = header_map(workbook[EDCT_PN_SHEET], EDCT_PN_HEADER_ROW)
            for column in EDCT_PN_REQUIRED_COLUMNS:
                configured = settings.get_header(EDCT_PN_SHEET, column)
                if configured not in pn_headers:
                    missing_columns.append(f"{EDCT_PN_SHEET}.{configured}")

        if OPEN_TASK_SHEET in workbook.sheetnames:
            configured = settings.get_header(OPEN_TASK_SHEET, OPEN_TASK_PUNCH_HEADER)
            if configured not in header_map(workbook[OPEN_TASK_SHEET], EDCT_HEADER_ROW):
                missing_columns.append(f"{OPEN_TASK_SHEET}.{configured}")

        expected_template_header = settings.get_header(
            EDCT_COFOR_TEMPLATE_SHEET, EDCT_COFOR_TEMPLATE_PUNCH_HEADER
        )
        cofor_template_column: int | None = None
        if EDCT_COFOR_TEMPLATE_SHEET in workbook.sheetnames:
            template_headers = header_map(
                workbook[EDCT_COFOR_TEMPLATE_SHEET], EDCT_COFOR_TEMPLATE_HEADER_ROW
            )
            cofor_template_column = template_headers.get(expected_template_header)
            if cofor_template_column is None:
                missing_columns.append(f"{EDCT_COFOR_TEMPLATE_SHEET}.{expected_template_header}")

        if missing_sheets or missing_columns:
            parts: list[str] = []
            if missing_sheets:
                parts.append(f"sheets: {', '.join(missing_sheets)}")
            if missing_columns:
                parts.append(f"columns: {', '.join(missing_columns)}")
            raise EdctLoadError(f"Missing required structure: {'; '.join(parts)}")

        assert cofor_template_column is not None
        if supplier_index_header in supplier_headers:
            index_header = supplier_index_header
        else:
            index_header = "Line"
        supplier = workbook[SUPPLIER_LEVEL_SHEET]
        supplier_rows = tuple(
            row
            for row in range(EDCT_HEADER_ROW + 1, supplier.max_row + 1)
            if normalized_text(supplier.cell(row, supplier_headers[index_header]).value)
        )
        return LoadedEdctWorkbook(
            path=path,
            workbook=workbook,
            settings=settings,
            supplier_headers=supplier_headers,
            pn_headers=pn_headers,
            supplier_rows=supplier_rows,
            supplier_index_header=index_header,
            cofor_template_column=cofor_template_column,
        )
    except Exception:
        workbook.close()
        raise
