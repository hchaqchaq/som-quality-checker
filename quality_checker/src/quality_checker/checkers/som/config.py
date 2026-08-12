from __future__ import annotations

from dataclasses import dataclass


WANTED_COLUMNS = [
    "Manufacturer COFOR",
    "Manufacturer address",
    "Shipper COFOR2",
    "Shipper COFOR Address",
    "Quality contact",
    "Logistic contact",
    "Contacted",
    "Info completed",
    "NOTE",
    "Format check",
    "Status",
    "Completion date",
    "Plant",
]

TEXT_COLUMNS = [column for column in WANTED_COLUMNS if column != "Completion date"]

EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"




@dataclass(frozen=True, slots=True)
class ScopeFilterDefinition:
    column: str
    allowed_values: tuple[str, ...]
    normalize_text: bool = True
    casefold: bool = False


SCOPE_FILTERS: tuple[ScopeFilterDefinition, ...] = ()
