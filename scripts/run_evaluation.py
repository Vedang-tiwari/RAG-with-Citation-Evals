#!/usr/bin/env python
import os
import sys
import argparse
import json

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database.session import SessionLocal, init_db
from backend.app.evaluation.runner import EvaluationRunner

def main():
    parser = argparse.ArgumentParser(description="Execute automated RAG evaluation pipeline")
    parser.add_argument("--name", default="Benchmark Evaluation Run", help="Name of experiment")
    parser.add_argument("--strategy", choices=["hybrid", "dense", "sparse"], default="hybrid", help="Retrieval strategy")
    parser.add_argument("--top-k", type=int, default=5, help="Top K retrieval count")
    parser.add_argument("--no-rerank", action="store_true", help="Disable cross-encoder reranking")
    parser.add_argument("--dataset", default=None, help="Path to evaluation questions.json")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()

    print(f"=== Starting RAG Evaluation: {args.name} ===")
    print(f"Strategy: {args.strategy} | Top-K: {args.top_k} | Rerank: {not args.no_rerank}")

    try:
        report = EvaluationRunner.run_experiment(
            db=db,
            name=args.name,
            retrieval_strategy=args.strategy,
            top_k=args.top_k,
            rerank=not args.no_rerank,
            dataset_path=args.dataset
        )

        print("\n=== Evaluation Results Summary ===")
        print(f"Experiment ID: {report['experiment_id']}")
        for metric, val in report["metrics"].items():
            print(f"  {metric:22s}: {val}")

        out_dir = "evaluation/reports"
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, f"experiment_{report['experiment_id'][:8]}.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\nFull report saved to: {out_file}")

    except Exception as e:
        print(f"Evaluation error: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()

