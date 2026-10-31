from typing import List, Dict, Any

class ReciprocalRankFusion:
    @staticmethod
    def fuse(
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        k: int = 60,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4
    ) -> List[Dict[str, Any]]:
        """
        Combines dense vector search results and BM25 sparse search results using RRF.
        Returns unified list of passages sorted by fused score.
        """
        rrf_scores: Dict[str, float] = {}
        items_map: Dict[str, Dict[str, Any]] = {}

        # Process dense results
        for rank, item in enumerate(dense_results):
            chunk_id = item["chunk_id"]
            items_map[chunk_id] = item
            score = dense_weight * (1.0 / (k + rank + 1))
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + score

        # Process sparse results
        for rank, item in enumerate(sparse_results):
            chunk_id = item["chunk_id"]
            if chunk_id not in items_map:
                items_map[chunk_id] = item
            else:
                # Merge scores
                items_map[chunk_id]["bm25_score"] = item.get("bm25_score")
            score = sparse_weight * (1.0 / (k + rank + 1))
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + score

        # Sort by RRF score descending
        sorted_chunk_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        fused = []
        for cid in sorted_chunk_ids:
            res = items_map[cid].copy()
            res["fused_score"] = rrf_scores[cid]
            res["similarity_score"] = res.get("similarity_score", 0.0)
            res["bm25_score"] = res.get("bm25_score", 0.0)
            fused.append(res)

        return fused

