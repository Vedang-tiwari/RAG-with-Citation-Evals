import pytest
from backend.app.citations.resolver import CitationResolver
from backend.app.citations.validator import CitationValidator
from backend.app.citations.metrics import CitationMetricsCalculator

def test_extract_inline_citations():
    text = "Multi-head attention uses multiple heads [S1] and self-attention computes dot products [S2]."
    tags = CitationResolver.extract_inline_citations(text)
    assert tags == ["S1", "S2"]

def test_resolve_citations():
    retrieved = [
        {"source_id": "S1", "chunk_id": "c_1", "document_id": "d_1", "document_name": "paper.pdf", "page_number": 3, "content": "Attention is all you need."}
    ]
    citations = [{"source_id": "S1", "quoted_text": "Attention is all you need."}]
    resolved = CitationResolver.resolve_citations(citations, ["S1"], retrieved)
    assert len(resolved) == 1
    assert resolved[0]["is_valid"] is True
    assert resolved[0]["document_name"] == "paper.pdf"
    assert resolved[0]["chunk_id"] == "c_1"

def test_validate_quote_in_passage():
    passage = "Self-attention allows each position in a sequence to attend to other positions."
    supported, score = CitationValidator.validate_quote_in_passage(
        quoted_text="attend to other positions",
        passage_content=passage
    )
    assert supported is True
    assert score == 1.0

    unsupported, score2 = CitationValidator.validate_quote_in_passage(
        quoted_text="completely unrelated hallucinated statement",
        passage_content=passage
    )
    assert unsupported is False
    assert score2 < 0.5

def test_citation_metrics_calculator():
    answer = "Transformers rely on attention [S1]. They process tokens concurrently [S2]."
    citations = [
        {"source_id": "S1", "is_valid": True, "confidence_score": 0.95},
        {"source_id": "S2", "is_valid": True, "confidence_score": 0.90}
    ]
    metrics = CitationMetricsCalculator.calculate_metrics(answer, citations)
    assert metrics["citation_validity"] == 1.0
    assert metrics["citation_precision"] == 1.0
    assert metrics["citation_coverage"] == 1.0

