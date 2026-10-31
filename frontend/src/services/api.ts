import { DocumentItem, ChatMessage, EvaluationExperiment, ExperimentComparison } from '../types';

const BASE_URL = '/api';

export const api = {
  // Documents
  async listDocuments(): Promise<DocumentItem[]> {
    const res = await fetch(`${BASE_URL}/documents`);
    if (!res.ok) throw new Error('Failed to load documents');
    return res.json();
  },

  async uploadDocument(file: File): Promise<DocumentItem> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async deleteDocument(docId: string): Promise<void> {
    const res = await fetch(`${BASE_URL}/documents/${docId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete document');
  },

  async reindexDocument(docId: string, chunkSize?: number, chunkOverlap?: number): Promise<DocumentItem> {
    const res = await fetch(`${BASE_URL}/documents/${docId}/reindex`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chunk_size: chunkSize, chunk_overlap: chunkOverlap }),
    });
    if (!res.ok) throw new Error('Failed to reindex document');
    return res.json();
  },

  // Chat
  async sendQuery(payload: {
    query: string;
    conversation_id?: string;
    top_k?: number;
    retrieval_strategy?: string;
    rerank?: boolean;
    temperature?: number;
  }): Promise<any> {
    const res = await fetch(`${BASE_URL}/chat/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Query failed' }));
      throw new Error(err.detail || 'Query failed');
    }
    return res.json();
  },

  async getChatHistory(): Promise<any[]> {
    const res = await fetch(`${BASE_URL}/chat/history`);
    if (!res.ok) throw new Error('Failed to fetch chat history');
    return res.json();
  },

  // Evaluation
  async runEvaluation(payload: {
    name?: string;
    chunk_size?: number;
    chunk_overlap?: number;
    retrieval_strategy?: string;
    top_k?: number;
    rerank?: boolean;
  }): Promise<any> {
    const res = await fetch(`${BASE_URL}/evaluation/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Evaluation execution failed');
    return res.json();
  },

  async getEvaluationResults(): Promise<EvaluationExperiment[]> {
    const res = await fetch(`${BASE_URL}/evaluation/results`);
    if (!res.ok) throw new Error('Failed to fetch evaluation results');
    return res.json();
  },

  async compareExperiments(): Promise<ExperimentComparison> {
    const res = await fetch(`${BASE_URL}/experiments/compare`);
    if (!res.ok) throw new Error('Failed to fetch experiment comparison');
    return res.json();
  },
};

