import React, { useState } from 'react';
import { Cpu, Pause, Play, Rocket, Sliders } from 'lucide-react';
import { EngineStatus } from '../services/api';

interface Props {
  status: EngineStatus | null;
  onTogglePause: () => Promise<void>;
  onUpdateLimit: (limit: number) => Promise<void>;
  onLaunchDemo: () => Promise<void>;
}

export const HeaderBar: React.FC<Props> = ({ status, onTogglePause, onUpdateLimit, onLaunchDemo }) => {
  const [limit, setLimit] = useState<number>(status?.max_concurrency ?? 4);

  return (
    <header className="jarvis-glass rounded-2xl p-5 mb-5 flex flex-wrap items-center justify-between gap-4">
      <div className="flex items-center gap-3.5">
        <div className="w-11 h-11 rounded-full bg-gradient-to-br from-[#00D9FF] via-[#218BFF] to-[#9868FF] flex items-center justify-center shadow-[0_0_20px_rgba(0,217,255,0.45)]">
          <Cpu className="w-6 h-6 text-[#050B16]" />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-wider text-[#F0F8FF]">
            JARVIS OS · MODULE 18 — MULTI-AGENT ORCHESTRATOR
          </h1>
          <p className="text-xs text-slate-400">
            DAG Dependency Scheduler · Bounded Concurrency · Human Approval Checkpoints · SQLite WAL
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2.5">
        <span className="px-3 py-1 rounded-full text-xs font-semibold border border-[#9868FF]/50 bg-[#9868FF]/15 text-[#D2BDFF]">
          SIMULATION MODE: REFERENCE AGENTS
        </span>
        <span
          className={`px-3 py-1 rounded-full text-xs font-semibold border ${
            status?.paused
              ? 'border-amber-400/50 bg-amber-400/15 text-amber-300'
              : 'border-[#25E6A2]/50 bg-[#25E6A2]/15 text-[#25E6A2]'
          }`}
        >
          ENGINE: {(status?.engine_state ?? 'loading').toUpperCase()}
        </span>
        <div className="flex items-center gap-1.5 bg-[#050B16]/70 border border-[#00D9FF]/25 rounded-lg px-2 py-1">
          <Sliders className="w-3.5 h-3.5 text-[#00D9FF]" />
          <input
            aria-label="Max concurrency"
            type="number"
            min={1}
            max={32}
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="w-12 bg-transparent text-xs text-center text-[#F0F8FF] focus:outline-none"
          />
          <button
            type="button"
            onClick={() => onUpdateLimit(limit)}
            className="text-xs px-2 py-0.5 rounded bg-[#218BFF]/25 hover:bg-[#00D9FF]/30 text-[#00D9FF]"
          >
            Set
          </button>
        </div>
        <button
          type="button"
          onClick={onTogglePause}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold border border-[#00D9FF]/30 bg-[#101E30] hover:border-[#00D9FF] transition"
        >
          {status?.paused ? <Play className="w-3.5 h-3.5 text-[#25E6A2]" /> : <Pause className="w-3.5 h-3.5 text-amber-300" />}
          {status?.paused ? 'Resume' : 'Pause'}
        </button>
        <button
          type="button"
          onClick={onLaunchDemo}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-bold bg-gradient-to-r from-[#00D9FF] to-[#218BFF] text-[#050B16] hover:opacity-95 transition"
        >
          <Rocket className="w-3.5 h-3.5" />
          Launch Demo DAG
        </button>
      </div>
    </header>
  );
};
