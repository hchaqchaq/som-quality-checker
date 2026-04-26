from pathlib import Path
import sys
from importlib import import_module

PROJECT_ROOT = Path(__file__).resolve().parent
PACKAGE_SRC = PROJECT_ROOT / "som_analyzer" / "src"
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

if __name__ == "__main__":
    run_app = import_module("som_analyzer.gui.app").run_app
    run_app()
