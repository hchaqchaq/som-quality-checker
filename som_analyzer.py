import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
PACKAGE_SRC = PROJECT_ROOT / "som_analyzer" / "src"
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from som_analyzer.analysis.runner import export_result, run_analysis  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SOM workbook validation.")
    parser.add_argument("input_file", help="Path to the Excel workbook to analyze.")
    parser.add_argument("output_path", help="Folder or file path where the analyzed workbook should be written.")
    args = parser.parse_args()

    result = run_analysis(args.input_file)
    exported_path = export_result(result, args.output_path)
    in_scope_failed = int((result.in_scope_df["Check"] > 0).sum())

    print(f"run_id={result.run_id}")
    print(f"duration_s={result.duration_s:.2f}")
    print(f"rows_total={len(result.final_df)}")
    print(f"rows_in_scope={len(result.in_scope_df)}")
    print(f"rows_failed={in_scope_failed}")
    print(f"exported_file={exported_path}")


if __name__ == "__main__":
    main()
