from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
PACKAGE_SRC = PROJECT_ROOT / "som_analyzer" / "src"
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from som_analyzer.gui.app import run_app


if __name__ == "__main__":
    run_app()
