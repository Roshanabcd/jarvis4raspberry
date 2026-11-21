import React, { useEffect, useState } from 'react';

interface Repo {
  repo_id: string;
  full_name: string;
  default_branch: string;
  require_ci_green: boolean;
}

interface PipelineRun {
  run_id: string;
  workflow_name: string;
  branch: string;
  status: string;
  duration_sec: number;
}

const API_BASE = '/api/v1/github-cicd';

export const DashboardPage: React.FC = () => {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [selected, setSelected] = useState<Repo | null>(null);
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [fullName, setFullName] = useState('');

  const loadRepos = async () => {
    const res = await fetch(`${API_BASE}/repos`);
    if (res.ok) {
      const d = await res.json();
      setRepos(d.repositories || []);
    }
  };

  const loadRuns = async (repoId: string) => {
    const res = await fetch(`${API_BASE}/pipelines?repo_id=${repoId}`);
    if (res.ok) {
      const d = await res.json();
      setRuns(d.runs || []);
    }
  };

  useEffect(() => {
    void loadRepos();
  }, []);

  const registerRepo = async () => {
    if (!fullName.includes('/')) return;
    const res = await fetch(`${API_BASE}/repos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name: fullName.trim(), default_branch: 'main' }),
    });
    if (res.ok) {
      const r = await res.json();
      setFullName('');
      await loadRepos();
      setSelected(r);
      await loadRuns(r.repo_id);
    }
  };

  const triggerCI = async () => {
    if (!selected) return;
    await fetch(`${API_BASE}/pipelines/trigger`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_id: selected.repo_id, branch: selected.default_branch }),
    });
    await loadRuns(selected.repo_id);
  };

  return (
    <div className="min-h-screen bg-jarvis-bg text-jarvis-text p-6">
      <header className="flex items-center justify-between border-b border-jarvis-cyan/25 pb-4 mb-6">
        <div>
          <h1 className="text-xl font-bold text-jarvis-cyan">JARVIS OS — Module 27: GitHub &amp; CI/CD Manager</h1>
          <p className="text-xs text-slate-400">Repositories, Pull Request Merge Gates, Pipelines &amp; Releases</p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs border border-amber-400/50 text-amber-300 bg-amber-500/10">
          Simulated GitHub Actions
        </span>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="bg-jarvis-panel border border-jarvis-cyan/20 rounded-xl p-4 space-y-3">
          <h2 className="text-sm font-semibold text-jarvis-cyan">Repositories</h2>
          <div className="flex gap-2">
            <input value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="owner/repo" className="flex-1 bg-jarvis-bg border border-slate-700 rounded-lg px-3 py-2 text-sm" />
            <button onClick={registerRepo} className="px-3 py-2 rounded-lg bg-jarvis-cyan text-slate-950 font-semibold text-sm">Add</button>
          </div>
          <div className="space-y-2">
            {repos.map((r) => (
              <button key={r.repo_id} onClick={() => { setSelected(r); void loadRuns(r.repo_id); }} className="w-full text-left p-3 rounded-lg bg-jarvis-bg border border-slate-700 hover:border-jarvis-cyan">
                <div className="font-medium text-sm">{r.full_name}</div>
                <div className="text-xs text-slate-400">branch: {r.default_branch}</div>
              </button>
            ))}
          </div>
        </section>

        <section className="lg:col-span-2 bg-jarvis-panel border border-jarvis-cyan/20 rounded-xl p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-jarvis-cyan">{selected ? selected.full_name : 'Select a Repository'}</h2>
            {selected && <button onClick={triggerCI} className="px-4 py-1.5 rounded-lg bg-jarvis-blue text-white text-sm font-semibold">Run CI Pipeline</button>}
          </div>
          <div className="space-y-2">
            {runs.map((run) => (
              <div key={run.run_id} className="p-3 rounded-lg bg-jarvis-bg border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium">{run.workflow_name} @ {run.branch}</div>
                  <div className="text-xs text-slate-400">{run.duration_sec}s</div>
                </div>
                <span className="text-xs px-2 py-1 rounded bg-slate-800 text-jarvis-green">{run.status}</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
};
