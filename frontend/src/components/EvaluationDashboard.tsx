import React, { useState, useEffect } from 'react';
import { Play, BarChart3, TrendingUp, CheckCircle, Clock, Zap, DollarSign, Award, Layers, Search, RefreshCw, Cpu } from 'lucide-react';
import { EvaluationExperiment, ExperimentComparison } from '../types';
import { api } from '../services/api';

export const EvaluationDashboard: React.FC = () => {
  const [experiments, setExperiments] = useState<EvaluationExperiment[]>([]);
  const [comparison, setComparison] = useState<ExperimentComparison | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [running, setRunning] = useState<boolean>(false);

  // Form State
  const [expName, setExpName] = useState<string>('Hybrid + Reranker Experiment');
  const [chunkSize, setChunkSize] = useState<number>(500);
  const [chunkOverlap, setChunkOverlap] = useState<number>(100);
  const [strategy, setStrategy] = useState<string>('hybrid');
  const [topK, setTopK] = useState<number>(5);
  const [rerank, setRerank] = useState<boolean>(true);

  const fetchEvals = async () => {
    try {
      setLoading(true);
      const [exps, comp] = await Promise.all([
        api.getEvaluationResults(),
        api.compareExperiments()
      ]);
      setExperiments(exps);
      setComparison(comp);
    } catch (err: any) {
      console.error('Failed to load evaluation data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvals();
  }, []);

  const handleRunEvaluation = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setRunning(true);
      await api.runEvaluation({
        name: expName,
        chunk_size: chunkSize,
        chunk_overlap: chunkOverlap,
        retrieval_strategy: strategy,
        top_k: topK,
        rerank: rerank
      });
      await fetchEvals();
    } catch (err: any) {
      alert('Evaluation run failed: ' + err.message);
    } finally {
      setRunning(false);
    }
  };

  const latestExp = experiments[0];
  const metricsMap = latestExp?.results.reduce((acc, curr) => {
    acc[curr.metric_name] = curr.metric_value;
    return acc;
  }, {} as Record<string, number>) || {};

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">RAG Evaluation & Experimentation Dashboard</h2>
          <p className="text-sm text-slate-400 mt-1">
            Quantify retrieval precision, citation accuracy, faithfulness, and latency across RAG configurations.
          </p>
        </div>

        <button
          onClick={fetchEvals}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-all self-start md:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* Metrics Cards (Latest Experiment) */}
      {latestExp && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Award className="w-5 h-5 text-emerald-400" />
              Latest Experiment: <span className="text-emerald-400">{latestExp.name}</span>
            </h3>
            <span className="text-xs text-slate-500 font-mono">ID: {latestExp.id.slice(0, 8)}</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {/* Precision@K */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
              <span className="text-xs text-slate-400">Precision@K</span>
              <div className="text-2xl font-bold text-emerald-400 font-mono mt-1">
                {((metricsMap['Precision@K'] ?? 0) * 100).toFixed(0)}%
              </div>
              <span className="text-[10px] text-slate-500">Retrieval relevance</span>
            </div>

            {/* Recall@K */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
              <span className="text-xs text-slate-400">Recall@K</span>
              <div className="text-2xl font-bold text-emerald-400 font-mono mt-1">
                {((metricsMap['Recall@K'] ?? 0) * 100).toFixed(0)}%
              </div>
              <span className="text-[10px] text-slate-500">Target coverage</span>
            </div>

            {/* Faithfulness */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
              <span className="text-xs text-slate-400">Faithfulness</span>
              <div className="text-2xl font-bold text-blue-400 font-mono mt-1">
                {((metricsMap['Faithfulness'] ?? 0) * 100).toFixed(0)}%
              </div>
              <span className="text-[10px] text-slate-500">Grounded claims</span>
            </div>

            {/* Citation Precision */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
              <span className="text-xs text-slate-400">Citation Prec.</span>
              <div className="text-2xl font-bold text-purple-400 font-mono mt-1">
                {((metricsMap['Citation_Precision'] ?? 0) * 100).toFixed(0)}%
              </div>
              <span className="text-[10px] text-slate-500">Valid citations</span>
            </div>

            {/* Latency */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
              <span className="text-xs text-slate-400">Avg Latency</span>
              <div className="text-2xl font-bold text-amber-400 font-mono mt-1">
                {(metricsMap['Avg_Latency_ms'] ?? 0).toFixed(0)} ms
              </div>
              <span className="text-[10px] text-slate-500">Roundtrip query</span>
            </div>

            {/* Est Cost */}
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
              <span className="text-xs text-slate-400">Cost / Query</span>
              <div className="text-2xl font-bold text-emerald-300 font-mono mt-1">
                ${(metricsMap['Estimated_Cost_USD'] ?? 0).toFixed(5)}
              </div>
              <span className="text-[10px] text-slate-500">Avg token cost</span>
            </div>
          </div>
        </div>
      )}

      {/* Grid: New Run Form & Comparative Experiment Table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Run Evaluation Form */}
        <div className="bg-slate-800/40 border border-slate-700/60 rounded-2xl p-6">
          <h3 className="text-base font-semibold text-white flex items-center gap-2 mb-4">
            <Play className="w-4 h-4 text-emerald-400" />
            Run Evaluation Experiment
          </h3>

          <form onSubmit={handleRunEvaluation} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Experiment Name</label>
              <input
                type="text"
                value={expName}
                onChange={(e) => setExpName(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-white"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Chunk Size: {chunkSize}</label>
                <input
                  type="range"
                  min="200"
                  max="1000"
                  step="100"
                  value={chunkSize}
                  onChange={(e) => setChunkSize(Number(e.target.value))}
                  className="w-full accent-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Overlap: {chunkOverlap}</label>
                <input
                  type="range"
                  min="0"
                  max="200"
                  step="25"
                  value={chunkOverlap}
                  onChange={(e) => setChunkOverlap(Number(e.target.value))}
                  className="w-full accent-emerald-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Strategy</label>
                <select
                  value={strategy}
                  onChange={(e) => setStrategy(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
                >
                  <option value="hybrid">Hybrid (Dense + BM25)</option>
                  <option value="dense">Dense Vector</option>
                  <option value="sparse">Sparse BM25</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Top-K: {topK}</label>
                <input
                  type="range"
                  min="2"
                  max="10"
                  value={topK}
                  onChange={(e) => setTopK(Number(e.target.value))}
                  className="w-full accent-emerald-500"
                />
              </div>
            </div>

            <div className="pt-2">
              <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-300">
                <input
                  type="checkbox"
                  checked={rerank}
                  onChange={(e) => setRerank(e.target.checked)}
                  className="rounded accent-emerald-500 w-4 h-4"
                />
                <span>Cross-Encoder Reranker Enabled</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={running}
              className={`w-full py-2.5 rounded-xl font-medium text-xs text-white transition-all shadow-lg flex items-center justify-center gap-2 mt-4 ${
                running
                  ? 'bg-slate-700 cursor-not-allowed text-slate-400'
                  : 'bg-emerald-500 hover:bg-emerald-600 shadow-emerald-500/20'
              }`}
            >
              <Play className={`w-3.5 h-3.5 ${running ? 'animate-spin' : ''}`} />
              <span>{running ? 'Running Evaluation Engine...' : 'Execute Evaluation'}</span>
            </button>
          </form>
        </div>

        {/* Comparative Experiment Table */}
        <div className="lg:col-span-2 bg-slate-800/40 border border-slate-700/60 rounded-2xl p-6 overflow-hidden">
          <h3 className="text-base font-semibold text-white flex items-center gap-2 mb-4">
            <BarChart3 className="w-4 h-4 text-emerald-400" />
            Experiment Comparison Matrix
          </h3>

          {!comparison || comparison.experiments.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-xs">
              No evaluation experiments executed yet. Run an experiment using the form to start tracking metrics.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-700 text-slate-400 uppercase tracking-wider text-[10px]">
                    <th className="py-2.5 px-3">Metric</th>
                    {comparison.experiments.map((exp) => (
                      <th key={exp.id} className="py-2.5 px-3">
                        <div className="font-semibold text-white">{exp.name}</div>
                        <div className="text-[10px] text-slate-500 font-mono">
                          {exp.configuration?.retrieval_strategy} | {exp.configuration?.rerank ? 'Reranked' : 'No-Rerank'}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {Object.entries(comparison.metrics_summary).map(([metricName, expValues]) => (
                    <tr key={metricName} className="hover:bg-slate-800/50">
                      <td className="py-2.5 px-3 font-medium text-slate-300">{metricName}</td>
                      {comparison.experiments.map((exp) => {
                        const val = expValues[exp.id];
                        let displayVal = 'N/A';
                        if (typeof val === 'number') {
                          if (metricName.includes('Latency')) displayVal = `${val.toFixed(0)} ms`;
                          else if (metricName.includes('Cost')) displayVal = `$${val.toFixed(5)}`;
                          else if (metricName.includes('Tokens')) displayVal = String(Math.round(val));
                          else displayVal = (val * 100).toFixed(1) + '%';
                        }
                        return (
                          <td key={exp.id} className="py-2.5 px-3 font-mono text-emerald-400">
                            {displayVal}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

