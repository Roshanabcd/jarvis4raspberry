import React, { useEffect, useState } from 'react';

interface Meeting {
  meeting_id: string;
  title: string;
  meeting_date: string;
  participants: string[];
  agenda: string;
  status: string;
  summary?: {
    executive_overview: string;
    decisions: string[];
    risks: string[];
    speaker_stats: { speaker: string; word_count: number; share_pct: number }[];
  };
}

interface ActionItem {
  item_id: string;
  owner: string;
  description: string;
  due_hint?: string | null;
  status: 'open' | 'done';
}

const API_BASE = '/api/v1/meeting-assistant';

export const DashboardPage: React.FC = () => {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [selected, setSelected] = useState<Meeting | null>(null);
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [title, setTitle] = useState('');
  const [bulkTranscript, setBulkTranscript] = useState('');

  const loadMeetings = async () => {
    const res = await fetch(`${API_BASE}/meetings`);
    if (res.ok) {
      const data = await res.json();
      setMeetings(data.meetings || []);
    }
  };

  const selectMeeting = async (meetingId: string) => {
    const res = await fetch(`${API_BASE}/meetings/${meetingId}`);
    if (res.ok) {
      const data = await res.json();
      setSelected(data.meeting);
      setActions(data.action_items || []);
    }
  };

  useEffect(() => {
    void loadMeetings();
  }, []);

  const createMeeting = async () => {
    if (!title.trim()) return;
    const res = await fetch(`${API_BASE}/meetings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: title.trim(), meeting_date: '2026-11-20', participants: [], agenda: '' }),
    });
    if (res.ok) {
      const m = await res.json();
      setTitle('');
      await loadMeetings();
      await selectMeeting(m.meeting_id);
    }
  };

  const ingestAndAnalyze = async () => {
    if (!selected) return;
    if (bulkTranscript.trim()) {
      await fetch(`${API_BASE}/meetings/${selected.meeting_id}/transcript/bulk`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_transcript: bulkTranscript }),
      });
      setBulkTranscript('');
    }
    await fetch(`${API_BASE}/meetings/${selected.meeting_id}/analyze`, { method: 'POST' });
    await selectMeeting(selected.meeting_id);
    await loadMeetings();
  };

  return (
    <div className="min-h-screen bg-jarvis-bg text-jarvis-text p-6">
      <header className="flex items-center justify-between border-b border-jarvis-cyan/25 pb-4 mb-6">
        <div>
          <h1 className="text-xl font-bold text-jarvis-cyan">JARVIS OS — Module 25: AI Meeting Assistant</h1>
          <p className="text-xs text-slate-400">Speaker Diarization, Talk-Share Analytics, Decisions, Action Items &amp; Minutes</p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs border border-amber-400/50 text-amber-300 bg-amber-500/10">
          Simulated Local Synthesis
        </span>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="bg-jarvis-panel border border-jarvis-cyan/20 rounded-xl p-4 space-y-4">
          <h2 className="text-sm font-semibold text-jarvis-cyan">Meetings</h2>
          <div className="flex gap-2">
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="New meeting title..."
              className="flex-1 bg-jarvis-bg border border-slate-700 rounded-lg px-3 py-2 text-sm"
            />
            <button onClick={createMeeting} className="px-3 py-2 rounded-lg bg-jarvis-cyan text-slate-950 font-semibold text-sm">
              Create
            </button>
          </div>
          <div className="space-y-2">
            {meetings.map((m) => (
              <button
                key={m.meeting_id}
                onClick={() => selectMeeting(m.meeting_id)}
                className="w-full text-left p-3 rounded-lg bg-jarvis-bg/80 border border-slate-700 hover:border-jarvis-cyan"
              >
                <div className="font-medium text-sm">{m.title}</div>
                <div className="text-xs text-slate-400">{m.meeting_date} · {m.status}</div>
              </button>
            ))}
          </div>
        </section>

        <section className="lg:col-span-2 bg-jarvis-panel border border-jarvis-cyan/20 rounded-xl p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-jarvis-cyan">{selected ? selected.title : 'Select a Meeting'}</h2>
            {selected && (
              <a
                href={`${API_BASE}/meetings/${selected.meeting_id}/minutes.md`}
                target="_blank"
                rel="noreferrer"
                className="text-xs px-3 py-1.5 rounded-lg border border-jarvis-purple text-jarvis-purple"
              >
                Export Markdown Minutes
              </a>
            )}
          </div>
          <textarea
            value={bulkTranscript}
            onChange={(e) => setBulkTranscript(e.target.value)}
            placeholder="Paste transcript lines (Speaker: message)..."
            className="w-full h-28 bg-jarvis-bg border border-slate-700 rounded-lg p-3 text-sm"
          />
          <button onClick={ingestAndAnalyze} className="px-4 py-2 rounded-lg bg-jarvis-blue text-white font-semibold text-sm">
            Ingest &amp; Analyze Meeting
          </button>

          {selected?.summary && (
            <div className="space-y-3 pt-2 border-t border-slate-800">
              <p className="text-sm text-slate-200">{selected.summary.executive_overview}</p>
              <div>
                <h3 className="text-xs uppercase text-jarvis-cyan mb-1">Action Items ({actions.length})</h3>
                <ul className="space-y-1 text-sm">
                  {actions.map((a) => (
                    <li key={a.item_id} className="p-2 rounded bg-jarvis-bg border border-slate-800">
                      <strong className="text-jarvis-green">{a.owner}:</strong> {a.description}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
};
