import React, { useEffect, useState } from 'react';

interface ModelRecord {
  model_id: string;
  provider: string;
  display_name: string;
  privacy_tier: string;
  quality_score: number;
  avg_latency_ms: number;
  enabled: boolean;
  circuit_state: string;
}

const API = '/api/v1/model-router';

export default function DashboardPage() {
  const [simulated, setSimulated] = useState(true);
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [prompt, setPrompt] = useState('Write a Python FastAPI dependency for rate limiting.');
  const [strategy, setStrategy] = useState('balanced');
  const [result, setResult] = useState<string>('');

  async function refresh() {
    try {
      const [st, md] = await Promise.all([
        fetch(`${API}/status`).then((r) => r.json()),
        fetch(`${API}/models`).then((r) => r.json()),
      ]);
      setSimulated(Boolean(st.simulated));
      setModels(md.models || []);
    } catch {
      setResult('Backend unreachable on port 8122.');
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function runRoute() {
    const res = await fetch(`${API}/route`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, strategy }),
    });
    const data = await res.json();
    setResult(JSON.stringify(data, null, 2));
    refresh();
  }

  return (
    <div className="min-h-screen bg-[#050B16] text-[#F0F8FF] p-6">
      <header className="flex flex-wrap items-center justify-between gap-4 bg-[#101E30] border border-[#00D9FF]/30 rounded-xl p-4 mb-6">
        <div>
          <h1 className="text-xl font-bold text-[#00D9FF]">JARVIS OS — Intelligent AI Model Router (Module 22)</h1>
          <p className="text-xs text-slate-400">Task-aware routing, automatic failover, circuit breakers &amp; cost guardrails</p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-semibold border border-amber-400/50 bg-amber-400/10 text-amber-300">
          {simulated ? 'SIMULATED ADAPTER' : 'LIVE ADAPTER'}
        </span>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="bg-[#101E30] border border-[#00D9FF]/25 rounded-xl p-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-[#00D9FF] mb-3">Route Playground</h2>
          <div className="flex gap-2 mb-3">
            <select
              aria-label="Routing Strategy"
              className="bg-[#050B16] border border-slate-700 rounded-lg px-3 py-2 text-sm"
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
            >
              <option value="balanced">Balanced</option>
              <option value="cost_optimized">Cost Optimized</option>
              <option value="latency_optimized">Latency Optimized</option>
              <option value="quality_first">Quality First</option>
              <option value="local_only">Local Only</option>
            </select>
            <button onClick={runRoute} className="px-4 py-2 rounded-lg bg-[#00D9FF] text-[#050B16] font-semibold text-sm">
              Route Prompt
            </button>
          </div>
          <textarea
            className="w-full bg-[#050B16] border border-slate-700 rounded-lg p-3 text-sm mb-3"
            rows={3}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
          {result && (
            <pre className="bg-[#050B16] border border-slate-800 rounded-lg p-3 text-xs overflow-auto max-h-60 text-cyan-200">
              {result}
            </pre>
          )}
        </section>

        <section className="bg-[#101E30] border border-[#00D9FF]/25 rounded-xl p-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-[#00D9FF] mb-3">
            Registered Models ({models.length})
          </h2>
          <ul className="space-y-2 text-sm">
            {models.map((m) => (
              <li key={m.model_id} className="p-3 rounded-lg bg-[#050B16] border border-slate-800 flex justify-between">
                <div>
                  <div className="font-semibold">{m.display_name}</div>
                  <div className="text-xs font-mono text-slate-400">
                    {m.model_id} · {m.avg_latency_ms}ms · quality {m.quality_score}
                  </div>
                </div>
                <span className="text-xs text-[#25E6A2]">{m.privacy_tier} / {m.circuit_state}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
