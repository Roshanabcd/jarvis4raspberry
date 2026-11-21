import React, { useCallback, useEffect, useState } from 'react';
import { AlertOctagon, Camera, CheckCircle2, Play, RotateCcw, ShieldCheck } from 'lucide-react';
import { ActionRecord, ApprovalRecord, AssistantStatus, computerAssistantApi } from '../services/api';

export const DashboardPage: React.FC = () => {
  const [status, setStatus] = useState<AssistantStatus | null>(null);
  const [actions, setActions] = useState<ActionRecord[]>([]);
  const [approvals, setApprovals] = useState<ApprovalRecord[]>([]);
  const [screenshotB64, setScreenshotB64] = useState<string | null>(null);
  const [actionType, setActionType] = useState('capture_screenshot');
  const [paramsText, setParamsText] = useState('{}');
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [st, acts, aprs] = await Promise.all([
        computerAssistantApi.getStatus(),
        computerAssistantApi.listActions(),
        computerAssistantApi.listApprovals(),
      ]);
      setStatus(st);
      setActions(acts.actions);
      setApprovals(aprs.approvals);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to reach Computer Assistant API');
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const capture = async () => {
    try {
      const act = await computerAssistantApi.executeAction('capture_screenshot', {});
      const shotId = act.result?.screenshot_id as string | undefined;
      if (shotId) {
        const shot = await computerAssistantApi.getScreenshot(shotId);
        setScreenshotB64(shot.image_b64);
      }
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Screenshot failed');
    }
  };

  const dispatch = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const parsed = JSON.parse(paramsText || '{}');
      await computerAssistantApi.executeAction(actionType, parsed);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed');
    }
  };

  return (
    <main className="max-w-[1440px] mx-auto p-5 space-y-5">
      <header className="jarvis-glass rounded-2xl p-5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <ShieldCheck className="w-8 h-8 text-[#00D9FF]" />
          <div>
            <h1 className="text-lg font-bold tracking-wider">JARVIS OS · MODULE 19 — AUTONOMOUS COMPUTER ASSISTANT</h1>
            <p className="text-xs text-slate-400">SafeDemoDesktopAdapter · Permission Policies · E-STOP · Dry-Run · Replay</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          <span className="px-3 py-1 rounded-full text-xs font-bold border border-[#9868FF]/50 bg-[#9868FF]/15 text-[#D2BDFF]">
            SAFE DEMO ADAPTER (SIMULATED)
          </span>
          <button
            type="button"
            onClick={() => computerAssistantApi.setDryRun(!status?.dry_run_mode).then(refresh)}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold border border-[#00D9FF]/30 bg-[#101E30]"
          >
            Dry-Run: {status?.dry_run_mode ? 'ON' : 'OFF'}
          </button>
          <button
            type="button"
            onClick={() =>
              (status?.estop_active
                ? computerAssistantApi.resetEstop()
                : computerAssistantApi.engageEstop('Operator E-STOP from UI')
              ).then(refresh)
            }
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-extrabold bg-rose-600 text-white"
          >
            <AlertOctagon className="w-4 h-4" />
            {status?.estop_active ? 'RESET E-STOP' : 'EMERGENCY STOP'}
          </button>
        </div>
      </header>

      {error && (
        <div role="alert" className="p-3 rounded-xl border border-rose-500/50 bg-rose-500/15 text-rose-200 text-xs">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <section className="lg:col-span-2 jarvis-glass rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-[#00D9FF]">PERMITTED DESKTOP VIEWPORT (SIMULATED)</h2>
            <button type="button" onClick={capture} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-[#00D9FF] text-[#050B16]">
              <Camera className="w-3.5 h-3.5" /> Capture Screenshot
            </button>
          </div>
          <div className="rounded-lg border border-[#00D9FF]/20 bg-[#030710] min-h-[240px] flex items-center justify-center overflow-hidden">
            {screenshotB64 ? (
              <img src={`data:image/png;base64,${screenshotB64}`} alt="Simulated desktop capture" className="w-full h-auto" />
            ) : (
              <span className="text-xs text-slate-400">Capture a screenshot to inspect the simulated desktop state.</span>
            )}
          </div>
        </section>

        <form onSubmit={dispatch} className="jarvis-glass rounded-xl p-4 space-y-3">
          <h2 className="text-sm font-bold text-[#00D9FF]">DISPATCH CONTROLLED ACTION</h2>
          <select value={actionType} onChange={(e) => setActionType(e.target.value)} className="w-full rounded-lg bg-[#050B16] border border-[#00D9FF]/25 px-3 py-2 text-xs">
            <option value="discover_apps">discover_apps (LOW)</option>
            <option value="capture_screenshot">capture_screenshot (LOW)</option>
            <option value="select_window">select_window (LOW)</option>
            <option value="mouse_click">mouse_click (MEDIUM)</option>
            <option value="keyboard_type">keyboard_type (MEDIUM)</option>
            <option value="keyboard_hotkey">keyboard_hotkey (HIGH)</option>
            <option value="launch_app">launch_app (HIGH)</option>
            <option value="file_list">file_list (LOW)</option>
            <option value="file_write">file_write (HIGH)</option>
          </select>
          <textarea rows={4} value={paramsText} onChange={(e) => setParamsText(e.target.value)} className="w-full rounded-lg bg-[#050B16] border border-[#00D9FF]/25 px-3 py-2 text-xs font-mono" />
          <button type="submit" className="w-full inline-flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-bold bg-gradient-to-r from-[#00D9FF] to-[#218BFF] text-[#050B16]">
            <Play className="w-3.5 h-3.5" /> Execute / Queue Action
          </button>
        </form>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <section className="jarvis-glass rounded-xl p-4">
          <h2 className="text-sm font-bold text-[#00D9FF] mb-3">HUMAN APPROVAL REQUESTS</h2>
          <div className="space-y-2">
            {approvals.map((ap) => (
              <div key={ap.approval_id} className="p-3 rounded-lg bg-[#050B16]/75 border border-white/10 text-xs flex items-center justify-between gap-2">
                <div>
                  <div className="font-semibold">{ap.action_type} ({ap.status})</div>
                  <div className="text-slate-400">{ap.prompt}</div>
                </div>
                {ap.status === 'pending' && (
                  <div className="flex gap-1.5">
                    <button type="button" onClick={() => computerAssistantApi.decideApproval(ap.approval_id, true).then(refresh)} className="px-2.5 py-1 rounded bg-[#25E6A2]/20 text-[#25E6A2]">
                      <CheckCircle2 className="w-3.5 h-3.5 inline mr-1" />Approve
                    </button>
                    <button type="button" onClick={() => computerAssistantApi.decideApproval(ap.approval_id, false).then(refresh)} className="px-2.5 py-1 rounded bg-rose-500/20 text-rose-300">
                      Reject
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        <section className="jarvis-glass rounded-xl p-4">
          <h2 className="text-sm font-bold text-[#00D9FF] mb-3">ACTION HISTORY &amp; DRY-RUN REPLAY</h2>
          <div className="space-y-2 max-h-72 overflow-y-auto">
            {actions.map((a) => (
              <div key={a.action_id} className="p-2.5 rounded-lg bg-[#050B16]/75 border border-white/10 text-xs flex items-center justify-between">
                <div>
                  <span className="font-semibold text-[#F0F8FF]">{a.action_type}</span>{' '}
                  <span className="text-slate-400">· {a.status} · {a.duration_ms}ms</span>
                </div>
                <button type="button" onClick={() => computerAssistantApi.replay([a.action_id], true).then(refresh)} className="inline-flex items-center gap-1 px-2 py-1 rounded bg-[#218BFF]/20 text-[#00D9FF]">
                  <RotateCcw className="w-3 h-3" /> Replay
                </button>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
};
