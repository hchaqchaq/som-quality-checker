from __future__ import annotations

import argparse

from .analysis.runner import run_analysis


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test SOM workbook analysis.")
    parser.add_argument("input_file", help="Path to the Excel workbook to analyze.")
    args = parser.parse_args()

    result = run_analysis(args.input_file)
    in_scope_failed = int((result.in_scope_df["Check"] > 0).sum())
    print(f"run_id={result.run_id}")
    print(f"duration_s={result.duration_s:.2f}")
    print(f"rows_total={len(result.final_df)}")
    print(f"rows_in_scope={len(result.in_scope_df)}")
    print(f"rows_failed={in_scope_failed}")


if __name__ == "__main__":
    main()


