import React, { useEffect, useState } from 'react';

interface Session {
  session_id: string;
  name: string;
  current_url: string;
  status: string;
}

interface Approval {
  approval_id: string;
  session_id: string;
  url: string;
  form_id: string;
  status: string;
  fields: Record<string, string>;
}

interface Workflow {
  task_id: string;
  name: string;
  status: string;
  current_step: number;
  steps: Array<{ action: string }>;
}

const API = '/api/v1/browser-agent';

export default function DashboardPage() {
  const [simulated, setSimulated] = useState(true);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [urlInput, setUrlInput] = useState('https://docs.jarvis.local/overview');
  const [notice, setNotice] = useState<string>('');

  async function refresh() {
    try {
      const [st, ss, ap, wf] = await Promise.all([
        fetch(`${API}/status`).then((r) => r.json()),
        fetch(`${API}/sessions`).then((r) => r.json()),
        fetch(`${API}/approvals`).then((r) => r.json()),
        fetch(`${API}/workflows`).then((r) => r.json()),
      ]);
      setSimulated(Boolean(st.simulated));
      setSessions(ss.sessions || []);
      setApprovals(ap.approvals || []);
      setWorkflows(wf.workflows || []);
    } catch {
      setNotice('Backend API unreachable. Start FastAPI on port 8121.');
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function createSession() {
    const res = await fetch(`${API}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'React Operator Session', start_url: urlInput }),
    });
    if (res.ok) {
      setNotice('Created browser session.');
      refresh();
    } else {
      const err = await res.json();
      setNotice(err?.error?.message || 'Failed to create session.');
    }
  }

  async function decideApproval(id: string, approved: boolean) {
    await fetch(`${API}/approvals/${id}/decide`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approved, decided_by: 'react-operator' }),
    });
    refresh();
  }

  return (
    <div className="min-h-screen bg-[#050B16] text-[#F0F8FF] p-6">
      <header className="flex flex-wrap items-center justify-between gap-4 bg-[#101E30] border border-[#00D9FF]/30 rounded-xl p-4 mb-6">
        <div>
          <h1 className="text-xl font-bold text-[#00D9FF] tracking-wide">
            JARVIS OS — Intelligent Browser Agent (Module 21)
          </h1>
          <p className="text-xs text-slate-400">
            Policy-governed navigation, real HTML DOM extraction, screenshot analysis &amp; approval gates
          </p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-semibold border border-amber-400/50 bg-amber-400/10 text-amber-300">
          {simulated ? 'SIMULATED ADAPTER' : 'LIVE ADAPTER'}
        </span>
      </header>

      {notice && (
        <div className="mb-4 p-3 rounded-lg bg-[#101E30] border border-[#00D9FF]/40 text-sm">
          {notice}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="bg-[#101E30] border border-[#00D9FF]/25 rounded-xl p-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-[#00D9FF] mb-3">
            Browser Sessions ({sessions.length})
          </h2>
          <div className="flex gap-2 mb-4">
            <input
              aria-label="Start URL"
              className="flex-1 bg-[#050B16] border border-slate-700 rounded-lg px-3 py-2 text-sm"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
            />
            <button
              onClick={createSession}
              className="px-4 py-2 rounded-lg bg-[#00D9FF] text-[#050B16] font-semibold text-sm"
            >
              New Session
            </button>
          </div>
          <ul className="space-y-2 text-sm">
            {sessions.map((s) => (
              <li key={s.session_id} className="p-3 rounded-lg bg-[#050B16] border border-slate-800">
                <div className="font-semibold">{s.name}</div>
                <div className="text-xs text-[#00D9FF] font-mono">{s.current_url}</div>
              </li>
            ))}
          </ul>
        </section>

        <section className="bg-[#101E30] border border-[#00D9FF]/25 rounded-xl p-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-[#00D9FF] mb-3">
            Pending Form Approvals ({approvals.filter((a) => a.status === 'pending').length})
          </h2>
          <ul className="space-y-2 text-sm mb-6">
            {approvals.map((a) => (
              <li key={a.approval_id} className="p-3 rounded-lg bg-[#050B16] border border-slate-800">
                <div className="flex justify-between">
                  <span className="font-semibold">Form: {a.form_id}</span>
                  <span className="text-xs text-amber-300">{a.status}</span>
                </div>
                <div className="text-xs font-mono text-slate-400">{a.url}</div>
                {a.status === 'pending' && (
                  <div className="flex gap-2 mt-2">
                    <button
                      onClick={() => decideApproval(a.approval_id, true)}
                      className="px-3 py-1 rounded bg-[#25E6A2]/20 border border-[#25E6A2] text-xs"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => decideApproval(a.approval_id, false)}
                      className="px-3 py-1 rounded bg-rose-500/20 border border-rose-400 text-xs"
                    >
                      Reject
                    </button>
                  </div>
                )}
              </li>
            ))}
          </ul>

          <h2 className="text-sm font-semibold uppercase tracking-wider text-[#9868FF] mb-2">
            Multi-Page Workflows ({workflows.length})
          </h2>
          <ul className="space-y-2 text-sm">
            {workflows.map((w) => (
              <li key={w.task_id} className="p-2 rounded bg-[#050B16] border border-slate-800 flex justify-between">
                <span>{w.name}</span>
                <span className="text-xs text-[#00D9FF]">{w.status}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
