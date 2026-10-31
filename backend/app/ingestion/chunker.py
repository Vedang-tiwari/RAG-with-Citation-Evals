from typing import List, Dict, Any, Tuple

class ConfigurableChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        """
        chunk_size: approximate number of tokens / words per chunk
        chunk_overlap: overlap between contiguous chunks
        """
        self.chunk_size = max(50, chunk_size)
        self.chunk_overlap = max(0, min(chunk_overlap, chunk_size - 10))

    def split_text_into_chunks(
        self,
        doc_id: str,
        pages_content: List[Tuple[int, str]]
    ) -> List[Dict[str, Any]]:
        """
        Splits page contents into chunks while tracking page numbers.
        """
        chunks: List[Dict[str, Any]] = []
        chunk_index = 0

        for page_num, page_text in pages_content:
            words = page_text.split()
            if not words:
                continue

            step = self.chunk_size - self.chunk_overlap
            for start_idx in range(0, len(words), step):
                end_idx = min(start_idx + self.chunk_size, len(words))
                chunk_words = words[start_idx:end_idx]
                chunk_text = " ".join(chunk_words)

                if len(chunk_words) < 5 and chunks:
                    # Append very tiny trailing fragments to the previous chunk
                    chunks[-1]["content"] += " " + chunk_text
                    chunks[-1]["token_count"] = int(len(chunks[-1]["content"].split()) * 1.3)
                    continue

                chunk_id = f"{doc_id}_c{chunk_index}"
                approx_tokens = int(len(chunk_words) * 1.3)

                chunks.append({
                    "id": chunk_id,
                    "document_id": doc_id,
                    "chunk_index": chunk_index,
                    "content": chunk_text,
                    "page_number": page_num,
                    "token_count": approx_tokens,
                    "meta_info": {
                        "word_count": len(chunk_words),
                        "start_word_index": start_idx,
                        "end_word_index": end_idx
                    }
                })
                chunk_index += 1

                if end_idx >= len(words):
                    break

        return chunks

