from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT.parent))
APP_LOGO_PATH = APP_BUNDLE_ROOT / "logo.png"

if getattr(sys, "frozen", False):
    DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Quality Checker"
else:
    DATA_DIR = PROJECT_ROOT / "data"

DB_PATH = DATA_DIR / "quality_checker.db"
PREVIEW_ROWS = 25


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
