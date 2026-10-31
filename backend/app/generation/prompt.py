import json
from typing import List, Dict, Any

class PromptBuilder:
    SYSTEM_INSTRUCTION = """You are a reliable, citation-grounded AI research assistant.
Your task is to answer the user's question accurately using ONLY the provided evidence passages.

CRITICAL RULES:
1. Base your answer strictly and exclusively on the provided evidence passages. Do not extrapolate, hallucinate, or rely on external facts.
2. Every factual statement or claim MUST be immediately followed by a citation tag corresponding to the source passage, e.g. [S1] or [S2].
3. Multiple sources can be cited together, e.g. [S1][S2].
4. If the provided evidence does not contain sufficient facts to answer the question reliably, you MUST explicitly state that the evidence is insufficient and set "insufficient_evidence": true.
5. You must return your answer formatted strictly as a valid JSON object matching the following structure:
{
  "answer": "Your comprehensive answer with citation tags like [S1] inline.",
  "citations": [
    {
      "source_id": "S1",
      "quoted_text": "Exact text or key snippet from passage S1 that supports this claim."
    }
  ],
  "insufficient_evidence": false
}
Do not include any conversational filler outside of the JSON object.
"""

    @staticmethod
    def build_evidence_context(passages: List[Dict[str, Any]]) -> str:
        """
        Formats retrieved passages into the standardized evidence block:
        [S1] Source: document.pdf, Page: 12
        Content: ...
        """
        context_parts = []
        for p in passages:
            source_id = p.get("source_id", "S1")
            doc_name = p.get("document_name", "Unknown Document")
            page_num = p.get("page_number", "N/A")
            content = p.get("content", "")

            context_parts.append(
                f"[{source_id}] Source: {doc_name}, Page: {page_num}\nContent: {content}"
            )
        return "\n\n".join(context_parts)

    @classmethod
    def build_user_prompt(cls, query: str, passages: List[Dict[str, Any]]) -> str:
        evidence_block = cls.build_evidence_context(passages)
        return f"""EVIDENCE PASSAGES:
{evidence_block}

USER QUESTION:
{query}

Remember to return ONLY valid JSON with inline citations [S1], [S2] and populate the citations list."""

