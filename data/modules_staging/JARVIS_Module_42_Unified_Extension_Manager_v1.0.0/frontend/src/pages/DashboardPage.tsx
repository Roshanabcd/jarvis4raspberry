import React, { useCallback, useEffect, useState } from "react";
import { FolderSearch, HeartPulse, Layers, ShieldAlert } from "lucide-react";
import { extensionApi, ExtensionModule, ManagerStatus } from "../services/api";

export const DashboardPage: React.FC = () => {
  const [status, setStatus] = useState<ManagerStatus | null>(null);
  const [modules, setModules] = useState<ExtensionModule[]>([]);
  const [folder, setFolder] = useState("/home/roshan/Downloads/module-jarvis");
  const [arch, setArch] = useState("arm64");
  const [inspector, setInspector] = useState<string>("Select a module or run a dry-run install plan.");
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [st, mods] = await Promise.all([extensionApi.getStatus(), extensionApi.listModules()]);
      setStatus(st);
      setModules(mods.modules);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load extension registry");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const res = await extensionApi.scanFolder(folder, arch);
      setInspector(JSON.stringify(res, null, 2));
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed");
    }
  };

  return (
    <div className="mx-auto max-w-7xl space-y-5 p-6">
      <header className="jarvis-panel flex flex-wrap items-center justify-between gap-4 rounded-2xl p-5">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-[#00D9FF]">
            <Layers className="h-5 w-5" /> JARVIS Module 42 — Unified Extension Manager & SDK
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Safe Archive Scanner · ARM64 Compatibility Engine · Dry-Run Install Planner · Real Health Probes
          </p>
        </div>
        <button
          onClick={async () => {
            const plan = await extensionApi.buildPlan([]);
            setInspector(JSON.stringify(plan, null, 2));
          }}
          className="rounded-lg border border-cyan-400/30 bg-[#218BFF]/20 px-4 py-2 text-xs font-semibold text-[#F0F8FF]"
        >
          Preview Dry-Run Install Plan
        </button>
      </header>

      {error && <div className="rounded-xl border border-rose-500/40 bg-rose-950/50 p-3 text-sm text-rose-200">{error}</div>}

      {status && (
        <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <div className="jarvis-panel rounded-xl p-4">
            <div className="text-xs uppercase text-slate-400">Registered Modules</div>
            <div className="mt-1 text-2xl font-bold">{status.total_modules}</div>
          </div>
          <div className="jarvis-panel rounded-xl p-4">
            <div className="text-xs uppercase text-slate-400">Enabled</div>
            <div className="mt-1 text-2xl font-bold text-[#25E6A2]">{status.enabled_modules}</div>
          </div>
          <div className="jarvis-panel rounded-xl p-4">
            <div className="text-xs uppercase text-slate-400">Cross-Module Conflicts</div>
            <div className="mt-1 text-2xl font-bold text-amber-400">{status.cross_module_conflicts}</div>
          </div>
          <div className="jarvis-panel rounded-xl p-4">
            <div className="text-xs uppercase text-slate-400">Pending Approvals</div>
            <div className="mt-1 text-2xl font-bold text-[#9868FF]">{status.pending_approvals}</div>
          </div>
        </section>
      )}

      <form onSubmit={handleScan} className="jarvis-panel flex flex-wrap items-center gap-3 rounded-xl p-4">
        <FolderSearch className="h-5 w-5 text-[#00D9FF]" />
        <input
          value={folder}
          onChange={(e) => setFolder(e.target.value)}
          className="min-w-[260px] flex-1 rounded-lg border border-slate-700 bg-[#050B16] px-3 py-2 text-sm"
          placeholder="/home/roshan/Downloads/module-jarvis"
        />
        <select
          value={arch}
          onChange={(e) => setArch(e.target.value)}
          className="rounded-lg border border-slate-700 bg-[#050B16] px-3 py-2 text-sm"
        >
          <option value="arm64">Linux ARM64 (Pi 5)</option>
          <option value="x86_64">Linux x86_64</option>
        </select>
        <button type="submit" className="rounded-lg bg-gradient-to-r from-[#00D9FF] to-[#218BFF] px-4 py-2 text-sm font-bold text-[#050B16]">
          Scan Archives
        </button>
      </form>

      <div className="grid gap-5 lg:grid-cols-2">
        <div className="jarvis-panel rounded-xl p-4">
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-[#00D9FF]">
            <ShieldAlert className="h-4 w-4" /> Module Registry ({modules.length})
          </div>
          <div className="space-y-2">
            {modules.map((m) => (
              <div key={m.module_id} className="rounded-lg border border-cyan-500/20 bg-[#050B16]/70 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <div className="font-semibold text-[#F0F8FF]">{m.name}</div>
                    <div className="text-xs text-slate-400">
                      {m.module_id} · v{m.version} · {m.integration_status}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="rounded-full bg-[#9868FF]/20 px-2 py-0.5 text-xs font-semibold text-[#9868FF]">
                      {m.health_status}
                    </span>
                    <button
                      onClick={() => setInspector(JSON.stringify(m, null, 2))}
                      className="rounded border border-cyan-400/30 px-2 py-1 text-xs"
                    >
                      Details
                    </button>
                    <button
                      onClick={async () => {
                        await extensionApi.toggleModule(m.module_id, !m.enabled);
                        await refresh();
                      }}
                      className="rounded bg-[#25E6A2]/20 px-2 py-1 text-xs font-semibold text-[#25E6A2]"
                    >
                      {m.enabled ? "Disable" : "Enable"}
                    </button>
                    <button
                      onClick={async () => {
                        const res = await extensionApi.probeHealth(m.module_id);
                        setInspector(JSON.stringify(res, null, 2));
                        await refresh();
                      }}
                      className="inline-flex items-center gap-1 rounded bg-[#218BFF]/20 px-2 py-1 text-xs text-[#00D9FF]"
                    >
                      <HeartPulse className="h-3 w-3" /> Probe
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="jarvis-panel rounded-xl p-4">
          <div className="mb-3 text-sm font-semibold uppercase tracking-wider text-[#00D9FF]">
            Compatibility & Dry-Run Plan Inspector
          </div>
          <pre className="max-h-96 overflow-auto rounded-lg border border-cyan-500/20 bg-[#050B16]/80 p-3 font-mono text-xs text-sky-100">
            {inspector}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
