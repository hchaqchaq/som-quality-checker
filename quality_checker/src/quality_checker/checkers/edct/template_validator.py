from __future__ import annotations

from collections import Counter, defaultdict

from .config import (
    EDCT_COFOR_TEMPLATE_COMPANY_HEADER,
    EDCT_COFOR_TEMPLATE_HEADER_ROW,
    EDCT_COFOR_TEMPLATE_PUNCH_HEADER,
    EDCT_COFOR_TEMPLATE_SHEET,
    EDCT_HEADER_ROW,
)
from .models import EdctRowResult
from .workbook import (
    LoadedEdctWorkbook,
    header_map,
    normalized_choice,
    normalized_punch,
    normalized_text,
)


def validate_template(
    source: LoadedEdctWorkbook,
) -> tuple[dict[tuple[str, int], EdctRowResult], Counter[tuple[str, str]]]:
    template = source.workbook[EDCT_COFOR_TEMPLATE_SHEET]
    supplier = source.workbook["Supplier Level"]
    supplier_code_column = source.supplier_headers[
        source.settings.get_header("Supplier Level", "Supplier Punch code")
    ]
    supplier_name_column = source.supplier_headers[
        source.settings.get_header("Supplier Level", "Supplier name")
    ]
    names_by_code: dict[str, set[str]] = defaultdict(set)
    for row in range(EDCT_HEADER_ROW + 1, supplier.max_row + 1):
        code = normalized_punch(supplier.cell(row, supplier_code_column).value)
        if code:
            name = normalized_choice(supplier.cell(row, supplier_name_column).value)
            if name:
                names_by_code[code].add(name)
            else:
                names_by_code.setdefault(code, set())

    punch_header = source.settings.get_header(
        EDCT_COFOR_TEMPLATE_SHEET, EDCT_COFOR_TEMPLATE_PUNCH_HEADER
    )
    company_header = source.settings.get_header(
        EDCT_COFOR_TEMPLATE_SHEET, EDCT_COFOR_TEMPLATE_COMPANY_HEADER
    )
    company_column = header_map(template, EDCT_COFOR_TEMPLATE_HEADER_ROW)[company_header]
    results: dict[tuple[str, int], EdctRowResult] = {}
    totals: Counter[tuple[str, str]] = Counter()
    for row in range(EDCT_COFOR_TEMPLATE_HEADER_ROW + 1, template.max_row + 1):
        code = normalized_punch(template.cell(row, source.cofor_template_column).value)
        if not code:
            continue
        key = (EDCT_COFOR_TEMPLATE_SHEET, row)
        if code not in names_by_code:
            results[key] = EdctRowResult(
                1, f"Supplier Punch code not found in Supplier Level: {punch_header} = {code}"
            )
            totals[("template_supplier_code", punch_header)] += 1
            continue
        raw_name = template.cell(row, company_column).value
        name = normalized_choice(raw_name)
        if name and name in names_by_code[code]:
            results[key] = EdctRowResult(0, "Quality check passed")
        else:
            display_name = normalized_text(raw_name) or "<empty>"
            results[key] = EdctRowResult(
                1,
                f"{company_header} = {display_name}: does not match Supplier name "
                f"for {punch_header} = {code}",
            )
            totals[("template_supplier_name", company_header)] += 1
    return results, totals
