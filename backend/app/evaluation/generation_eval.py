import re
from typing import List, Dict, Any, Set

class GenerationEvaluator:
    @staticmethod
    def _tokenize(text: str) -> Set[str]:
        return set(re.findall(r"\b\w+\b", text.lower()))

    @classmethod
    def calculate_faithfulness(cls, answer: str, context_passages: List[str]) -> float:
        """
        Faithfulness measures whether claims in the answer can be inferred from the context.
        Approximates ungrounded hallucination rate.
        """
        if not answer.strip() or not context_passages:
            return 0.0

        full_context = " ".join(context_passages).lower()
        context_words = cls._tokenize(full_context)
        
        sentences = [s.strip() for s in re.split(r"[.!?]\s+", answer) if len(s.strip()) > 5]
        if not sentences:
            return 1.0

        supported_sentences = 0
        for sent in sentences:
            sent_words = cls._tokenize(sent) - {"the", "is", "at", "which", "on", "a", "an", "this", "that", "in", "to", "and"}
            if not sent_words:
                supported_sentences += 1
                continue
            overlap = len(sent_words.intersection(context_words)) / len(sent_words)
            if overlap >= 0.5:
                supported_sentences += 1

        return round(supported_sentences / len(sentences), 4)

    @classmethod
    def calculate_answer_relevancy(cls, query: str, answer: str) -> float:
        """
        Answer relevancy measures how directly the answer addresses the query terms.
        """
        q_words = cls._tokenize(query) - {"what", "is", "how", "why", "where", "when", "the", "a", "an"}
        a_words = cls._tokenize(answer)
        if not q_words:
            return 1.0
        overlap = len(q_words.intersection(a_words)) / len(q_words)
        # Scale to smooth relevancy curve
        return round(min(1.0, 0.4 + 0.6 * overlap), 4)

    @classmethod
    def calculate_answer_correctness(cls, answer: str, ground_truth: str) -> float:
        """
        Calculates token F1 similarity with stemming between generated answer and ground truth.
        """
        if not ground_truth:
            return 1.0

        def stem(w: str) -> str:
            w = w.lower()
            if w.endswith("ies") and len(w) > 4: return w[:-3] + "y"
            if w.endswith("es") and len(w) > 3: return w[:-2]
            if w.endswith("s") and len(w) > 2: return w[:-1]
            if w.endswith("ing") and len(w) > 4: return w[:-3]
            if w.endswith("ed") and len(w) > 3: return w[:-2]
            return w

        a_tokens = [stem(w) for w in re.findall(r"\b\w+\b", answer.lower())]
        gt_tokens = [stem(w) for w in re.findall(r"\b\w+\b", ground_truth.lower())]

        common = set(a_tokens).intersection(set(gt_tokens))
        if not common:
            return 0.0

        prec = len(common) / len(set(a_tokens))
        rec = len(common) / len(set(gt_tokens))
        f1 = (2 * prec * rec) / (prec + rec)
        return round(f1, 4)

    @classmethod
    def calculate_context_recall(cls, ground_truth: str, context_passages: List[str]) -> float:
        """
        Context recall measures how much of the ground truth is covered by retrieved context.
        """
        if not ground_truth or not context_passages:
            return 0.0
        gt_words = cls._tokenize(ground_truth) - {"the", "is", "at", "which", "on", "a", "an", "and", "in"}
        full_context = " ".join(context_passages).lower()
        ctx_words = cls._tokenize(full_context)
        if not gt_words:
            return 1.0
        overlap = len(gt_words.intersection(ctx_words)) / len(gt_words)
        return round(overlap, 4)

