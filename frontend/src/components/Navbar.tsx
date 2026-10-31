import React from 'react';
import { BookOpen, BarChart3, MessageSquare, ShieldCheck } from 'lucide-react';

interface NavbarProps {
  activeTab: 'chat' | 'documents' | 'evaluation';
  setActiveTab: (tab: 'chat' | 'documents' | 'evaluation') => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-white flex items-center gap-2">
              RAG <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">Citations + Evals</span>
            </h1>
            <p className="text-xs text-slate-400">Verifiable Retrieval-Augmented Generation & Automated Evals</p>
          </div>
        </div>

        <nav className="flex items-center space-x-1 bg-slate-800/80 p-1 rounded-xl border border-slate-700/60">
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'chat'
                ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            <span>Chat & Citations</span>
          </button>

          <button
            onClick={() => setActiveTab('documents')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'documents'
                ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
            }`}
          >
            <BookOpen className="w-4 h-4" />
            <span>Knowledge Base</span>
          </button>

          <button
            onClick={() => setActiveTab('evaluation')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'evaluation'
                ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Evaluation & Evals</span>
          </button>
        </nav>
      </div>
    </header>
  );
};

