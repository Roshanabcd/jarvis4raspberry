import React, { useEffect, useState } from "react";

interface SecStatus {
  adapter: string;
  simulated: boolean;
  posture_score: number;
  open_incidents: number;
  baselines_count: number;
  scans_count: number;
}

const API = "/api/v1/cybersecurity";

export default function DashboardPage() {
  const [status, setStatus] = useState<SecStatus | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const loadStatus = async () => {
    const res = await fetch(`${API}/status`);
    if (res.ok) setStatus(await res.json());
  };

  useEffect(() => {
    loadStatus().catch(() => setNotice("Unable to connect to Cybersecurity API."));
  }, []);

  const runScan = async () => {
    const res = await fetch(`${API}/scan/secrets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ relative_path: "." })
    });
    if (res.ok) {
      const data = await res.json();
      setNotice(`Scanned ${data.files_scanned} files — ${data.findings_count} findings.`);
      await loadStatus();
    }
  };

  return (
    <div className="min-h-screen bg-[#050B16] text-[#F0F8FF] p-6">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-cyan-400/20 pb-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-wider text-[#00D9FF]">
            JARVIS Defensive Cybersecurity Agent
          </h1>
          <p className="text-sm text-slate-400">
            Module 33 • Sandboxed Secret Scanning, SHA-256 FIM &amp; Log Anomaly Triage
          </p>
        </div>
        <span className="px-3 py-1 rounded-full border border-[#25E6A2]/50 text-[#25E6A2] text-xs">
          DEFENSIVE LOCAL SCANNER
        </span>
      </header>

      {notice && (
        <div className="mb-4 rounded-lg border border-cyan-400/30 bg-[#101E30] px-4 py-2 text-sm text-[#00D9FF]">
          {notice}
        </div>
      )}

      <section className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">Posture Score</div>
          <div className="text-2xl font-bold text-[#25E6A2]">{status?.posture_score ?? 100}/100</div>
        </div>
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">Open Incidents</div>
          <div className="text-2xl font-bold">{status?.open_incidents ?? 0}</div>
        </div>
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">FIM Baselines</div>
          <div className="text-2xl font-bold">{status?.baselines_count ?? 0}</div>
        </div>
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">Scans Run</div>
          <div className="text-2xl font-bold">{status?.scans_count ?? 0}</div>
        </div>
      </section>

      <button
        onClick={runScan}
        className="px-4 py-2 rounded-lg bg-[#00D9FF] text-[#050B16] font-semibold text-sm"
      >
        Run Sandboxed Secret Scan
      </button>
    </div>
  );
}
