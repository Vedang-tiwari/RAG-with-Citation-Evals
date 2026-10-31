import re
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from backend.app.core.logging import logger

class BM25SearchEngine:
    def __init__(self):
        self.corpus: List[Dict[str, Any]] = []
        self.tokenized_corpus: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None

    def tokenize(self, text: str) -> List[str]:
        # Lowercase and split into words
        return re.findall(r"\b\w+\b", text.lower())

    def index_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Indexes or refreshes the BM25 search corpus.
        Each chunk item should have: chunk_id, document_id, document_name, page_number, content.
        """
        self.corpus = chunks
        self.tokenized_corpus = [self.tokenize(c["content"]) for c in chunks]
        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)
            logger.info(f"BM25 index built with {len(self.corpus)} chunks")
        else:
            self.bm25 = None

    def add_chunks(self, new_chunks: List[Dict[str, Any]]):
        self.corpus.extend(new_chunks)
        self.tokenized_corpus = [self.tokenize(c["content"]) for c in self.corpus]
        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)

    def remove_document(self, document_id: str):
        self.corpus = [c for c in self.corpus if c.get("document_id") != document_id]
        self.tokenized_corpus = [self.tokenize(c["content"]) for c in self.corpus]
        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)
        else:
            self.bm25 = None

    def search(self, query: str, top_k: int = 10, doc_id_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.bm25 or not self.corpus:
            return []

        tokenized_query = self.tokenize(query)
        if not tokenized_query:
            return []

        scores = self.bm25.get_scores(tokenized_query)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        results = []
        for idx in ranked_indices:
            score = float(scores[idx])
            if score <= 0.0:
                continue

            item = self.corpus[idx]
            if doc_id_filter and item.get("document_id") != doc_id_filter:
                continue

            results.append({
                "chunk_id": item["chunk_id"],
                "document_id": item["document_id"],
                "document_name": item.get("document_name", ""),
                "page_number": item.get("page_number"),
                "content": item["content"],
                "bm25_score": score
            })

            if len(results) >= top_k:
                break

        return results

bm25_engine = BM25SearchEngine()

