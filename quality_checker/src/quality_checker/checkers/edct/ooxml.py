from __future__ import annotations

from posixpath import basename, dirname, normpath
from xml.etree import ElementTree
from zipfile import ZipFile

from .models import EdctLoadError


def worksheet_parts(archive: ZipFile) -> dict[str, str]:
    namespace = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    relationship_id = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    relationships = {
        element.attrib["Id"]: element.attrib["Target"]
        for element in ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    }
    root = ElementTree.fromstring(archive.read("xl/workbook.xml"))
    return {
        sheet.attrib["name"]: normpath("xl/" + relationships[sheet.attrib[relationship_id]]).lstrip(
            "/"
        )
        if not relationships[sheet.attrib[relationship_id]].startswith("/")
        else relationships[sheet.attrib[relationship_id]].lstrip("/")
        for sheet in root.findall(f"{{{namespace}}}sheets/{{{namespace}}}sheet")
    }


def table_part(archive: ZipFile, worksheet_part: str, table_name: str) -> str:
    relationships_part = f"{dirname(worksheet_part)}/_rels/{basename(worksheet_part)}.rels"
    relationships = ElementTree.fromstring(archive.read(relationships_part))
    for relationship in relationships:
        if not relationship.attrib["Type"].endswith("/table"):
            continue
        target = relationship.attrib["Target"]
        part = (
            target.lstrip("/")
            if target.startswith("/")
            else normpath(f"{dirname(worksheet_part)}/{target}")
        )
        table = ElementTree.fromstring(archive.read(part))
        if table.attrib.get("displayName") == table_name:
            return part
    raise EdctLoadError(f"Missing source table part: {table_name}")
