#!/usr/bin/env python
import os
import sys
import argparse

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database.session import SessionLocal, init_db
from backend.app.evaluation.reports import ExperimentReporter

def main():
    parser = argparse.ArgumentParser(description="Compare evaluation experiments")
    parser.add_argument("--ids", nargs="*", default=None, help="List of experiment IDs to compare")
    parser.add_argument("--output-markdown", default="evaluation/reports/comparison.md", help="Output markdown path")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()

    comparison = ExperimentReporter.compare_experiments(db=db, experiment_ids=args.ids)
    md_report = ExperimentReporter.generate_markdown_report(comparison)

    print("\n=== Experiment Comparison Report ===\n")
    print(md_report)

    if args.output_markdown:
        os.makedirs(os.path.dirname(args.output_markdown), exist_ok=True)
        with open(args.output_markdown, "w", encoding="utf-8") as f:
            f.write(md_report)
        print(f"\nMarkdown comparison written to: {args.output_markdown}")

    db.close()

if __name__ == "__main__":
    main()

