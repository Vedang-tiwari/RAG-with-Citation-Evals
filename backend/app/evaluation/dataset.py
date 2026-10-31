import json
import os
from typing import List, Dict, Any

DEFAULT_BENCHMARK_DATASET = [
    {
        "question": "What is multi-head attention and why is it used?",
        "ground_truth": "Multi-head attention uses multiple attention heads to jointly attend to information from different representation subspaces at different positions.",
        "relevant_documents": ["transformer.pdf", "attention_notes.pdf"],
        "relevant_pages": [12, 5],
        "relevant_chunks": ["transformer_c1", "attention_c0"]
    },
    {
        "question": "How does self-attention compute token relationships?",
        "ground_truth": "Self-attention computes token relationships by mapping queries, keys, and values through scaled dot-product attention.",
        "relevant_documents": ["transformer.pdf"],
        "relevant_pages": [4],
        "relevant_chunks": ["transformer_c2"]
    },
    {
        "question": "What is Reciprocal Rank Fusion (RRF)?",
        "ground_truth": "Reciprocal Rank Fusion is an algorithm that combines ranking scores from multiple search systems like dense and sparse retrieval.",
        "relevant_documents": ["rag_architecture.pdf"],
        "relevant_pages": [3],
        "relevant_chunks": ["rag_c3"]
    },
    {
        "question": "Why is cross-encoder reranking beneficial after hybrid retrieval?",
        "ground_truth": "A cross-encoder reranker scores the full query and document pair together to evaluate deep semantic relevance, significantly improving top-ranking accuracy.",
        "relevant_documents": ["reranking_guide.txt"],
        "relevant_pages": [1],
        "relevant_chunks": ["rerank_c0"]
    },
    {
        "question": "How are citations validated in the RAG system?",
        "ground_truth": "Citations are validated by resolving source identifiers to indexed chunks and verifying that quoted snippets match the retrieved source text.",
        "relevant_documents": ["citations_spec.docx"],
        "relevant_pages": [2],
        "relevant_chunks": ["citation_c1"]
    }
]

class DatasetLoader:
    @staticmethod
    def load_dataset(dataset_path: str = None) -> List[Dict[str, Any]]:
        if dataset_path and os.path.exists(dataset_path):
            with open(dataset_path, "r", encoding="utf-8") as f:
                return json.load(f)
        
        # Check standard evaluation path
        std_path = "evaluation/datasets/questions.json"
        if os.path.exists(std_path):
            with open(std_path, "r", encoding="utf-8") as f:
                return json.load(f)

        return DEFAULT_BENCHMARK_DATASET

    @staticmethod
    def save_dataset(data: List[Dict[str, Any]], output_path: str):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

