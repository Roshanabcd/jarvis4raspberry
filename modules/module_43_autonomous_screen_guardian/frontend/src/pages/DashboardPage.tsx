import React, { useCallback, useEffect, useState } from "react";
import { AlertTriangle, Cpu, Eye, ShieldCheck, Square, Wrench } from "lucide-react";
import { guardianApi, GuardianStatus } from "../services/api";

export const DashboardPage: React.FC = () => {
  const [status, setStatus] = useState<GuardianStatus | null>(null);
  const [notifications, setNotifications] = useState<Array<Record<string, unknown>>>([]);
  const [repairs, setRepairs] = useState<Array<Record<string, unknown>>>([]);
  const [consent, setConsent] = useState(false);
  const [workspace, setWorkspace] = useState("");
  const [mode, setMode] = useState("assisted_repair");
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [st, nt, rp] = await Promise.all([
        guardianApi.getStatus(),
        guardianApi.listNotifications(),
        guardianApi.listRepairs(),
      ]);
      setStatus(st);
      setNotifications(nt.notifications);
      setRepairs(rp.repairs);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load Screen Guardian telemetry");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <div className="mx-auto max-w-7xl space-y-5 p-6">
      <header className="jarvis-panel flex flex-wrap items-center justify-between gap-4 rounded-2xl p-5">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-[#00D9FF]">
            <Eye className="h-5 w-5" /> JARVIS Module 43 — Autonomous Screen Guardian & AI Repair Agent
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Explicit-Consent Monitoring · Local Tesseract OCR · Contextual Error Detection · Controlled Code Repair
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="rounded-full border border-cyan-400/30 bg-[#050B16] px-3 py-1 text-xs font-bold uppercase text-[#25E6A2]">
            {status?.monitoring.state ?? "STOPPED"}
          </span>
          <button
            onClick={async () => {
              await guardianApi.stopMonitor();
              await refresh();
            }}
            className="inline-flex items-center gap-1 rounded-lg bg-rose-500/20 px-3 py-2 text-xs font-bold text-rose-300"
          >
            <Square className="h-3.5 w-3.5" /> STOP MONITORING
          </button>
        </div>
      </header>

      {error && <div className="rounded-xl border border-rose-500/40 bg-rose-950/50 p-3 text-sm text-rose-200">{error}</div>}

      {status && (
        <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <div className="jarvis-panel rounded-xl p-4">
            <div className="text-xs uppercase text-slate-400">OCR Engine</div>
            <div className="mt-1 text-lg font-bold text-[#00D9FF]">{status.ocr_engine}</div>
          </div>
          <div className="jarvis-panel rounded-xl p-4">
            <div className="text-xs uppercase text-slate-400">Active Errors</div>
            <div className="mt-1 text-2xl font-bold text-rose-400">{status.active_errors}</div>
          </div>
          <div className="jarvis-panel rounded-xl p-4">
            <div className="text-xs uppercase text-slate-400">Unread Alerts</div>
            <div className="mt-1 text-2xl font-bold text-[#9868FF]">{status.unread_notifications}</div>
          </div>
          <div className="jarvis-panel rounded-xl p-4">
            <div className="flex items-center gap-1 text-xs uppercase text-slate-400">
              <Cpu className="h-3.5 w-3.5" /> System ({status.telemetry.architecture})
            </div>
            <div className="mt-1 text-sm font-bold text-[#25E6A2]">
              RAM {status.telemetry.memory.used_pct}% · Disk {status.telemetry.disk.used_pct}%
            </div>
          </div>
        </section>
      )}

      <div className="grid gap-5 lg:grid-cols-2">
        <div className="jarvis-panel space-y-3 rounded-xl p-4">
          <div className="flex items-center gap-2 text-sm font-semibold uppercase text-[#00D9FF]">
            <ShieldCheck className="h-4 w-4" /> Monitoring & Privacy Controls
          </div>
          <label className="flex items-center gap-2 text-xs text-slate-200">
            <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
            I explicitly authorize desktop screen monitoring for this session
          </label>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={async () => {
                try {
                  await guardianApi.startMonitor(consent);
                  await refresh();
                } catch (e) {
                  setError(e instanceof Error ? e.message : "Failed to start");
                }
              }}
              className="rounded-lg bg-[#25E6A2]/20 px-3 py-1.5 text-xs font-bold text-[#25E6A2]"
            >
              Start Monitoring
            </button>
            <button
              onClick={async () => {
                await guardianApi.pauseMonitor();
                await refresh();
              }}
              className="rounded-lg bg-amber-500/20 px-3 py-1.5 text-xs font-bold text-amber-300"
            >
              Pause
            </button>
            <button
              onClick={async () => {
                await guardianApi.resumeMonitor();
                await refresh();
              }}
              className="rounded-lg bg-[#218BFF]/20 px-3 py-1.5 text-xs font-bold text-[#00D9FF]"
            >
              Resume
            </button>
          </div>
        </div>

        <div className="jarvis-panel space-y-3 rounded-xl p-4">
          <div className="flex items-center gap-2 text-sm font-semibold uppercase text-[#00D9FF]">
            <AlertTriangle className="h-4 w-4" /> Notifications ({notifications.length})
          </div>
          <div className="space-y-2">
            {notifications.map((n) => (
              <div key={String(n.notification_id)} className="rounded-lg border border-cyan-500/20 bg-[#050B16]/70 p-3 text-xs">
                <div className="font-semibold text-[#F0F8FF]">{String(n.title)}</div>
                <div className="text-slate-400">{String(n.details)}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="jarvis-panel space-y-3 rounded-xl p-4">
        <div className="flex items-center gap-2 text-sm font-semibold uppercase text-[#00D9FF]">
          <Wrench className="h-4 w-4" /> AI Repair Center ({repairs.length})
        </div>
        <div className="flex flex-wrap gap-2">
          <input
            value={workspace}
            onChange={(e) => setWorkspace(e.target.value)}
            placeholder="/path/to/authorized/workspace"
            className="min-w-[240px] flex-1 rounded-lg border border-slate-700 bg-[#050B16] px-3 py-2 text-xs"
          />
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            className="rounded-lg border border-slate-700 bg-[#050B16] px-3 py-2 text-xs"
          >
            <option value="observe_only">Observe Only</option>
            <option value="suggest_fix">Suggest Fix</option>
            <option value="assisted_repair">Assisted Repair</option>
            <option value="trusted_workspace_autopilot">Trusted Workspace Autopilot</option>
          </select>
          <button
            onClick={async () => {
              try {
                await guardianApi.createRepair({
                  workspace_path: workspace,
                  mode,
                  summary: "Repair detected issue",
                  agent_id: "reference_local_repair_agent",
                });
                await refresh();
              } catch (e) {
                setError(e instanceof Error ? e.message : "Repair request rejected");
              }
            }}
            className="rounded-lg bg-gradient-to-r from-[#00D9FF] to-[#218BFF] px-4 py-2 text-xs font-bold text-[#050B16]"
          >
            Create Repair Request
          </button>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
