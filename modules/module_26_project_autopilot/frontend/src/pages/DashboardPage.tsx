import React, { useEffect, useState } from 'react';

interface Project {
  project_id: string;
  name: string;
  goal: string;
  tech_stack: string[];
  status: string;
  workspace_path?: string | null;
}

interface Task {
  task_id: string;
  title: string;
  status: string;
  requires_approval: boolean;
  estimated_minutes: number;
  output_summary?: string | null;
}

const API_BASE = '/api/v1/project-autopilot';

export const DashboardPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selected, setSelected] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [progress, setProgress] = useState(0);
  const [name, setName] = useState('');
  const [goal, setGoal] = useState('');

  const loadProjects = async () => {
    const res = await fetch(`${API_BASE}/projects`);
    if (res.ok) {
      const data = await res.json();
      setProjects(data.projects || []);
    }
  };

  const selectProject = async (id: string) => {
    const res = await fetch(`${API_BASE}/projects/${id}`);
    if (res.ok) {
      const b = await res.json();
      setSelected(b.project);
      setTasks(b.tasks || []);
      setProgress(b.progress_pct || 0);
    }
  };

  useEffect(() => {
    void loadProjects();
  }, []);

  const createProject = async () => {
    if (!name.trim() || !goal.trim()) return;
    const res = await fetch(`${API_BASE}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name.trim(), goal: goal.trim(), tech_stack: ['Python', 'FastAPI'], dry_run: true, auto_plan: true }),
    });
    if (res.ok) {
      const b = await res.json();
      setName('');
      setGoal('');
      await loadProjects();
      await selectProject(b.project.project_id);
    }
  };

  const advance = async () => {
    if (!selected) return;
    await fetch(`${API_BASE}/projects/${selected.project_id}/advance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ max_steps: 2 }),
    });
    await selectProject(selected.project_id);
    await loadProjects();
  };

  return (
    <div className="min-h-screen bg-jarvis-bg text-jarvis-text p-6">
      <header className="flex items-center justify-between border-b border-jarvis-cyan/25 pb-4 mb-6">
        <div>
          <h1 className="text-xl font-bold text-jarvis-cyan">JARVIS OS — Module 26: Project Autopilot</h1>
          <p className="text-xs text-slate-400">Autonomous Milestone Decomposition, Dependency Runner &amp; Approval Gates</p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs border border-amber-400/50 text-amber-300 bg-amber-500/10">
          Simulated Local Planner
        </span>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="bg-jarvis-panel border border-jarvis-cyan/20 rounded-xl p-4 space-y-3">
          <h2 className="text-sm font-semibold text-jarvis-cyan">Projects</h2>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Project name..." className="w-full bg-jarvis-bg border border-slate-700 rounded-lg px-3 py-2 text-sm" />
          <textarea value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="Engineering goal..." className="w-full h-20 bg-jarvis-bg border border-slate-700 rounded-lg p-2 text-sm" />
          <button onClick={createProject} className="w-full py-2 rounded-lg bg-jarvis-cyan text-slate-950 font-semibold text-sm">Create &amp; Auto-Plan</button>
          <div className="space-y-2 pt-2">
            {projects.map((p) => (
              <button key={p.project_id} onClick={() => selectProject(p.project_id)} className="w-full text-left p-3 rounded-lg bg-jarvis-bg border border-slate-700 hover:border-jarvis-cyan">
                <div className="font-medium text-sm">{p.name}</div>
                <div className="text-xs text-slate-400">{p.status}</div>
              </button>
            ))}
          </div>
        </section>

        <section className="lg:col-span-2 bg-jarvis-panel border border-jarvis-cyan/20 rounded-xl p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-jarvis-cyan">{selected ? `${selected.name} (${progress}%)` : 'Select a Project'}</h2>
            {selected && (
              <button onClick={advance} className="px-4 py-1.5 rounded-lg bg-jarvis-blue text-white text-sm font-semibold">
                Run Next 2 Steps
              </button>
            )}
          </div>
          <div className="space-y-2">
            {tasks.map((t) => (
              <div key={t.task_id} className="p-3 rounded-lg bg-jarvis-bg border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium">{t.title}</div>
                  <div className="text-xs text-slate-400">{t.output_summary || `${t.estimated_minutes}m`}</div>
                </div>
                <span className="text-xs px-2 py-1 rounded bg-slate-800 text-jarvis-cyan">{t.status}</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
};
