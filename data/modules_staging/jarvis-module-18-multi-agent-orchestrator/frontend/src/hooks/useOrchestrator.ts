import { useCallback, useEffect, useState } from 'react';
import {
  AgentMessageRecord,
  AgentRecord,
  ApprovalRecord,
  DagGraph,
  EngineStatus,
  ExecutionLogRecord,
  orchestratorApi,
  TaskRecord,
} from '../services/api';

export function useOrchestrator(pollMs = 2500) {
  const [status, setStatus] = useState<EngineStatus | null>(null);
  const [agents, setAgents] = useState<AgentRecord[]>([]);
  const [tasks, setTasks] = useState<TaskRecord[]>([]);
  const [approvals, setApprovals] = useState<ApprovalRecord[]>([]);
  const [messages, setMessages] = useState<AgentMessageRecord[]>([]);
  const [logs, setLogs] = useState<ExecutionLogRecord[]>([]);
  const [dag, setDag] = useState<DagGraph>({ workflow_id: 'all', nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [s, a, t, ap, m, l, d] = await Promise.all([
        orchestratorApi.getStatus(),
        orchestratorApi.listAgents(),
        orchestratorApi.listTasks(),
        orchestratorApi.listApprovals(),
        orchestratorApi.listMessages(),
        orchestratorApi.listLogs(),
        orchestratorApi.getDag(),
      ]);
      setStatus(s);
      setAgents(a.agents);
      setTasks(t.tasks);
      setApprovals(ap.approvals);
      setMessages(m.messages);
      setLogs(l.logs);
      setDag(d);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reach orchestrator API');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, pollMs);
    return () => clearInterval(timer);
  }, [refresh, pollMs]);

  return { status, agents, tasks, approvals, messages, logs, dag, loading, error, refresh, setError };
}
