import time
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.retrieval.hybrid_search import retrieval_pipeline
from backend.app.generation.llm import LLMClient
from backend.app.citations.resolver import CitationResolver
from backend.app.citations.validator import CitationValidator
from backend.app.citations.metrics import CitationMetricsCalculator
from backend.app.database.repository import ChatRepository

class RAGPipeline:
    def __init__(self, llm_provider: Optional[str] = None, llm_model: Optional[str] = None):
        self.llm_client = LLMClient(provider=llm_provider, model=llm_model)

    def answer_query(
        self,
        db: Session,
        query: str,
        conversation_id: Optional[str] = None,
        top_k: Optional[int] = None,
        retrieval_strategy: Optional[str] = "hybrid",
        rerank: Optional[bool] = True,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Executes end-to-end RAG query flow:
        1. Retrieve top passages (Dense, Sparse, or Hybrid + Reranker)
        2. Assign [S1], [S2] source identifiers
        3. Call LLM with strict grounding instructions
        4. Extract and resolve citations against retrieved passages
        5. Validate citations (presence, quotation authenticity, coverage)
        6. Store conversation, message, and citation records in DB
        7. Return structured response
        """
        start_time = time.time()

        # Get or create conversation
        conv = ChatRepository.get_or_create_conversation(db, conv_id=conversation_id, title=query[:50])

        # Save user message
        ChatRepository.add_message(db, conv_id=conv.id, role="user", content=query)

        # 1. Retrieve passages
        k = top_k or settings.DEFAULT_TOP_K
        passages = retrieval_pipeline.retrieve(
            query=query,
            top_k=k,
            final_top_k=settings.DEFAULT_FINAL_TOP_K,
            strategy=retrieval_strategy or "hybrid",
            apply_rerank=rerank if rerank is not None else settings.RERANKER_ENABLED
        )

        # 2. Call LLM
        llm_output = self.llm_client.generate(query=query, passages=passages, temperature=temperature)
        answer = llm_output.get("answer", "")
        raw_citations = llm_output.get("citations", [])
        insufficient_evidence = llm_output.get("insufficient_evidence", False)
        tokens_used = llm_output.get("tokens_used", 0)

        # 3. Resolve & validate citations
        inline_sources = CitationResolver.extract_inline_citations(answer)
        resolved = CitationResolver.resolve_citations(
            citations=raw_citations,
            inline_sources=inline_sources,
            retrieved_passages=passages
        )
        validated_citations = CitationValidator.validate_citations(resolved)

        # 4. Calculate metrics
        citation_metrics = CitationMetricsCalculator.calculate_metrics(
            answer=answer,
            citations=validated_citations
        )

        latency_ms = round((time.time() - start_time) * 1000, 2)

        # 5. Save assistant message and citations in DB
        assistant_msg = ChatRepository.add_message(
            db=db,
            conv_id=conv.id,
            role="assistant",
            content=answer,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            insufficient_evidence=insufficient_evidence
        )
        ChatRepository.add_citations(db=db, message_id=assistant_msg.id, citations=validated_citations)

        return {
            "conversation_id": conv.id,
            "message_id": assistant_msg.id,
            "answer": answer,
            "citations": validated_citations,
            "retrieved_passages": passages,
            "insufficient_evidence": insufficient_evidence,
            "citation_precision": citation_metrics["citation_precision"],
            "citation_coverage": citation_metrics["citation_coverage"],
            "citation_validity": citation_metrics["citation_validity"],
            "latency_ms": latency_ms,
            "tokens_used": tokens_used
        }

rag_engine = RAGPipeline()

