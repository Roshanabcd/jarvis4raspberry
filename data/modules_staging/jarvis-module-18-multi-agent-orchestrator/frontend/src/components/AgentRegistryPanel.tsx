import React, { useState } from 'react';
import { AgentRecord } from '../services/api';

interface Props {
  agents: AgentRecord[];
  onRegister: (payload: Record<string, unknown>) => Promise<void>;
  onToggleStatus: (agentId: string, nextStatus: string) => Promise<void>;
}

export const AgentRegistryPanel: React.FC<Props> = ({ agents, onRegister, onToggleStatus }) => {
  const [name, setName] = useState('');
  const [role, setRole] = useState('');
  const [caps, setCaps] = useState('code_analysis,security_scan');
  const [handlerType, setHandlerType] = useState('code_analysis');
  const [maxConcurrency, setMaxConcurrency] = useState(2);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !role.trim()) return;
    await onRegister({
      name: name.trim(),
      role: role.trim(),
      capabilities: caps.split(',').map((s) => s.trim()).filter(Boolean),
      handler_type: handlerType,
      max_concurrency: maxConcurrency,
    });
    setName('');
    setRole('');
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="lg:col-span-2 jarvis-glass rounded-xl p-4 overflow-x-auto">
        <h2 className="text-sm font-bold tracking-wider text-[#00D9FF] mb-3">REGISTERED AGENTS</h2>
        <table className="w-full text-xs">
          <thead>
            <tr className="text-slate-400 border-b border-white/10">
              <th className="py-2 text-left">Agent</th>
              <th className="py-2 text-left">Capabilities</th>
              <th className="py-2 text-left">Load</th>
              <th className="py-2 text-left">Mode</th>
              <th className="py-2 text-left">Control</th>
            </tr>
          </thead>
          <tbody>
            {agents.map((a) => (
              <tr key={a.agent_id} className="border-b border-white/5">
                <td className="py-2.5">
                  <div className="font-semibold text-[#F0F8FF]">{a.name}</div>
                  <div className="text-[11px] text-slate-400">{a.agent_id} · {a.role}</div>
                </td>
                <td className="py-2.5 text-slate-300">{a.capabilities.join(', ')}</td>
                <td className="py-2.5">{a.active_tasks}/{a.max_concurrency} (ok:{a.completed_tasks})</td>
                <td className="py-2.5">
                  <span className={`px-2 py-0.5 rounded-full text-[11px] ${a.simulated ? 'bg-[#9868FF]/20 text-[#D2BDFF]' : 'bg-[#25E6A2]/20 text-[#25E6A2]'}`}>
                    {a.simulated ? 'SIMULATED' : 'LOCAL'}
                  </span>
                </td>
                <td className="py-2.5">
                  <button
                    type="button"
                    onClick={() => onToggleStatus(a.agent_id, a.status === 'paused' ? 'online' : 'paused')}
                    className="px-2.5 py-1 rounded bg-[#218BFF]/20 text-[#00D9FF]"
                  >
                    {a.status === 'paused' ? 'Resume' : 'Pause'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <form onSubmit={submit} className="jarvis-glass rounded-xl p-4 space-y-3">
        <h2 className="text-sm font-bold tracking-wider text-[#00D9FF]">REGISTER AGENT</h2>
        <input required value={name} onChange={(e) => setName(e.target.value)} placeholder="Agent Name" className="w-full rounded-lg bg-[#050B16]/85 border border-[#00D9FF]/25 px-3 py-2 text-xs" />
        <input required value={role} onChange={(e) => setRole(e.target.value)} placeholder="Agent Role" className="w-full rounded-lg bg-[#050B16]/85 border border-[#00D9FF]/25 px-3 py-2 text-xs" />
        <input value={caps} onChange={(e) => setCaps(e.target.value)} placeholder="Capabilities" className="w-full rounded-lg bg-[#050B16]/85 border border-[#00D9FF]/25 px-3 py-2 text-xs" />
        <div className="grid grid-cols-2 gap-2">
          <select value={handlerType} onChange={(e) => setHandlerType(e.target.value)} className="rounded-lg bg-[#050B16]/85 border border-[#00D9FF]/25 px-3 py-2 text-xs">
            <option value="research">research</option>
            <option value="code_analysis">code_analysis</option>
            <option value="data_aggregator">data_aggregator</option>
            <option value="deploy">deploy</option>
          </select>
          <input type="number" min={1} max={16} value={maxConcurrency} onChange={(e) => setMaxConcurrency(Number(e.target.value))} className="rounded-lg bg-[#050B16]/85 border border-[#00D9FF]/25 px-3 py-2 text-xs" />
        </div>
        <button type="submit" className="w-full py-2 rounded-lg text-xs font-bold bg-gradient-to-r from-[#00D9FF] to-[#218BFF] text-[#050B16]">
          Register Agent
        </button>
      </form>
    </div>
  );
};
