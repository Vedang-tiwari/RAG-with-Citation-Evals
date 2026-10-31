import math
from typing import List, Set, Any

class RetrievalEvaluator:
    @staticmethod
    def precision_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
        if k <= 0:
            return 0.0
        top_k = retrieved_ids[:k]
        hits = sum(1 for item in top_k if item in relevant_ids)
        return round(hits / k, 4)

    @staticmethod
    def recall_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
        if not relevant_ids:
            return 1.0
        top_k = retrieved_ids[:k]
        hits = sum(1 for item in top_k if item in relevant_ids)
        return round(hits / len(relevant_ids), 4)

    @staticmethod
    def mrr(retrieved_ids: List[str], relevant_ids: Set[str]) -> float:
        """
        Mean Reciprocal Rank for a single query.
        """
        for rank, item in enumerate(retrieved_ids, 1):
            if item in relevant_ids:
                return round(1.0 / rank, 4)
        return 0.0

    @staticmethod
    def hit_rate_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
        top_k = retrieved_ids[:k]
        return 1.0 if any(item in relevant_ids for item in top_k) else 0.0

    @staticmethod
    def ndcg_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
        """
        Normalized Discounted Cumulative Gain at K (binary relevance).
        """
        if not relevant_ids or k <= 0:
            return 0.0

        top_k = retrieved_ids[:k]
        dcg = 0.0
        for i, item in enumerate(top_k):
            rel = 1.0 if item in relevant_ids else 0.0
            dcg += rel / math.log2(i + 2)

        # Ideal DCG
        ideal_hits = min(k, len(relevant_ids))
        idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))
        if idcg == 0.0:
            return 0.0
        return round(dcg / idcg, 4)

