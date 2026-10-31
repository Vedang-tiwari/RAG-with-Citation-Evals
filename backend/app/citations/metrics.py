import re
from typing import List, Dict, Any

class CitationMetricsCalculator:
    @staticmethod
    def calculate_metrics(
        answer: str,
        citations: List[Dict[str, Any]],
        ground_truth_sources: List[str] = None
    ) -> Dict[str, float]:
        """
        Computes citation metrics:
        - citation_validity: percentage of citations that map to valid retrieved chunks
        - citation_precision: percentage of citations verified as supportive
        - citation_coverage: percentage of answer sentences containing citation tags
        - citation_recall: percentage of ground truth sources cited (if ground_truth_sources provided)
        """
        if not citations:
            return {
                "citation_validity": 0.0 if re.findall(r"\[S\d+\]", answer) else 1.0,
                "citation_precision": 0.0,
                "citation_coverage": 0.0,
                "citation_recall": 0.0
            }

        total_citations = len(citations)
        valid_count = sum(1 for c in citations if c.get("is_valid", False))
        support_count = sum(1 for c in citations if c.get("confidence_score", 0.0) >= 0.7)

        citation_validity = valid_count / total_citations if total_citations > 0 else 1.0
        citation_precision = support_count / total_citations if total_citations > 0 else 0.0

        # Calculate coverage over sentences
        sentences = [s.strip() for s in re.split(r"[.!?]\s+", answer) if len(s.strip()) > 5]
        if sentences:
            cited_sentences = sum(1 for s in sentences if re.search(r"\[S\d+\]", s))
            citation_coverage = cited_sentences / len(sentences)
        else:
            citation_coverage = 1.0 if citations else 0.0

        # Calculate citation recall if ground truth sources provided
        citation_recall = 1.0
        if ground_truth_sources:
            cited_source_ids = {c.get("chunk_id") or c.get("source_id") for c in citations}
            matched_gt = sum(1 for gt in ground_truth_sources if gt in cited_source_ids)
            citation_recall = matched_gt / len(ground_truth_sources) if ground_truth_sources else 1.0

        return {
            "citation_validity": round(citation_validity, 4),
            "citation_precision": round(citation_precision, 4),
            "citation_coverage": round(citation_coverage, 4),
            "citation_recall": round(citation_recall, 4)
        }

