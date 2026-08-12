import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
PACKAGE_SRC = PROJECT_ROOT / "quality_checker" / "src"
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))


def main() -> None:
    from quality_checker.gui.app import run_app

    run_app()


if __name__ == "__main__":
    main()
