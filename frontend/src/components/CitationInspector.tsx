import React from 'react';
import { X, CheckCircle, AlertTriangle, ExternalLink, ShieldCheck, FileText } from 'lucide-react';
import { CitationDetail, RetrievedPassage } from '../types';

interface CitationInspectorProps {
  citation: CitationDetail | null;
  passage?: RetrievedPassage | null;
  onClose: () => void;
}

export const CitationInspector: React.FC<CitationInspectorProps> = ({ citation, passage, onClose }) => {
  if (!citation && !passage) return null;

  const sourceId = citation?.source_id || passage?.source_id || 'S';
  const docName = citation?.document_name || passage?.document_name || 'Document';
  const pageNumber = citation?.page_number ?? passage?.page_number;
  const content = citation?.quoted_text || passage?.content || '';
  const fullPassageContent = passage?.content || '';
  const isValid = citation ? citation.is_valid : true;
  const confidence = citation?.confidence_score ?? passage?.final_score;

  // Render passage content with highlighted quoted text
  const renderHighlightedContent = () => {
    if (!fullPassageContent) {
      return <p className="text-sm text-slate-300 leading-relaxed italic">{content}</p>;
    }

    if (!citation?.quoted_text) {
      return <p className="text-sm text-slate-300 leading-relaxed">{fullPassageContent}</p>;
    }

    const quote = citation.quoted_text.trim();
    const idx = fullPassageContent.toLowerCase().indexOf(quote.toLowerCase());

    if (idx === -1) {
      return (
        <div>
          <div className="mb-3 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>Exact quote was paraphrased or synthesized by the model.</span>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed">{fullPassageContent}</p>
        </div>
      );
    }

    const before = fullPassageContent.slice(0, idx);
    const match = fullPassageContent.slice(idx, idx + quote.length);
    const after = fullPassageContent.slice(idx + quote.length);

    return (
      <p className="text-sm text-slate-300 leading-relaxed">
        {before}
        <mark className="bg-emerald-500/30 text-emerald-200 px-1 py-0.5 rounded font-medium border border-emerald-500/40">
          {match}
        </mark>
        {after}
      </p>
    );
  };

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[480px] bg-slate-900 border-l border-slate-800 shadow-2xl z-50 flex flex-col transform transition-transform animate-in slide-in-from-right">
      <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/60 backdrop-blur">
        <div className="flex items-center gap-3">
          <span className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold flex items-center justify-center text-sm font-mono">
            [{sourceId}]
          </span>
          <div>
            <h3 className="text-base font-semibold text-white">Citation Grounding</h3>
            <p className="text-xs text-slate-400">Verifiable source passage inspection</p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="p-6 flex-1 overflow-y-auto space-y-6">
        {/* Verification Status */}
        <div className={`p-4 rounded-xl border flex items-start gap-3 ${
          isValid
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
            : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
        }`}>
          {isValid ? (
            <ShieldCheck className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
          )}
          <div>
            <h4 className="text-sm font-semibold">
              {isValid ? 'Verified Citation Grounding' : 'Citation Verification Warning'}
            </h4>
            <p className="text-xs opacity-90 mt-0.5">
              {isValid
                ? 'This claim successfully resolves to an authentic indexed chunk in the knowledge base.'
                : 'This source identifier does not match any retrieved source passage.'}
            </p>
          </div>
        </div>

        {/* Metadata Details */}
        <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">Source Document:</span>
            <span className="font-medium text-slate-200 flex items-center gap-1.5 truncate max-w-[200px]" title={docName}>
              <FileText className="w-3.5 h-3.5 text-emerald-400" />
              {docName}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">Page Reference:</span>
            <span className="font-medium text-slate-200 font-mono">
              {pageNumber ? `Page ${pageNumber}` : 'N/A'}
            </span>
          </div>

          {confidence !== undefined && (
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Relevance / Match Score:</span>
              <span className="font-medium text-emerald-400 font-mono">
                {(confidence * 100).toFixed(1)}%
              </span>
            </div>
          )}

          {passage?.rerank_score !== undefined && (
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Cross-Encoder Score:</span>
              <span className="font-medium text-purple-400 font-mono">
                {passage.rerank_score.toFixed(4)}
              </span>
            </div>
          )}
        </div>

        {/* Supporting Evidence Passage */}
        <div>
          <h4 className="text-xs uppercase tracking-wider font-semibold text-slate-400 mb-2">
            Supporting Evidence Passage
          </h4>
          <div className="p-4 rounded-xl bg-slate-800/80 border border-slate-700/80 max-h-72 overflow-y-auto">
            {renderHighlightedContent()}
          </div>
        </div>
      </div>
    </div>
  );
};

