import React, { useState, useEffect } from 'react';
import { Upload, FileText, Trash2, RefreshCw, CheckCircle2, AlertCircle, Clock, Database, Layers } from 'lucide-react';
import { DocumentItem } from '../types';
import { api } from '../services/api';

export const DocumentManager: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [uploading, setUploading] = useState<boolean>(false);
  const [reindexingId, setReindexingId] = useState<string | null>(null);
  const [reindexChunkSize, setReindexChunkSize] = useState<number>(500);
  const [reindexOverlap, setReindexOverlap] = useState<number>(100);
  const [showReindexModal, setShowReindexModal] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchDocs = async () => {
    try {
      setLoading(true);
      const docs = await api.listDocuments();
      setDocuments(docs);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    try {
      setUploading(true);
      setError(null);
      await api.uploadDocument(file);
      await fetchDocs();
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (docId: string) => {
    if (!confirm('Are you sure you want to delete this document from the vector store and database?')) return;
    try {
      await api.deleteDocument(docId);
      setDocuments(documents.filter((d) => d.id !== docId));
    } catch (err: any) {
      alert('Delete failed: ' + err.message);
    }
  };

  const handleReindex = async (docId: string) => {
    try {
      setReindexingId(docId);
      await api.reindexDocument(docId, reindexChunkSize, reindexOverlap);
      setShowReindexModal(null);
      await fetchDocs();
    } catch (err: any) {
      alert('Reindex failed: ' + err.message);
    } finally {
      setReindexingId(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Document Knowledge Base</h2>
          <p className="text-sm text-slate-400 mt-1">
            Upload PDF, DOCX, or TXT documents. Every document is parsed, chunked, embedded, and indexed in Qdrant & BM25.
          </p>
        </div>

        <div>
          <label className={`cursor-pointer inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all shadow-lg ${
            uploading ? 'bg-slate-700 text-slate-400 cursor-not-allowed' : 'bg-emerald-500 hover:bg-emerald-600 text-white shadow-emerald-500/20'
          }`}>
            <Upload className="w-4 h-4" />
            <span>{uploading ? 'Processing Document...' : 'Upload Document'}</span>
            <input
              type="file"
              accept=".pdf,.docx,.doc,.txt,.md"
              className="hidden"
              onChange={handleFileUpload}
              disabled={uploading}
            />
          </label>
        </div>
      </div>

      {error && (
        <div className="mt-4 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {/* Document List */}
      <div className="mt-8">
        {loading ? (
          <div className="text-center py-16 text-slate-500">Loading document catalog...</div>
        ) : documents.length === 0 ? (
          <div className="border border-dashed border-slate-800 rounded-2xl p-12 text-center bg-slate-900/50">
            <Database className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <h3 className="text-lg font-medium text-slate-300">No documents indexed yet</h3>
            <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
              Upload PDF, DOCX, or TXT files to enable citation-grounded retrieval and evaluation.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="bg-slate-800/50 border border-slate-700/60 rounded-xl p-5 hover:border-slate-600 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 rounded-xl bg-slate-700/50 border border-slate-600/50 flex items-center justify-center text-slate-300 flex-shrink-0">
                    <FileText className="w-6 h-6 text-emerald-400" />
                  </div>
                  <div>
                    <h4 className="text-base font-semibold text-white flex items-center gap-2">
                      {doc.filename}
                      <span className="text-xs uppercase font-mono px-2 py-0.5 rounded bg-slate-700 text-slate-300">
                        {doc.file_type}
                      </span>
                    </h4>
                    <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-slate-400">
                      <span className="flex items-center gap-1">
                        <Layers className="w-3.5 h-3.5 text-slate-500" />
                        {doc.chunk_count} Chunks
                      </span>
                      <span>•</span>
                      <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
                      <span>•</span>
                      <span className="font-mono text-slate-500 truncate max-w-xs" title={doc.file_hash}>
                        Hash: {doc.file_hash.slice(0, 12)}...
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3 self-end md:self-center">
                  {doc.status === 'indexed' ? (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Indexed
                    </span>
                  ) : doc.status === 'processing' ? (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                      <Clock className="w-3.5 h-3.5 animate-spin" />
                      Processing
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
                      <AlertCircle className="w-3.5 h-3.5" />
                      Error
                    </span>
                  )}

                  <button
                    onClick={() => setShowReindexModal(doc.id)}
                    className="p-2 rounded-lg bg-slate-700/60 hover:bg-slate-700 text-slate-300 hover:text-white transition-all text-xs flex items-center gap-1"
                    title="Re-index with different chunk sizes"
                  >
                    <RefreshCw className={`w-4 h-4 ${reindexingId === doc.id ? 'animate-spin' : ''}`} />
                    <span className="hidden sm:inline">Re-index</span>
                  </button>

                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="p-2 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 hover:text-rose-300 transition-all"
                    title="Delete document"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Reindex Modal */}
      {showReindexModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6 max-w-md w-full shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-2">Re-index Document</h3>
            <p className="text-xs text-slate-400 mb-5">
              Experiment with different chunking parameters to evaluate their impact on retrieval quality.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Chunk Size (approx tokens/words): {reindexChunkSize}
                </label>
                <input
                  type="range"
                  min="100"
                  max="1000"
                  step="50"
                  value={reindexChunkSize}
                  onChange={(e) => setReindexChunkSize(Number(e.target.value))}
                  className="w-full accent-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Chunk Overlap (tokens/words): {reindexOverlap}
                </label>
                <input
                  type="range"
                  min="0"
                  max="300"
                  step="25"
                  value={reindexOverlap}
                  onChange={(e) => setReindexOverlap(Number(e.target.value))}
                  className="w-full accent-emerald-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowReindexModal(null)}
                className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white bg-slate-700/50"
              >
                Cancel
              </button>
              <button
                onClick={() => handleReindex(showReindexModal)}
                disabled={reindexingId !== null}
                className="px-4 py-2 rounded-xl text-xs font-medium bg-emerald-500 hover:bg-emerald-600 text-white"
              >
                {reindexingId ? 'Re-indexing...' : 'Apply & Re-index'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

