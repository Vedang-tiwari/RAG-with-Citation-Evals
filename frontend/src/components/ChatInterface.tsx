import React, { useState } from 'react';
import { Send, Sparkles, Bot, User, CheckCircle2, Clock, Zap, BookOpen, Sliders, ShieldAlert, Layers } from 'lucide-react';
import { ChatMessage, CitationDetail, RetrievedPassage } from '../types';
import { api } from '../services/api';
import { CitationInspector } from './CitationInspector';

export const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I am your Citation-Grounded RAG Assistant. Ask any question about your documents, and every claim will be backed by verifiable citations [S1] that you can inspect in real-time.',
      citations: []
    }
  ]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [strategy, setStrategy] = useState<string>('hybrid');
  const [rerank, setRerank] = useState<boolean>(true);
  const [topK, setTopK] = useState<number>(5);
  const [selectedCitation, setSelectedCitation] = useState<CitationDetail | null>(null);
  const [selectedPassage, setSelectedPassage] = useState<RetrievedPassage | null>(null);
  const [showConfig, setShowConfig] = useState<boolean>(false);

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput('');

    const userMsg: ChatMessage = {
      id: String(Date.now()),
      role: 'user',
      content: userText
    };

    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await api.sendQuery({
        query: userText,
        top_k: topK,
        retrieval_strategy: strategy,
        rerank: rerank
      });

      const assistantMsg: ChatMessage = {
        id: res.message_id || String(Date.now() + 1),
        role: 'assistant',
        content: res.answer,
        citations: res.citations || [],
        retrieved_passages: res.retrieved_passages || [],
        insufficient_evidence: res.insufficient_evidence,
        citation_precision: res.citation_precision,
        citation_coverage: res.citation_coverage,
        citation_validity: res.citation_validity,
        latency_ms: res.latency_ms,
        tokens_used: res.tokens_used
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: String(Date.now() + 1),
          role: 'assistant',
          content: `Error generating response: ${err.message}`
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Convert inline citations like [S1] into interactive clickable buttons
  const renderMessageContent = (msg: ChatMessage) => {
    const text = msg.content;
    const parts = text.split(/(\[S\d+\])/g);

    return (
      <div className="text-sm leading-relaxed text-slate-200">
        {parts.map((part, index) => {
          const match = part.match(/\[(S\d+)\]/);
          if (match) {
            const sourceId = match[1];
            const citation = msg.citations?.find((c) => c.source_id === sourceId);
            const passage = msg.retrieved_passages?.find((p) => p.source_id === sourceId);

            return (
              <button
                key={index}
                onClick={() => {
                  setSelectedCitation(citation || { source_id: sourceId, is_valid: !!passage });
                  setSelectedPassage(passage || null);
                }}
                className="inline-flex items-center px-1.5 py-0.5 mx-0.5 text-xs font-mono font-bold rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500 hover:text-white transition-all transform hover:scale-105"
                title={`Inspect Source [${sourceId}]`}
              >
                [{sourceId}]
              </button>
            );
          }
          return <span key={index}>{part}</span>;
        })}
      </div>
    );
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-6 flex flex-col h-[calc(100vh-5rem)]">
      {/* Controls & Configuration Bar */}
      <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl px-4 py-3 mb-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="flex items-center gap-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-700/50 px-3 py-1.5 rounded-lg transition-all"
          >
            <Sliders className="w-3.5 h-3.5 text-emerald-400" />
            <span>Retrieval Settings</span>
          </button>

          <span className="text-xs text-slate-400 flex items-center gap-1 font-mono">
            Strategy: <strong className="text-emerald-400 uppercase">{strategy}</strong>
          </span>
          <span className="text-xs text-slate-400 flex items-center gap-1 font-mono">
            Reranking: <strong className={rerank ? "text-purple-400" : "text-slate-500"}>{rerank ? "ON" : "OFF"}</strong>
          </span>
        </div>

        <div className="text-xs text-slate-400 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>Citation Grounding Active</span>
        </div>
      </div>

      {showConfig && (
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 mb-4 grid grid-cols-1 sm:grid-cols-3 gap-4 animate-in fade-in duration-200">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Retrieval Strategy</label>
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white"
            >
              <option value="hybrid">Hybrid (Dense + BM25 Fusion)</option>
              <option value="dense">Dense Vector Search (Qdrant)</option>
              <option value="sparse">Sparse Search (BM25)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Top-K Retrieved: {topK}</label>
            <input
              type="range"
              min="2"
              max="15"
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-full accent-emerald-500 mt-1"
            />
          </div>

          <div className="flex items-center pt-4">
            <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-300">
              <input
                type="checkbox"
                checked={rerank}
                onChange={(e) => setRerank(e.target.checked)}
                className="rounded accent-emerald-500 w-4 h-4"
              />
              <span>Enable Cross-Encoder Reranking</span>
            </label>
          </div>
        </div>
      )}

      {/* Messages Feed */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1 mb-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 flex-shrink-0 mt-1">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div
              className={`max-w-3xl rounded-2xl p-4 shadow-sm ${
                msg.role === 'user'
                  ? 'bg-emerald-600 text-white rounded-br-none'
                  : 'bg-slate-800/80 border border-slate-700/60 rounded-bl-none'
              }`}
            >
              {msg.insufficient_evidence && (
                <div className="mb-3 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center gap-2 font-medium">
                  <ShieldAlert className="w-4 h-4 flex-shrink-0" />
                  <span>Notice: Insufficient evidence in knowledge base for reliable factual answer.</span>
                </div>
              )}

              {renderMessageContent(msg)}

              {/* Assistant Message Metrics Bar */}
              {msg.role === 'assistant' && msg.id !== 'welcome' && (
                <div className="mt-3 pt-3 border-t border-slate-700/50 flex flex-wrap items-center gap-4 text-[11px] text-slate-400">
                  {msg.latency_ms !== undefined && (
                    <span className="flex items-center gap-1 font-mono">
                      <Clock className="w-3 h-3 text-slate-500" />
                      {msg.latency_ms.toFixed(0)} ms
                    </span>
                  )}
                  {msg.tokens_used !== undefined && (
                    <span className="flex items-center gap-1 font-mono">
                      <Zap className="w-3 h-3 text-amber-400" />
                      {msg.tokens_used} tokens
                    </span>
                  )}
                  {msg.citation_precision !== undefined && (
                    <span className="flex items-center gap-1 font-mono">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      Prec: {(msg.citation_precision * 100).toFixed(0)}%
                    </span>
                  )}
                  {msg.retrieved_passages && msg.retrieved_passages.length > 0 && (
                    <button
                      onClick={() => {
                        const first = msg.retrieved_passages![0];
                        setSelectedPassage(first);
                        setSelectedCitation(null);
                      }}
                      className="text-emerald-400 hover:underline flex items-center gap-1 ml-auto font-medium"
                    >
                      <BookOpen className="w-3 h-3" />
                      <span>{msg.retrieved_passages.length} Source Passages</span>
                    </button>
                  )}
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-lg bg-slate-700 flex items-center justify-center text-slate-300 flex-shrink-0 mt-1">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 flex-shrink-0">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl rounded-bl-none p-4 text-xs text-slate-400 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-emerald-400 animate-pulse" />
              <span>Retrieving hybrid evidence and grounding citations...</span>
            </div>
          </div>
        )}
      </div>

      {/* Query Input Box */}
      <form onSubmit={handleSend} className="relative mt-auto">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question grounded in your documents (e.g. 'What is multi-head attention?')..."
          className="w-full bg-slate-800 border border-slate-700 rounded-2xl pl-5 pr-14 py-3.5 text-sm text-white focus:outline-none focus:border-emerald-500 shadow-xl"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className={`absolute right-2.5 top-2.5 p-2 rounded-xl text-white transition-all ${
            loading || !input.trim()
              ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
              : 'bg-emerald-500 hover:bg-emerald-600 shadow-lg shadow-emerald-500/20'
          }`}
        >
          <Send className="w-4 h-4" />
        </button>
      </form>

      {/* Citation Inspector Side Drawer */}
      <CitationInspector
        citation={selectedCitation}
        passage={selectedPassage}
        onClose={() => {
          setSelectedCitation(null);
          setSelectedPassage(null);
        }}
      />
    </div>
  );
};

