from __future__ import annotations

from collections import Counter

from .config import EDCT_COFOR_TEMPLATE_HEADER_ROW, EDCT_COFOR_TEMPLATE_PUNCH_HEADER, EDCT_COFOR_TEMPLATE_SHEET, EDCT_HEADER_ROW
from .models import EdctRowResult
from .workbook import LoadedEdctWorkbook, normalized_punch


def validate_template(source: LoadedEdctWorkbook) -> tuple[dict[tuple[str, int], EdctRowResult], Counter[tuple[str, str]]]:
    template = source.workbook[EDCT_COFOR_TEMPLATE_SHEET]
    supplier = source.workbook["Supplier Level"]
    supplier_header = source.settings.get_header("Supplier Level", "Supplier Punch code")
    supplier_column = source.supplier_headers[supplier_header]
    known = {
        code
        for row in range(EDCT_HEADER_ROW + 1, supplier.max_row + 1)
        if (code := normalized_punch(supplier.cell(row, supplier_column).value))
    }
    punch_header = source.settings.get_header(EDCT_COFOR_TEMPLATE_SHEET, EDCT_COFOR_TEMPLATE_PUNCH_HEADER)
    results: dict[tuple[str, int], EdctRowResult] = {}
    totals: Counter[tuple[str, str]] = Counter()
    for row in range(EDCT_COFOR_TEMPLATE_HEADER_ROW + 1, template.max_row + 1):
        raw = template.cell(row, source.cofor_template_column).value
        code = normalized_punch(raw)
        if not code:
            continue
        if code in known:
            results[(EDCT_COFOR_TEMPLATE_SHEET, row)] = EdctRowResult(0, "Quality check passed")
        else:
            results[(EDCT_COFOR_TEMPLATE_SHEET, row)] = EdctRowResult(
                1, f"Supplier Punch code not found in Supplier Level: {punch_header} = {code}"
            )
            totals[("template_supplier_code", punch_header)] += 1
    return results, totals
