import React from 'react';
import { motion } from 'framer-motion';
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { EngineStatus } from '../services/api';

interface Props {
  status: EngineStatus | null;
}

export const MetricsStrip: React.FC<Props> = ({ status }) => {
  const counts = status?.task_counts ?? {};
  const chartData = [
    { name: 'Queued', count: (counts.queued ?? 0) + (counts.pending ?? 0) },
    { name: 'Running', count: counts.running ?? 0 },
    { name: 'Approval', count: counts.awaiting_approval ?? 0 },
    { name: 'Completed', count: counts.completed ?? 0 },
    { name: 'Failed', count: counts.failed ?? 0 },
  ];

  const cards = [
    { label: 'Registered Agents', value: status?.agent_count ?? 0, color: 'text-[#00D9FF]' },
    { label: 'Active / Max Workers', value: `${status?.active_workers ?? 0} / ${status?.max_concurrency ?? 4}`, color: 'text-[#218BFF]' },
    { label: 'Completed Tasks', value: counts.completed ?? 0, color: 'text-[#25E6A2]' },
    { label: 'Pending Approvals', value: status?.pending_approvals ?? 0, color: 'text-amber-300' },
    { label: 'Agent Messages', value: status?.total_messages ?? 0, color: 'text-[#9868FF]' },
  ];

  return (
    <section className="grid grid-cols-1 lg:grid-cols-6 gap-4 mb-5">
      <div className="lg:col-span-4 grid grid-cols-2 sm:grid-cols-5 gap-3">
        {cards.map((c) => (
          <motion.div
            key={c.label}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="jarvis-glass rounded-xl p-4"
          >
            <div className="text-[11px] uppercase tracking-wider text-slate-400">{c.label}</div>
            <div className={`text-2xl font-bold mt-1 ${c.color}`}>{c.value}</div>
          </motion.div>
        ))}
      </div>
      <div className="lg:col-span-2 jarvis-glass rounded-xl p-3 h-28">
        <div className="text-[11px] uppercase tracking-wider text-slate-400 mb-1">Task Distribution</div>
        <ResponsiveContainer width="100%" height="80%">
          <BarChart data={chartData}>
            <XAxis dataKey="name" tick={{ fill: '#8FA8C8', fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis hide allowDecimals={false} />
            <Tooltip contentStyle={{ background: '#101E30', border: '1px solid #00D9FF', fontSize: 12 }} />
            <Bar dataKey="count" fill="#00D9FF" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
};
