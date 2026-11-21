import React, { useEffect, useState } from "react";

interface HealthStatus {
  adapter: string;
  simulated: boolean;
  hostname: string;
  load_1m: number;
  memory_used_pct: number;
  disk_used_pct: number;
  cpu_temp_c: number | null;
  open_alerts_count: number;
  services_count: number;
}

const API = "/api/v1/system-health";

export default function DashboardPage() {
  const [status, setStatus] = useState<HealthStatus | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const loadStatus = async () => {
    const res = await fetch(`${API}/status`);
    if (res.ok) setStatus(await res.json());
  };

  useEffect(() => {
    loadStatus().catch(() => setNotice("Unable to connect to System Health API."));
  }, []);

  const runDiagnostics = async () => {
    const res = await fetch(`${API}/diagnostics/run`, { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      setNotice(`Diagnostics complete — Score: ${data.health_score}/100`);
      await loadStatus();
    }
  };

  return (
    <div className="min-h-screen bg-[#050B16] text-[#F0F8FF] p-6">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-cyan-400/20 pb-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-wider text-[#00D9FF]">
            JARVIS System Health &amp; Diagnostics
          </h1>
          <p className="text-sm text-slate-400">
            Module 32 • Real Local Host Telemetry, Threshold Alerting &amp; Service Probes
          </p>
        </div>
        <span className="px-3 py-1 rounded-full border border-[#25E6A2]/50 text-[#25E6A2] text-xs">
          {status?.simulated ? "SIMULATED" : "LIVE LOCAL OS PROBE"}
        </span>
      </header>

      {notice && (
        <div className="mb-4 rounded-lg border border-cyan-400/30 bg-[#101E30] px-4 py-2 text-sm text-[#00D9FF]">
          {notice}
        </div>
      )}

      <section className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">Load (1m)</div>
          <div className="text-2xl font-bold">{status?.load_1m ?? 0}</div>
        </div>
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">Memory Used</div>
          <div className="text-2xl font-bold">{status?.memory_used_pct ?? 0}%</div>
        </div>
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">Disk Used</div>
          <div className="text-2xl font-bold">{status?.disk_used_pct ?? 0}%</div>
        </div>
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">Open Alerts</div>
          <div className="text-2xl font-bold text-[#25E6A2]">{status?.open_alerts_count ?? 0}</div>
        </div>
      </section>

      <button
        onClick={runDiagnostics}
        className="px-4 py-2 rounded-lg bg-[#00D9FF] text-[#050B16] font-semibold text-sm"
      >
        Run Full Diagnostics
      </button>
    </div>
  );
}
