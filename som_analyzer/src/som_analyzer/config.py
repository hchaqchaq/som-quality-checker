from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT.parent))
APP_LOGO_PATH = APP_BUNDLE_ROOT / "logo.png"

if getattr(sys, "frozen", False):
    DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "SOM Quality Checker"
else:
    DATA_DIR = PROJECT_ROOT / "data"

DB_PATH = DATA_DIR / "som_analyzer.db"
PREVIEW_ROWS = 25

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


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True, slots=True)
class ScopeFilterDefinition:
    column: str
    allowed_values: tuple[str, ...]
    normalize_text: bool = True
    casefold: bool = False


SCOPE_FILTERS: tuple[ScopeFilterDefinition, ...] = ()
