import React, { useState } from 'react';
import { HeaderBar } from '../components/HeaderBar';
import { MetricsStrip } from '../components/MetricsStrip';
import { TaskQueuePanel } from '../components/TaskQueuePanel';
import { DependencyGraphPanel } from '../components/DependencyGraphPanel';
import { AgentRegistryPanel } from '../components/AgentRegistryPanel';
import { ApprovalQueuePanel } from '../components/ApprovalQueuePanel';
import { CommsAndLogsPanel } from '../components/CommsAndLogsPanel';
import { useOrchestrator } from '../hooks/useOrchestrator';
import { orchestratorApi } from '../services/api';

type TabKey = 'tasks' | 'agents' | 'approvals' | 'comms';

export const DashboardPage: React.FC = () => {
  const { status, agents, tasks, approvals, messages, logs, dag, loading, error, refresh, setError } =
    useOrchestrator();
  const [tab, setTab] = useState<TabKey>('tasks');

  const safeRun = async (fn: () => Promise<unknown>) => {
    try {
      await fn();
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed');
    }
  };

  return (
    <main className="max-w-[1440px] mx-auto p-5">
      <HeaderBar
        status={status}
        onTogglePause={() => safeRun(() => (status?.paused ? orchestratorApi.resumeEngine() : orchestratorApi.pauseEngine()))}
        onUpdateLimit={(n) => safeRun(() => orchestratorApi.setMaxConcurrency(n))}
        onLaunchDemo={() => safeRun(() => orchestratorApi.launchDemo())}
      />

      {error && (
        <div role="alert" className="mb-4 p-3 rounded-xl border border-rose-500/50 bg-rose-500/15 text-rose-200 text-xs">
          {error}
        </div>
      )}

      <MetricsStrip status={status} />

      <nav className="flex flex-wrap gap-2 mb-4" aria-label="Orchestrator sections">
        {(
          [
            ['tasks', 'Tasks & DAG'],
            ['agents', 'Agent Registry'],
            ['approvals', `Approvals (${status?.pending_approvals ?? 0})`],
            ['comms', 'Agent Comms & Logs'],
          ] as [TabKey, string][]
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`px-4 py-2 rounded-lg text-xs font-semibold border transition ${
              tab === key
                ? 'border-[#00D9FF] bg-[#00D9FF]/20 text-[#00D9FF]'
                : 'border-white/10 bg-[#101E30]/70 text-slate-300 hover:border-[#00D9FF]/40'
            }`}
          >
            {label}
          </button>
        ))}
      </nav>

      {loading && !status ? (
        <div className="jarvis-glass rounded-xl p-10 text-center text-sm text-slate-400">
          Initializing JARVIS Multi-Agent Orchestrator...
        </div>
      ) : (
        <>
          {tab === 'tasks' && (
            <>
              <TaskQueuePanel
                tasks={tasks}
                onCreateTask={(p) => safeRun(() => orchestratorApi.createTask(p))}
                onPauseTask={(id) => safeRun(() => orchestratorApi.pauseTask(id))}
                onResumeTask={(id) => safeRun(() => orchestratorApi.resumeTask(id))}
                onCancelTask={(id) => safeRun(() => orchestratorApi.cancelTask(id))}
              />
              <DependencyGraphPanel dag={dag} />
            </>
          )}
          {tab === 'agents' && (
            <AgentRegistryPanel
              agents={agents}
              onRegister={(p) => safeRun(() => orchestratorApi.registerAgent(p))}
              onToggleStatus={(id, s) => safeRun(() => orchestratorApi.updateAgent(id, { status: s }))}
            />
          )}
          {tab === 'approvals' && (
            <ApprovalQueuePanel
              approvals={approvals}
              onDecide={(id, ok) => safeRun(() => orchestratorApi.decideApproval(id, ok))}
            />
          )}
          {tab === 'comms' && (
            <CommsAndLogsPanel
              messages={messages}
              logs={logs}
              onSendMessage={(content) =>
                safeRun(() =>
                  orchestratorApi.sendMessage({
                    sender_agent_id: 'operator',
                    recipient_agent_id: 'broadcast',
                    content,
                  })
                )
              }
            />
          )}
        </>
      )}
    </main>
  );
};
