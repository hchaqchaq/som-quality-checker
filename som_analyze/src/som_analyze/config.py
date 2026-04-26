from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "som_analyze.db"
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

