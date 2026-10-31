import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.database.repository import EvaluationRepository

class ExperimentReporter:
    @staticmethod
    def compare_experiments(db: Session, experiment_ids: List[str] = None) -> Dict[str, Any]:
        """
        Gathers experiment data and compares metrics side-by-side.
        """
        all_experiments = EvaluationRepository.list_experiments(db)
        if experiment_ids:
            experiments = [e for e in all_experiments if e.id in experiment_ids]
        else:
            experiments = all_experiments[:5]  # Latest 5

        metrics_summary: Dict[str, Dict[str, float]] = {}

        for exp in experiments:
            for res in exp.results:
                if res.metric_name not in metrics_summary:
                    metrics_summary[res.metric_name] = {}
                metrics_summary[res.metric_name][exp.id] = res.metric_value

        return {
            "experiments": [
                {
                    "id": exp.id,
                    "name": exp.name,
                    "configuration": exp.configuration,
                    "embedding_model": exp.embedding_model,
                    "llm_model": exp.llm_model,
                    "status": exp.status,
                    "created_at": exp.created_at.isoformat() if exp.created_at else None,
                    "results": [
                        {
                            "metric_name": r.metric_name,
                            "metric_value": r.metric_value,
                            "sample_count": r.sample_count
                        }
                        for r in exp.results
                    ]
                }
                for exp in experiments
            ],
            "metrics_summary": metrics_summary
        }

    @staticmethod
    def generate_markdown_report(comparison: Dict[str, Any]) -> str:
        """
        Generates markdown table comparing experiments.
        """
        experiments = comparison.get("experiments", [])
        if not experiments:
            return "No experiments recorded."

        headers = ["Metric"] + [f"{e['name']} ({e['id'][:6]})" for e in experiments]
        rows = []
        metrics_summary = comparison.get("metrics_summary", {})

        for metric_name, exp_values in metrics_summary.items():
            row = [metric_name]
            for exp in experiments:
                val = exp_values.get(exp["id"], "N/A")
                if isinstance(val, float):
                    row.append(f"{val:.4f}")
                else:
                    row.append(str(val))
            rows.append(row)

        header_line = "| " + " | ".join(headers) + " |"
        sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
        row_lines = ["| " + " | ".join(r) + " |" for r in rows]

        return "\n".join([header_line, sep_line] + row_lines)

