import React, { useEffect, useState } from 'react';

interface DatasetSummary {
  dataset_id: string;
  name: string;
  row_count: number;
  columns: string[];
}

const API_BASE = '/api/v1/ai-data-analyst';

export const DashboardPage: React.FC = () => {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');

  const loadDatasets = async () => {
    const res = await fetch(`${API_BASE}/datasets`);
    if (res.ok) {
      const data = await res.json();
      setDatasets(data.datasets || []);
    }
  };

  useEffect(() => {
    void loadDatasets();
  }, []);

  const ask = async () => {
    if (!selectedId || !question.trim()) return;
    const res = await fetch(`${API_BASE}/datasets/${selectedId}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: question.trim() }),
    });
    if (res.ok) {
      const data = await res.json();
      setAnswer(data.answer);
    }
  };

  return (
    <div className="min-h-screen bg-jarvis-bg text-jarvis-text p-6">
      <header className="flex items-center justify-between border-b border-jarvis-cyan/25 pb-4 mb-6">
        <div>
          <h1 className="text-xl font-bold text-jarvis-cyan">JARVIS OS — Module 28: AI Data Analyst</h1>
          <p className="text-xs text-slate-400">Statistical Profiling, Z-Score Anomalies, Aggregations &amp; Natural-Language Q&amp;A</p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs border border-amber-400/50 text-amber-300 bg-amber-500/10">
          Local Stats + Simulated Narrative
        </span>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="bg-jarvis-panel border border-jarvis-cyan/20 rounded-xl p-4 space-y-2">
          <h2 className="text-sm font-semibold text-jarvis-cyan">Datasets</h2>
          {datasets.map((d) => (
            <button key={d.dataset_id} onClick={() => setSelectedId(d.dataset_id)} className="w-full text-left p-3 rounded-lg bg-jarvis-bg border border-slate-700 hover:border-jarvis-cyan">
              <div className="font-medium text-sm">{d.name}</div>
              <div className="text-xs text-slate-400">{d.row_count} rows · {d.columns.length} cols</div>
            </button>
          ))}
        </section>

        <section className="lg:col-span-2 bg-jarvis-panel border border-jarvis-cyan/20 rounded-xl p-4 space-y-4">
          <h2 className="text-sm font-semibold text-jarvis-cyan">Ask Your Dataset</h2>
          <div className="flex gap-2">
            <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask a question..." className="flex-1 bg-jarvis-bg border border-slate-700 rounded-lg px-3 py-2 text-sm" />
            <button onClick={ask} className="px-4 py-2 rounded-lg bg-jarvis-cyan text-slate-950 font-semibold text-sm">Analyze</button>
          </div>
          {answer && <div className="p-3 rounded-lg bg-jarvis-bg border border-jarvis-cyan/30 text-sm">{answer}</div>}
        </section>
      </div>
    </div>
  );
};
