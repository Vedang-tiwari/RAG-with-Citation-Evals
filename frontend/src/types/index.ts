export interface DocumentItem {
  id: string;
  filename: string;
  file_hash: string;
  file_type: string;
  file_size: number;
  status: 'pending' | 'processing' | 'indexed' | 'error';
  error_message?: string;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface CitationDetail {
  source_id: string;
  document_id?: string;
  document_name?: string;
  chunk_id?: string;
  page_number?: number;
  quoted_text?: string;
  is_valid: boolean;
  confidence_score?: number;
}

export interface RetrievedPassage {
  source_id: string;
  chunk_id: string;
  document_id: string;
  document_name: string;
  page_number?: number;
  content: string;
  similarity_score: number;
  bm25_score?: number;
  rerank_score?: number;
  final_score: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: CitationDetail[];
  retrieved_passages?: RetrievedPassage[];
  insufficient_evidence?: boolean;
  citation_precision?: number;
  citation_coverage?: number;
  citation_validity?: number;
  latency_ms?: number;
  tokens_used?: number;
}

export interface EvaluationMetricResult {
  metric_name: string;
  metric_value: number;
  sample_count: number;
}

export interface EvaluationExperiment {
  id: string;
  name: string;
  configuration: Record<string, any>;
  embedding_model: string;
  llm_model: string;
  status: string;
  created_at: string;
  results: EvaluationMetricResult[];
}

export interface ExperimentComparison {
  experiments: EvaluationExperiment[];
  metrics_summary: Record<string, Record<string, number>>;
}

