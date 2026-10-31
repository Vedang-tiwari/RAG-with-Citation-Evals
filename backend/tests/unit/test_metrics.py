import pytest
from backend.app.evaluation.retrieval_eval import RetrievalEvaluator
from backend.app.evaluation.generation_eval import GenerationEvaluator

def test_retrieval_metrics():
    retrieved = ["c1", "c2", "c3", "c4", "c5"]
    relevant = {"c2", "c4"}

    p_at_5 = RetrievalEvaluator.precision_at_k(retrieved, relevant, k=5)
    r_at_5 = RetrievalEvaluator.recall_at_k(retrieved, relevant, k=5)
    mrr = RetrievalEvaluator.mrr(retrieved, relevant)
    hit = RetrievalEvaluator.hit_rate_at_k(retrieved, relevant, k=5)

    assert p_at_5 == 0.4
    assert r_at_5 == 1.0
    assert mrr == 0.5  # First hit is at rank 2 -> 1/2 = 0.5
    assert hit == 1.0

def test_generation_evaluator():
    context = ["Self-attention connects all pairs of input tokens in a sequence."]
    answer = "Self-attention connects input tokens in a sequence."

    faithfulness = GenerationEvaluator.calculate_faithfulness(answer, context)
    assert faithfulness >= 0.8

    relevancy = GenerationEvaluator.calculate_answer_relevancy(
        query="How does self-attention work?",
        answer=answer
    )
    assert relevancy > 0.5

    correctness = GenerationEvaluator.calculate_answer_correctness(
        answer=answer,
        ground_truth="Self-attention allows tokens to connect across sequences."
    )
    assert correctness >= 0.5

