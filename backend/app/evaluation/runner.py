import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.evaluation.dataset import DatasetLoader
from backend.app.evaluation.retrieval_eval import RetrievalEvaluator
from backend.app.evaluation.generation_eval import GenerationEvaluator
from backend.app.citations.metrics import CitationMetricsCalculator
from backend.app.retrieval.hybrid_search import retrieval_pipeline
from backend.app.generation.rag_pipeline import RAGPipeline
from backend.app.database.repository import EvaluationRepository

class EvaluationRunner:
    @classmethod
    def run_experiment(
        cls,
        db: Session,
        name: str = "Benchmark Evaluation",
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        retrieval_strategy: str = "hybrid",
        top_k: int = 5,
        rerank: bool = True,
        embedding_model: Optional[str] = None,
        llm_model: Optional[str] = None,
        dataset_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Runs automated evaluation over a dataset and records metrics.
        """
        dataset = DatasetLoader.load_dataset(dataset_path)
        if not dataset:
            raise ValueError("Evaluation dataset is empty.")

        emb_name = embedding_model or settings.DEFAULT_EMBEDDING_MODEL
        llm_name = llm_model or settings.LLM_PROVIDER

        config = {
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "retrieval_strategy": retrieval_strategy,
            "top_k": top_k,
            "rerank": rerank,
            "embedding_model": emb_name,
            "llm_model": llm_name,
            "sample_count": len(dataset)
        }

        # Create experiment in DB
        exp = EvaluationRepository.create_experiment(
            db=db,
            name=name,
            configuration=config,
            embedding_model=emb_name,
            llm_model=llm_name
        )

        pipeline = RAGPipeline(llm_provider=settings.LLM_PROVIDER, llm_model=llm_name)

        # Accumulators
        p_at_k_list = []
        r_at_k_list = []
        mrr_list = []
        ndcg_list = []
        hit_rate_list = []

        faithfulness_list = []
        relevancy_list = []
        correctness_list = []
        context_recall_list = []

        cit_precision_list = []
        cit_recall_list = []
        cit_coverage_list = []
        cit_validity_list = []

        latencies = []
        tokens_list = []

        sample_details = []

        for sample in dataset:
            query = sample["question"]
            gt = sample.get("ground_truth", "")
            rel_docs = set(sample.get("relevant_documents", []))
            rel_chunks = set(sample.get("relevant_chunks", []))
            # Targets for retrieval match
            targets = rel_chunks if rel_chunks else rel_docs

            start_t = time.time()
            res = pipeline.answer_query(
                db=db,
                query=query,
                top_k=top_k,
                retrieval_strategy=retrieval_strategy,
                rerank=rerank
            )
            lat = (time.time() - start_t) * 1000
            latencies.append(lat)
            tokens_list.append(res.get("tokens_used", 0))

            # Retrieved chunk IDs and doc names
            retrieved = res.get("retrieved_passages", [])
            ret_ids = [p.get("chunk_id") for p in retrieved]
            ret_doc_names = [p.get("document_name") for p in retrieved]
            ret_check_set = set(ret_ids).union(set(ret_doc_names))

            # 1. Retrieval Metrics
            p_k = RetrievalEvaluator.precision_at_k(ret_ids, targets, k=top_k)
            r_k = RetrievalEvaluator.recall_at_k(ret_ids, targets, k=top_k)
            # If chunk IDs didn't match directly, fall back to doc names
            if p_k == 0.0 and rel_docs:
                p_k = RetrievalEvaluator.precision_at_k(ret_doc_names, rel_docs, k=top_k)
                r_k = RetrievalEvaluator.recall_at_k(ret_doc_names, rel_docs, k=top_k)

            mrr_val = RetrievalEvaluator.mrr(ret_ids, targets)
            if mrr_val == 0.0 and rel_docs:
                mrr_val = RetrievalEvaluator.mrr(ret_doc_names, rel_docs)

            ndcg_val = RetrievalEvaluator.ndcg_at_k(ret_ids, targets, k=top_k)
            hit_val = RetrievalEvaluator.hit_rate_at_k(ret_ids, targets, k=top_k)
            if hit_val == 0.0 and rel_docs:
                hit_val = RetrievalEvaluator.hit_rate_at_k(ret_doc_names, rel_docs, k=top_k)

            p_at_k_list.append(p_k)
            r_at_k_list.append(r_k)
            mrr_list.append(mrr_val)
            ndcg_list.append(ndcg_val)
            hit_rate_list.append(hit_val)

            # 2. Generation Metrics
            ctx_texts = [p.get("content", "") for p in retrieved]
            faith = GenerationEvaluator.calculate_faithfulness(res["answer"], ctx_texts)
            rel = GenerationEvaluator.calculate_answer_relevancy(query, res["answer"])
            corr = GenerationEvaluator.calculate_answer_correctness(res["answer"], gt)
            ctx_rec = GenerationEvaluator.calculate_context_recall(gt, ctx_texts)

            faithfulness_list.append(faith)
            relevancy_list.append(rel)
            correctness_list.append(corr)
            context_recall_list.append(ctx_rec)

            # 3. Citation Metrics
            cit_prec = res.get("citation_precision", 1.0)
            cit_cov = res.get("citation_coverage", 1.0)
            cit_val = res.get("citation_validity", 1.0)

            # Target chunks for citation recall
            cit_rec_calc = CitationMetricsCalculator.calculate_metrics(
                answer=res["answer"],
                citations=res.get("citations", []),
                ground_truth_sources=list(targets)
            )

            cit_precision_list.append(cit_prec)
            cit_recall_list.append(cit_rec_calc["citation_recall"])
            cit_coverage_list.append(cit_cov)
            cit_validity_list.append(cit_val)

            sample_details.append({
                "question": query,
                "answer": res["answer"],
                "faithfulness": faith,
                "relevancy": rel,
                "citation_precision": cit_prec,
                "latency_ms": lat
            })

        def avg(lst):
            return round(sum(lst) / len(lst), 4) if lst else 0.0

        avg_latency = avg(latencies)
        avg_tokens = int(sum(tokens_list) / len(tokens_list)) if tokens_list else 0
        est_cost_per_query = round((avg_tokens / 1000) * 0.00015, 6)  # approx $0.15 / 1M tokens

        results_to_save = [
            {"metric_name": "Precision@K", "metric_value": avg(p_at_k_list), "sample_count": len(dataset)},
            {"metric_name": "Recall@K", "metric_value": avg(r_at_k_list), "sample_count": len(dataset)},
            {"metric_name": "MRR", "metric_value": avg(mrr_list), "sample_count": len(dataset)},
            {"metric_name": "NDCG@K", "metric_value": avg(ndcg_list), "sample_count": len(dataset)},
            {"metric_name": "Hit_Rate@K", "metric_value": avg(hit_rate_list), "sample_count": len(dataset)},
            {"metric_name": "Faithfulness", "metric_value": avg(faithfulness_list), "sample_count": len(dataset)},
            {"metric_name": "Answer_Relevancy", "metric_value": avg(relevancy_list), "sample_count": len(dataset)},
            {"metric_name": "Answer_Correctness", "metric_value": avg(correctness_list), "sample_count": len(dataset)},
            {"metric_name": "Context_Recall", "metric_value": avg(context_recall_list), "sample_count": len(dataset)},
            {"metric_name": "Citation_Precision", "metric_value": avg(cit_precision_list), "sample_count": len(dataset)},
            {"metric_name": "Citation_Recall", "metric_value": avg(cit_recall_list), "sample_count": len(dataset)},
            {"metric_name": "Citation_Coverage", "metric_value": avg(cit_coverage_list), "sample_count": len(dataset)},
            {"metric_name": "Citation_Validity", "metric_value": avg(cit_validity_list), "sample_count": len(dataset)},
            {"metric_name": "Avg_Latency_ms", "metric_value": avg_latency, "sample_count": len(dataset)},
            {"metric_name": "Avg_Tokens", "metric_value": float(avg_tokens), "sample_count": len(dataset)},
            {"metric_name": "Estimated_Cost_USD", "metric_value": est_cost_per_query, "sample_count": len(dataset)}
        ]

        EvaluationRepository.save_results(db=db, exp_id=exp.id, results=results_to_save)
        EvaluationRepository.complete_experiment(db=db, exp_id=exp.id)

        return {
            "experiment_id": exp.id,
            "name": name,
            "configuration": config,
            "metrics": {r["metric_name"]: r["metric_value"] for r in results_to_save},
            "sample_details": sample_details
        }

