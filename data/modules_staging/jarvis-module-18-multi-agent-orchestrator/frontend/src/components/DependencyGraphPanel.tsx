import React from 'react';
import { DagGraph } from '../services/api';

interface Props {
  dag: DagGraph;
}

export const DependencyGraphPanel: React.FC<Props> = ({ dag }) => {
  if (!dag.nodes.length) {
    return (
      <div className="jarvis-glass rounded-xl p-4 mt-4">
        <h2 className="text-sm font-bold tracking-wider text-[#00D9FF] mb-2">DEPENDENCY GRAPH (DAG)</h2>
        <p className="text-xs text-slate-400 py-6 text-center">No task nodes in graph yet.</p>
      </div>
    );
  }

  const cols = Math.min(4, dag.nodes.length);
  const pos: Record<string, { x: number; y: number }> = {};
  dag.nodes.forEach((n, i) => {
    pos[n.task_id] = { x: 20 + (i % cols) * 215, y: 20 + Math.floor(i / cols) * 86 };
  });
  const height = Math.max(150, Math.ceil(dag.nodes.length / cols) * 90 + 20);

  return (
    <div className="jarvis-glass rounded-xl p-4 mt-4 overflow-x-auto">
      <h2 className="text-sm font-bold tracking-wider text-[#00D9FF] mb-3">DEPENDENCY GRAPH (DAG)</h2>
      <svg width={cols * 220 + 20} height={height}>
        {dag.edges.map((e) => {
          const s = pos[e.source];
          const t = pos[e.target];
          if (!s || !t) return null;
          return (
            <line
              key={`${e.source}-${e.target}`}
              x1={s.x + 95}
              y1={s.y + 30}
              x2={t.x + 95}
              y2={t.y + 30}
              stroke="#00D9FF"
              strokeOpacity={0.55}
              strokeWidth={2}
            />
          );
        })}
        {dag.nodes.map((n) => {
          const p = pos[n.task_id];
          const stroke =
            n.status === 'completed'
              ? '#25E6A2'
              : n.status === 'awaiting_approval'
              ? '#F5B041'
              : n.status === 'failed'
              ? '#FF5C77'
              : '#00D9FF';
          return (
            <g key={n.task_id} transform={`translate(${p.x},${p.y})`}>
              <rect width={190} height={58} rx={10} fill="#101E30" stroke={stroke} strokeWidth={1.5} />
              <text x={10} y={22} fill="#F0F8FF" fontSize={11} fontWeight={700}>
                {n.title.slice(0, 22)}
              </text>
              <text x={10} y={42} fill={stroke} fontSize={10}>
                {n.status.toUpperCase()} · P{n.priority}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};
