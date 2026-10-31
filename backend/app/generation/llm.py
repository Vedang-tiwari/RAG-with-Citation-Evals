import json
import os
import re
import time
from typing import Dict, Any, List, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.generation.prompt import PromptBuilder

class LLMClient:
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = (provider or settings.LLM_PROVIDER).lower()
        self.model = model

    def generate(
        self,
        query: str,
        passages: List[Dict[str, Any]],
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Generates an evidence-backed answer formatted as JSON.
        Returns dict with keys: 'answer', 'citations', 'insufficient_evidence', 'tokens_used'.
        """
        if not passages:
            return {
                "answer": "I do not have sufficient information in the provided documents to answer this question.",
                "citations": [],
                "insufficient_evidence": True,
                "tokens_used": 0
            }

        prompt = PromptBuilder.build_user_prompt(query, passages)
        sys_prompt = PromptBuilder.SYSTEM_INSTRUCTION

        # Decide provider
        if self.provider == "gemini" and settings.GEMINI_API_KEY:
            try:
                return self._call_gemini(sys_prompt, prompt, temperature)
            except Exception as e:
                logger.warning(f"Gemini API call failed ({e}). Falling back to heuristic generator.")
        elif self.provider == "openai" and settings.OPENAI_API_KEY:
            try:
                return self._call_openai(sys_prompt, prompt, temperature)
            except Exception as e:
                logger.warning(f"OpenAI API call failed ({e}). Falling back to heuristic generator.")
        elif self.provider == "groq" and settings.GROQ_API_KEY:
            try:
                return self._call_groq(sys_prompt, prompt, temperature)
            except Exception as e:
                logger.warning(f"Groq API call failed ({e}). Falling back to heuristic generator.")

        # Heuristic offline generator for reliable testing without external keys
        return self._heuristic_generate(query, passages)

    def _call_gemini(self, system_instruction: str, user_prompt: str, temperature: float) -> Dict[str, Any]:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model_name = self.model or settings.GEMINI_MODEL
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction,
            generation_config={"temperature": temperature, "response_mime_type": "application/json"}
        )
        response = model.generate_content(user_prompt)
        parsed = json.loads(response.text)
        tokens_used = getattr(response.usage_metadata, "total_token_count", 0) if hasattr(response, "usage_metadata") else 0
        parsed["tokens_used"] = tokens_used
        return parsed

    def _call_openai(self, system_instruction: str, user_prompt: str, temperature: float) -> Dict[str, Any]:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        model_name = self.model or settings.OPENAI_MODEL
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=temperature
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        tokens_used = response.usage.total_tokens if response.usage else 0
        parsed["tokens_used"] = tokens_used
        return parsed

    def _call_groq(self, system_instruction: str, user_prompt: str, temperature: float) -> Dict[str, Any]:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.GROQ_API_KEY
        )
        model_name = self.model or settings.GROQ_MODEL
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=temperature
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        tokens_used = response.usage.total_tokens if response.usage else 0
        parsed["tokens_used"] = tokens_used
        return parsed

    def _heuristic_generate(self, query: str, passages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        High-fidelity heuristic generator:
        Matches query terms to passage sentences, constructs grounded answer with citations.
        """
        query_words = set(re.findall(r"\b\w+\b", query.lower())) - {"what", "is", "the", "a", "an", "how", "why", "in", "of", "and", "to"}
        
        selected_sentences = []
        citations = []
        
        for p in passages:
            source_id = p.get("source_id", "S1")
            content = p.get("content", "")
            # Split into sentences
            sentences = re.split(r"(?<=[.!?]) +", content)
            
            for s in sentences:
                s_clean = s.strip()
                if not s_clean:
                    continue
                s_words = set(re.findall(r"\b\w+\b", s_clean.lower()))
                overlap = len(query_words.intersection(s_words))
                if overlap > 0:
                    selected_sentences.append((overlap, s_clean, source_id, p))

        if not selected_sentences:
            # Check if any passage has content at all
            if passages:
                top_p = passages[0]
                first_sent = re.split(r"(?<=[.!?]) +", top_p["content"])[0]
                return {
                    "answer": f"According to the documentation, {first_sent.strip()} [{top_p['source_id']}].",
                    "citations": [
                        {
                            "source_id": top_p["source_id"],
                            "quoted_text": first_sent.strip()
                        }
                    ],
                    "insufficient_evidence": False,
                    "tokens_used": 150
                }
            return {
                "answer": "The provided documents do not contain sufficient evidence to answer this question.",
                "citations": [],
                "insufficient_evidence": True,
                "tokens_used": 50
            }

        # Sort sentences by keyword relevance
        selected_sentences.sort(key=lambda x: x[0], reverse=True)
        top_sentences = selected_sentences[:3]

        answer_parts = []
        for _, sent, src_id, passage in top_sentences:
            answer_parts.append(f"{sent} [{src_id}]")
            citations.append({
                "source_id": src_id,
                "quoted_text": sent
            })

        answer_text = " ".join(answer_parts)
        approx_tokens = int(len(answer_text.split()) * 1.3) + 120

        return {
            "answer": answer_text,
            "citations": citations,
            "insufficient_evidence": False,
            "tokens_used": approx_tokens
        }

