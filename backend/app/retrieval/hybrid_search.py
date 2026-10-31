from typing import List, Dict, Any, Optional
from backend.app.embeddings.embedder import embedder
from backend.app.retrieval.vector_search import vector_engine
from backend.app.retrieval.bm25_search import bm25_engine
from backend.app.retrieval.fusion import ReciprocalRankFusion
from backend.app.retrieval.reranker import reranker
from backend.app.core.config import settings

class HybridRetrievalPipeline:
    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        final_top_k: int = 5,
        strategy: str = "hybrid",
        apply_rerank: bool = True,
        doc_id_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes query retrieval using the specified strategy:
        - "dense": vector search only
        - "sparse": BM25 search only
        - "hybrid": dense + BM25 combined via Reciprocal Rank Fusion
        Applies cross-encoder reranker if enabled.
        Assigns source_id tags (S1, S2, ...) for citation grounding.
        """
        results: List[Dict[str, Any]] = []

        if strategy in ["dense", "hybrid"]:
            query_vector = embedder.embed_query(query)
            dense_results = vector_engine.search(query_vector, top_k=top_k, doc_id_filter=doc_id_filter)
        else:
            dense_results = []

        if strategy in ["sparse", "hybrid"]:
            sparse_results = bm25_engine.search(query, top_k=top_k, doc_id_filter=doc_id_filter)
        else:
            sparse_results = []

        if strategy == "hybrid":
            results = ReciprocalRankFusion.fuse(
                dense_results=dense_results,
                sparse_results=sparse_results,
                dense_weight=settings.DENSE_WEIGHT,
                sparse_weight=settings.SPARSE_WEIGHT
            )
        elif strategy == "dense":
            for r in dense_results:
                r["final_score"] = r.get("similarity_score", 0.0)
            results = dense_results
        elif strategy == "sparse":
            for r in sparse_results:
                r["final_score"] = r.get("bm25_score", 0.0)
            results = sparse_results

        # Apply reranking if requested
        if apply_rerank and results:
            results = reranker.rerank(query, results, top_k=final_top_k)
        else:
            results = results[:final_top_k]

        # Assign unique source identifiers [S1], [S2], ...
        for idx, item in enumerate(results):
            item["source_id"] = f"S{idx + 1}"
            if "final_score" not in item:
                item["final_score"] = item.get("fused_score") or item.get("similarity_score") or 0.0

        return results

retrieval_pipeline = HybridRetrievalPipeline()

