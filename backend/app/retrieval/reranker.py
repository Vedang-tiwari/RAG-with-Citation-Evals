from typing import List, Dict, Any, Tuple
from backend.app.core.config import settings
from backend.app.core.logging import logger

class CrossEncoderReranker:
    _model = None
    _model_name = None

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.DEFAULT_RERANKER_MODEL

    def _load_model(self):
        if CrossEncoderReranker._model is None or CrossEncoderReranker._model_name != self.model_name:
            try:
                from sentence_transformers import CrossEncoder
                logger.info(f"Loading Cross-Encoder reranker: {self.model_name}")
                CrossEncoderReranker._model = CrossEncoder(self.model_name)
                CrossEncoderReranker._model_name = self.model_name
            except Exception as e:
                logger.warning(f"Could not load CrossEncoder ({e}). Using heuristic reranking.")
                CrossEncoderReranker._model = "fallback"
                CrossEncoderReranker._model_name = "fallback"

    def rerank(self, query: str, passages: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        if not passages:
            return []

        self._load_model()

        if CrossEncoderReranker._model != "fallback" and CrossEncoderReranker._model is not None:
            try:
                pairs = [[query, p["content"]] for p in passages]
                scores = CrossEncoderReranker._model.predict(pairs)
                for idx, score in enumerate(scores):
                    # Convert to sigmoid / 0-1 scale float
                    passages[idx]["rerank_score"] = float(score)
                    passages[idx]["final_score"] = float(score)

                sorted_passages = sorted(passages, key=lambda x: x["rerank_score"], reverse=True)
                return sorted_passages[:top_k]
            except Exception as e:
                logger.warning(f"Error during CrossEncoder predict: {e}")

        # Heuristic reranking: combination of term overlap + fused score
        query_words = set(query.lower().split())
        for p in passages:
            content_words = set(p["content"].lower().split())
            overlap = len(query_words.intersection(content_words)) / max(1, len(query_words))
            base_score = p.get("fused_score") or p.get("similarity_score") or 0.5
            p["rerank_score"] = round(0.5 * base_score + 0.5 * overlap, 4)
            p["final_score"] = p["rerank_score"]

        sorted_passages = sorted(passages, key=lambda x: x["rerank_score"], reverse=True)
        return sorted_passages[:top_k]

reranker = CrossEncoderReranker()

