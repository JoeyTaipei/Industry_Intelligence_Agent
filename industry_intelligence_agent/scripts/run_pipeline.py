"""Windows-friendly CLI for running the Industry Intelligence Agent MVP."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import run_mvp_pipeline


def parse_bool(value: str | bool) -> bool:
    """Parse PowerShell-friendly true/false values."""
    if isinstance(value, bool):
        return value
    value = value.strip().lower()
    if value in {"true", "1", "yes", "y"}:
        return True
    if value in {"false", "0", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError("Use true or false.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Industry Intelligence Agent MVP.")
    parser.add_argument("--company", default="TSMC", help="Company name, for example TSMC.")
    parser.add_argument("--industry", default="semiconductor", help="Industry keyword.")
    parser.add_argument("--company-registry", default="", help="Local company registry CSV path.")
    parser.add_argument("--news-csv", default="", help="Sample news CSV path.")
    parser.add_argument("--annual-report", default="", help="Optional local annual report PDF path.")
    parser.add_argument("--use-sample-data", type=parse_bool, default=True, help="Generate/use sample data: true/false.")
    parser.add_argument("--export-excel", type=parse_bool, default=True, help="Export Excel workbook: true/false.")
    parser.add_argument("--language", default="zh-TW", choices=["zh-TW", "en"], help="Demo summary language.")
    parser.add_argument("--output-dir", default="data/exports", help="CSV output directory.")
    return parser


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    args = build_parser().parse_args()

    paths = run_mvp_pipeline(
        company=args.company,
        industry=args.industry,
        company_registry=args.company_registry or None,
        news_csv=args.news_csv or None,
        annual_report=args.annual_report or None,
        use_sample_data=args.use_sample_data,
        export_excel=args.export_excel,
        language=args.language,
        output_dir=args.output_dir,
    )

    print("\nMVP pipeline finished successfully.")
    print("Output files:")
    for label, path in paths.items():
        print(f"- {label}: {path}")


if __name__ == "__main__":
    main()
