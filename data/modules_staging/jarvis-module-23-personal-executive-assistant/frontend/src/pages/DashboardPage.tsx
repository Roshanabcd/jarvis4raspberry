import React, { useEffect, useState } from 'react';

interface Task {
  task_id: string;
  title: string;
  quadrant: string;
  priority: string;
  status: string;
}

const API = '/api/v1/executive-assistant';

export default function DashboardPage() {
  const [summary, setSummary] = useState('Loading daily executive brief...');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [title, setTitle] = useState('');

  async function refresh() {
    try {
      const [br, ts] = await Promise.all([
        fetch(`${API}/briefing`).then((r) => r.json()),
        fetch(`${API}/tasks`).then((r) => r.json()),
      ]);
      setSummary(br.executive_summary || 'Ready.');
      setTasks(ts.tasks || []);
    } catch {
      setSummary('Backend unreachable on port 8123.');
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function createTask() {
    if (!title.trim()) return;
    await fetch(`${API}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, urgent: true, important: true, priority: 'p1' }),
    });
    setTitle('');
    refresh();
  }

  return (
    <div className="min-h-screen bg-[#050B16] text-[#F0F8FF] p-6">
      <header className="flex flex-wrap items-center justify-between gap-4 bg-[#101E30] border border-[#00D9FF]/30 rounded-xl p-4 mb-5">
        <div>
          <h1 className="text-xl font-bold text-[#00D9FF]">JARVIS OS — Personal Executive Assistant (Module 23)</h1>
          <p className="text-xs text-slate-400">Daily briefings, Eisenhower priority matrix, time blocking &amp; habit streaks</p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-semibold border border-amber-400/50 bg-amber-400/10 text-amber-300">
          LOCAL BRIEF SYNTHESIZER
        </span>
      </header>

      <div className="bg-[#101E30] border border-[#00D9FF]/30 rounded-xl p-4 mb-5 text-sm">{summary}</div>

      <section className="bg-[#101E30] border border-[#00D9FF]/25 rounded-xl p-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-[#00D9FF] mb-3">
          Priority Tasks ({tasks.length})
        </h2>
        <div className="flex gap-2 mb-4">
          <input
            aria-label="Task Title"
            className="flex-1 bg-[#050B16] border border-slate-700 rounded-lg px-3 py-2 text-sm"
            placeholder="Add executive action item..."
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <button onClick={createTask} className="px-4 py-2 rounded-lg bg-[#00D9FF] text-[#050B16] font-semibold text-sm">
            Add Task
          </button>
        </div>
        <ul className="space-y-2 text-sm">
          {tasks.map((t) => (
            <li key={t.task_id} className="p-3 rounded-lg bg-[#050B16] border border-slate-800 flex justify-between">
              <span>{t.title}</span>
              <span className="text-xs text-[#25E6A2]">{t.quadrant} · {t.status}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
