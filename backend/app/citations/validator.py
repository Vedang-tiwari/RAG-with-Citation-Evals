import re
from typing import List, Dict, Any, Tuple

class CitationValidator:
    @staticmethod
    def validate_quote_in_passage(quoted_text: str, passage_content: str) -> Tuple[bool, float]:
        """
        Validates whether the quoted text exists in the passage content.
        Returns (is_supported, match_score).
        """
        if not quoted_text or not passage_content:
            return False, 0.0

        q_clean = " ".join(quoted_text.lower().split())
        p_clean = " ".join(passage_content.lower().split())

        # Exact substring match
        if q_clean in p_clean:
            return True, 1.0

        # Word overlap match for slightly paraphrased quotes
        q_words = set(re.findall(r"\b\w+\b", q_clean))
        p_words = set(re.findall(r"\b\w+\b", p_clean))

        if not q_words:
            return False, 0.0

        overlap = len(q_words.intersection(p_words)) / len(q_words)
        is_supported = overlap >= 0.7
        return is_supported, round(overlap, 3)

    @classmethod
    def validate_citations(cls, resolved_citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validates a list of resolved citations.
        Marks `is_valid` as False if the source does not exist or the quote is completely hallucinated.
        """
        validated = []
        for cit in resolved_citations:
            item = cit.copy()
            if not item.get("is_valid", False) or not item.get("passage_content"):
                item["is_valid"] = False
                item["confidence_score"] = 0.0
            else:
                quoted = item.get("quoted_text")
                if quoted:
                    supported, score = cls.validate_quote_in_passage(quoted, item["passage_content"])
                    item["is_valid"] = supported
                    item["confidence_score"] = score
                else:
                    # Source exists, no explicit quote given
                    item["is_valid"] = True
                    item["confidence_score"] = 0.85
            validated.append(item)
        return validated

