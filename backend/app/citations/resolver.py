import re
from typing import List, Dict, Any, Optional

class CitationResolver:
    @staticmethod
    def extract_inline_citations(text: str) -> List[str]:
        """
        Extracts citations from text such as [S1], [S2].
        """
        return re.findall(r"\[(S\d+)\]", text)

    @classmethod
    def resolve_citations(
        cls,
        citations: List[Dict[str, Any]],
        inline_sources: List[str],
        retrieved_passages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Maps source IDs to actual retrieved passage objects, resolving document_id, chunk_id, etc.
        """
        passage_map = {p["source_id"]: p for p in retrieved_passages if "source_id" in p}

        # Combine structured citations with any inline [S#] mentions
        resolved = []
        seen_sources = set()

        # First resolve structured citations
        for cit in citations:
            src_id = cit.get("source_id", "").strip("[]")
            if not src_id:
                continue

            passage = passage_map.get(src_id)
            if passage:
                resolved.append({
                    "source_id": src_id,
                    "document_id": passage.get("document_id"),
                    "document_name": passage.get("document_name"),
                    "chunk_id": passage.get("chunk_id"),
                    "page_number": passage.get("page_number"),
                    "quoted_text": cit.get("quoted_text"),
                    "is_valid": True,
                    "passage_content": passage.get("content")
                })
            else:
                # Hallucinated or non-existent source
                resolved.append({
                    "source_id": src_id,
                    "document_id": None,
                    "document_name": None,
                    "chunk_id": None,
                    "page_number": None,
                    "quoted_text": cit.get("quoted_text"),
                    "is_valid": False,
                    "passage_content": None
                })
            seen_sources.add(src_id)

        # Check any inline citations that weren't in the structured list
        for src_id in inline_sources:
            if src_id not in seen_sources:
                passage = passage_map.get(src_id)
                resolved.append({
                    "source_id": src_id,
                    "document_id": passage.get("document_id") if passage else None,
                    "document_name": passage.get("document_name") if passage else None,
                    "chunk_id": passage.get("chunk_id") if passage else None,
                    "page_number": passage.get("page_number") if passage else None,
                    "quoted_text": None,
                    "is_valid": passage is not None,
                    "passage_content": passage.get("content") if passage else None
                })
                seen_sources.add(src_id)

        return resolved

