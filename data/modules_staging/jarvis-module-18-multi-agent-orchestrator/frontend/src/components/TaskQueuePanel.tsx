import React, { useState } from 'react';
import { TaskRecord } from '../services/api';

interface Props {
  tasks: TaskRecord[];
  onCreateTask: (payload: Record<string, unknown>) => Promise<void>;
  onPauseTask: (id: string) => Promise<void>;
  onResumeTask: (id: string) => Promise<void>;
  onCancelTask: (id: string) => Promise<void>;
}

export const TaskQueuePanel: React.FC<Props> = ({
  tasks,
  onCreateTask,
  onPauseTask,
  onResumeTask,
  onCancelTask,
}) => {
  const [title, setTitle] = useState('');
  const [workflowId, setWorkflowId] = useState('custom-workflow');
  const [priority, setPriority] = useState(2);
  const [capability, setCapability] = useState('research');
  const [dependsOn, setDependsOn] = useState('');
  const [requiresApproval, setRequiresApproval] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    await onCreateTask({
      title: title.trim(),
      workflow_id: workflowId.trim() || 'custom-workflow',
      priority,
      required_capability: capability,
      depends_on: dependsOn
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
      requires_approval: requiresApproval,
    });
    setTitle('');
    setDependsOn('');
    setRequiresApproval(false);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="lg:col-span-2 jarvis-glass rounded-xl p-4 overflow-x-auto">
        <h2 className="text-sm font-bold tracking-wider text-[#00D9FF] mb-3">TASK QUEUE &amp; EXECUTION CONTROL</h2>
        {tasks.length === 0 ? (
          <p className="text-sm text-slate-400 py-6 text-center">No tasks queued yet. Launch the Demo DAG or submit a task.</p>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="text-slate-400 border-b border-white/10">
                <th className="py-2 text-left">Task</th>
                <th className="py-2 text-left">Prio</th>
                <th className="py-2 text-left">Status</th>
                <th className="py-2 text-left">Agent</th>
                <th className="py-2 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((t) => (
                <tr key={t.task_id} className="border-b border-white/5">
                  <td className="py-2.5 pr-2">
                    <div className="font-semibold text-[#F0F8FF]">{t.title}</div>
                    <div className="text-[11px] text-slate-400">
                      {t.task_id} · {t.workflow_id}
                    </div>
                  </td>
                  <td className="py-2.5">P{t.priority}</td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded-full bg-[#00D9FF]/15 text-[#00D9FF] border border-[#00D9FF]/30">
                      {t.status}
                    </span>
                  </td>
                  <td className="py-2.5 text-slate-300">{t.assigned_agent_id ?? '—'}</td>
                  <td className="py-2.5 flex gap-1.5">
                    {t.status === 'paused' && (
                      <button type="button" onClick={() => onResumeTask(t.task_id)} className="px-2 py-0.5 rounded bg-[#25E6A2]/20 text-[#25E6A2]">
                        Resume
                      </button>
                    )}
                    {['pending', 'queued', 'running'].includes(t.status) && (
                      <button type="button" onClick={() => onPauseTask(t.task_id)} className="px-2 py-0.5 rounded bg-amber-400/20 text-amber-300">
                        Pause
                      </button>
                    )}
                    {!['completed', 'failed', 'cancelled'].includes(t.status) && (
                      <button type="button" onClick={() => onCancelTask(t.task_id)} className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300">
                        Cancel
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <form onSubmit={handleSubmit} className="jarvis-glass rounded-xl p-4 space-y-3">
        <h2 className="text-sm font-bold tracking-wider text-[#00D9FF]">CREATE ORCHESTRATED TASK</h2>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Task Title</label>
          <input
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., Audit Robotics Controller"
            className="w-full rounded-lg bg-[#050B16]/85 border border-[#00D9FF]/25 px-3 py-2 text-xs text-[#F0F8FF]"
          />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Workflow ID</label>
            <input
              value={workflowId}
              onChange={(e) => setWorkflowId(e.target.value)}
              className="w-full rounded-lg bg-[#050B16]/85 border border-[#00D9FF]/25 px-3 py-2 text-xs"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Priority</label>
            <select
              value={priority}
              onChange={(e) => setPriority(Number(e.target.value))}
              className="w-full rounded-lg bg-[#050B16]/85 border border-[#00D9FF]/25 px-3 py-2 text-xs"
            >
              <option value={1}>LOW (1)</option>
              <option value={2}>NORMAL (2)</option>
              <option value={3}>HIGH (3)</option>
              <option value={4}>CRITICAL (4)</option>
            </select>
          </div>
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Required Capability</label>
          <select
            value={capability}
            onChange={(e) => setCapability(e.target.value)}
            className="w-full rounded-lg bg-[#050B16]/85 border border-[#00D9FF]/25 px-3 py-2 text-xs"
          >
            <option value="research">research (simulated)</option>
            <option value="code_analysis">code_analysis (local)</option>
            <option value="aggregation">aggregation (local)</option>
            <option value="deploy">deploy (simulated)</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Depends On (comma-separated IDs)</label>
          <input
            value={dependsOn}
            onChange={(e) => setDependsOn(e.target.value)}
            placeholder="tsk_abc123, tsk_def456"
            className="w-full rounded-lg bg-[#050B16]/85 border border-[#00D9FF]/25 px-3 py-2 text-xs"
          />
        </div>
        <label className="flex items-center gap-2 text-xs text-slate-300">
          <input type="checkbox" checked={requiresApproval} onChange={(e) => setRequiresApproval(e.target.checked)} />
          Require Human Approval Checkpoint
        </label>
        <button
          type="submit"
          className="w-full py-2 rounded-lg text-xs font-bold bg-gradient-to-r from-[#00D9FF] to-[#218BFF] text-[#050B16]"
        >
          Submit Task to Queue
        </button>
      </form>
    </div>
  );
};
