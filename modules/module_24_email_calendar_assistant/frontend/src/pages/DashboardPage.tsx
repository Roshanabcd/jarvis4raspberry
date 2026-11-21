import React, { useEffect, useState } from 'react';

interface EmailItem {
  email_id: string;
  sender: string;
  subject: string;
  category: string;
  priority_score: number;
}

const API = '/api/v1/email-calendar';

export default function DashboardPage() {
  const [emails, setEmails] = useState<EmailItem[]>([]);

  useEffect(() => {
    fetch(`${API}/emails`)
      .then((r) => r.json())
      .then((d) => setEmails(d.emails || []))
      .catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-[#050B16] text-[#F0F8FF] p-6">
      <header className="flex flex-wrap items-center justify-between gap-4 bg-[#101E30] border border-[#00D9FF]/30 rounded-xl p-4 mb-6">
        <div>
          <h1 className="text-xl font-bold text-[#00D9FF]">JARVIS OS — Email &amp; Calendar Assistant (Module 24)</h1>
          <p className="text-xs text-slate-400">Smart inbox triage, approval-gated outbound drafts, conflict-checked calendar &amp; ICS export</p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-semibold border border-amber-400/50 bg-amber-400/10 text-amber-300">
          SIMULATED MAIL/CAL ADAPTER
        </span>
      </header>

      <section className="bg-[#101E30] border border-[#00D9FF]/25 rounded-xl p-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-[#00D9FF] mb-3">
          Triaged Inbox ({emails.length})
        </h2>
        <ul className="space-y-2 text-sm">
          {emails.map((e) => (
            <li key={e.email_id} className="p-3 rounded-lg bg-[#050B16] border border-slate-800 flex justify-between">
              <div>
                <div className="font-semibold">{e.subject}</div>
                <div className="text-xs text-slate-400 font-mono">{e.sender}</div>
              </div>
              <span className="text-xs text-[#25E6A2]">{e.category} ({e.priority_score})</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
