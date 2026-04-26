from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "som_analyzer.db"
DEFAULT_INPUT_FILE = DATA_DIR / "Working file - Coforization -20.04.xlsx"
DEFAULT_OUTPUT_FILE = DATA_DIR / "output.xlsx"
PREVIEW_ROWS = 25

WANTED_COLUMNS = [
    "Seller COFOR2",
    "Manufacturer COFOR",
    "Manufacturer address",
    "Shipper COFOR2",
    "Shipper COFOR Address",
    "Location ID2",
    "Location ID Address",
    "Quality contact",
    "Logistic contact",
    "Contacted",
    "Info completed",
    "NOTE",
    "Owner",
    "Format check",
    "Status",
    "SOM double-check",
    "Plant",
]

LOCATION_COLUMNS = ["Manufacturer address", "Shipper COFOR Address", "Location ID Address"]
EMAIL_COLUMNS = ["Quality contact", "Logistic contact"]
CHAR_LENGTH_COLUMNS = ["Seller COFOR2", "Manufacturer COFOR", "Shipper COFOR2"]
CHAR_LENGTH_COLUMN_12 = ["Location ID2"]
EXCEL_FORMULA_COLUMNS = ["Info completed", "Format check", "Owner"]

EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
CHAR_PATTERN_REGEX = r"^[a-zA-Z0-9]{6} {2}[a-zA-Z0-9]{2}$"
CHAR_LENGTH = 12
CONTACTED_ALLOWED_VALUES = ["yes", "no", "out of scope"]

PLANT_FILTER = ["149", "144", "142"]
CONTACTED_FILTER = ["yes", "no"]
INFO_COMPLETED_FILTER = ["Complete"]

LOCATION_REGEX = re.compile(
    r"(\b\d{4,6}\b)"
    r"|(\d+\s*[,/\-])"
    r"|([A-Za-z]{3,},\s*[A-Za-z0-9])"
    r"|(\b(via|rue|strada|ul\.|str\.|road|avenue|blvd"
    r"|street|zone\s+ind|route|calle|rua|allee|viale"
    r"|corso|piazza|contrada|localit|district"
    r"|industrial|zone)\b)",
    re.IGNORECASE,
)

EXCEL_ERRORS = {
    "#n/a",
    "#ref!",
    "#value!",
    "#div/0!",
    "#name?",
    "#null!",
    "#num!",
    "#getting_data",
}


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True, slots=True)
class ScopeFilterDefinition:
    column: str
    allowed_values: tuple[str, ...]
    normalize_text: bool = True
    casefold: bool = False


@dataclass(frozen=True, slots=True)
class PredicateRuleDefinition:
    kind: Literal["predicate"] = "predicate"
    rule_name: str = ""
    columns: tuple[str, ...] = ()
    predicate_name: str = ""
    message_template: str = ""


@dataclass(frozen=True, slots=True)
class AllowedValueRuleDefinition:
    kind: Literal["allowed_values"] = "allowed_values"
    rule_name: str = ""
    column: str = ""
    allowed_values: tuple[str, ...] = ()
    message: str = ""


@dataclass(frozen=True, slots=True)
class ConsistencyRuleDefinition:
    kind: Literal["status_info_missing"] = "status_info_missing"
    rule_name: str = ""


RuleDefinition = PredicateRuleDefinition | AllowedValueRuleDefinition | ConsistencyRuleDefinition


SCOPE_FILTERS = (
    ScopeFilterDefinition(column="Plant", allowed_values=tuple(PLANT_FILTER)),
    ScopeFilterDefinition(column="Contacted", allowed_values=tuple(CONTACTED_FILTER), casefold=True),
    ScopeFilterDefinition(column="Info completed", allowed_values=tuple(INFO_COMPLETED_FILTER)),
)


DEFAULT_RULE_DEFINITIONS: tuple[RuleDefinition, ...] = (
    PredicateRuleDefinition(
        rule_name="email",
        columns=tuple(EMAIL_COLUMNS),
        predicate_name="email",
        message_template="Invalid email: {columns}",
    ),
    PredicateRuleDefinition(
        rule_name="cofor_pattern",
        columns=tuple(CHAR_LENGTH_COLUMNS),
        predicate_name="cofor_pattern",
        message_template="Invalid COFOR pattern (6 chars + 2 spaces + 2 chars): {columns}",
    ),
    PredicateRuleDefinition(
        rule_name="length_12",
        columns=tuple(CHAR_LENGTH_COLUMN_12),
        predicate_name="length_12",
        message_template=f"Invalid length (must be {CHAR_LENGTH}): {{columns}}",
    ),
    AllowedValueRuleDefinition(
        rule_name="contacted",
        column="Contacted",
        allowed_values=tuple(CONTACTED_ALLOWED_VALUES),
        message="Invalid Contacted value (allowed: yes, no, out of scope)",
    ),
    PredicateRuleDefinition(
        rule_name="location",
        columns=tuple(LOCATION_COLUMNS),
        predicate_name="location",
        message_template=(
            "Invalid location (missing postal code, street number, city/country pattern, "
            "or street-type keyword): {columns}"
        ),
    ),
    PredicateRuleDefinition(
        rule_name="excel_ref",
        columns=tuple(EXCEL_FORMULA_COLUMNS),
        predicate_name="excel_ref",
        message_template="Invalid reference (Excel error token): {columns}",
    ),
    ConsistencyRuleDefinition(rule_name="status_info_missing"),
)

