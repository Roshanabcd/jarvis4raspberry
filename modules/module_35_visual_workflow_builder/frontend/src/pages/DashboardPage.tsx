import React, { useEffect, useState } from "react";

interface WorkflowStatus {
  adapter: string;
  simulated: boolean;
  workflows_count: number;
  runs_count: number;
}

const API = "/api/v1/workflows";

export default function DashboardPage() {
  const [status, setStatus] = useState<WorkflowStatus | null>(null);

  useEffect(() => {
    fetch(`${API}/status`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setStatus(d))
      .catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-[#050B16] text-[#F0F8FF] p-6">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-cyan-400/20 pb-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-wider text-[#00D9FF]">
            JARVIS Visual Workflow Builder
          </h1>
          <p className="text-sm text-slate-400">
            Module 35 • DAG Validation, Visual Node Graph &amp; Topological Execution Engine
          </p>
        </div>
        <span className="px-3 py-1 rounded-full border border-[#25E6A2]/50 text-[#25E6A2] text-xs">
          LOCAL DAG ENGINE
        </span>
      </header>

      <section className="grid grid-cols-2 gap-4">
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">Saved Workflows</div>
          <div className="text-2xl font-bold">{status?.workflows_count ?? 0}</div>
        </div>
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">Executed Runs</div>
          <div className="text-2xl font-bold text-[#25E6A2]">{status?.runs_count ?? 0}</div>
        </div>
      </section>
    </div>
  );
}
