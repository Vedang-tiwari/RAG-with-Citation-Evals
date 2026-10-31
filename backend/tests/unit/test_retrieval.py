import pytest
from backend.app.retrieval.bm25_search import BM25SearchEngine
from backend.app.retrieval.fusion import ReciprocalRankFusion
from backend.app.retrieval.reranker import CrossEncoderReranker

def test_bm25_search():
    engine = BM25SearchEngine()
    chunks = [
        {"chunk_id": "c1", "document_id": "d1", "document_name": "doc1.txt", "content": "Transformer architecture relies on self-attention mechanisms."},
        {"chunk_id": "c2", "document_id": "d1", "document_name": "doc1.txt", "content": "Convolutional networks are used primarily for computer vision tasks."},
        {"chunk_id": "c3", "document_id": "d2", "document_name": "doc2.txt", "content": "Multi-head attention combines several attention heads."}
    ]
    engine.index_chunks(chunks)

    results = engine.search("self-attention transformer", top_k=2)
    assert len(results) > 0
    assert results[0]["chunk_id"] == "c1"

def test_reciprocal_rank_fusion():
    dense_results = [
        {"chunk_id": "c1", "similarity_score": 0.95},
        {"chunk_id": "c2", "similarity_score": 0.85},
        {"chunk_id": "c3", "similarity_score": 0.75}
    ]
    sparse_results = [
        {"chunk_id": "c2", "bm25_score": 5.4},
        {"chunk_id": "c1", "bm25_score": 3.2},
        {"chunk_id": "c4", "bm25_score": 2.1}
    ]

    fused = ReciprocalRankFusion.fuse(dense_results, sparse_results, k=60)
    assert len(fused) == 4
    # c1 and c2 appear in both, so they should be at the top
    top_ids = [f["chunk_id"] for f in fused[:2]]
    assert "c1" in top_ids
    assert "c2" in top_ids

def test_heuristic_reranker():
    reranker = CrossEncoderReranker()
    passages = [
        {"chunk_id": "p1", "content": "Apples and oranges are healthy fruits.", "similarity_score": 0.7},
        {"chunk_id": "p2", "content": "Self-attention powers the modern Transformer model.", "similarity_score": 0.8}
    ]
    reranked = reranker.rerank(query="Transformer self-attention", passages=passages, top_k=2)
    assert len(reranked) == 2
    assert reranked[0]["chunk_id"] == "p2"

