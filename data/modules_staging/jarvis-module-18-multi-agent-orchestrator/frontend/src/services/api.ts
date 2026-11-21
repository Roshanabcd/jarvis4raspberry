export interface AgentRecord {
  agent_id: string;
  name: string;
  role: string;
  capabilities: string[];
  status: 'online' | 'busy' | 'paused' | 'offline';
  max_concurrency: number;
  active_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  handler_type: string;
  simulated: boolean;
  registered_at: string;
  last_heartbeat: string;
}

export interface TaskRecord {
  task_id: string;
  workflow_id: string;
  title: string;
  description: string;
  required_capability?: string | null;
  assigned_agent_id?: string | null;
  priority: number;
  status: string;
  depends_on: string[];
  payload: Record<string, unknown>;
  result?: Record<string, unknown> | null;
  error?: string | null;
  retries_attempted: number;
  max_retries: number;
  timeout_sec: number;
  requires_approval: boolean;
  approval_status?: string | null;
  created_at: string;
}

export interface ApprovalRecord {
  approval_id: string;
  task_id: string;
  workflow_id: string;
  prompt: string;
  status: 'pending' | 'approved' | 'rejected';
  decided_by?: string | null;
  comment?: string | null;
  created_at: string;
}

export interface AgentMessageRecord {
  message_id: string;
  sender_agent_id: string;
  recipient_agent_id: string;
  task_id?: string | null;
  workflow_id?: string | null;
  channel: string;
  content: string;
  created_at: string;
}

export interface ExecutionLogRecord {
  log_id: number;
  task_id?: string | null;
  agent_id?: string | null;
  level: string;
  event_type: string;
  message: string;
  created_at: string;
}

export interface EngineStatus {
  engine_state: string;
  paused: boolean;
  simulation_mode: boolean;
  max_concurrency: number;
  active_workers: number;
  agent_count: number;
  task_counts: Record<string, number>;
  pending_approvals: number;
  total_messages: number;
  uptime_seconds: number;
}

export interface DagGraph {
  workflow_id: string;
  nodes: Array<{
    task_id: string;
    title: string;
    workflow_id: string;
    status: string;
    priority: number;
    assigned_agent_id?: string | null;
  }>;
  edges: Array<{ source: string; target: string }>;
}

const API_BASE = '/api/v1/orchestrator';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data?.error?.message || data?.detail || `Request failed (${res.status})`);
  }
  return data as T;
}

export const orchestratorApi = {
  getStatus: () => request<EngineStatus>('/status'),
  pauseEngine: () => request<EngineStatus>('/engine/pause', { method: 'POST' }),
  resumeEngine: () => request<EngineStatus>('/engine/resume', { method: 'POST' }),
  setMaxConcurrency: (max_concurrency: number) =>
    request<EngineStatus>('/engine/limits', {
      method: 'PUT',
      body: JSON.stringify({ max_concurrency }),
    }),
  listAgents: () => request<{ agents: AgentRecord[]; count: number }>('/agents'),
  registerAgent: (body: Record<string, unknown>) =>
    request<AgentRecord>('/agents', { method: 'POST', body: JSON.stringify(body) }),
  updateAgent: (agentId: string, body: Record<string, unknown>) =>
    request<AgentRecord>(`/agents/${agentId}`, { method: 'PATCH', body: JSON.stringify(body) }),
  listTasks: () => request<{ tasks: TaskRecord[]; count: number }>('/tasks'),
  createTask: (body: Record<string, unknown>) =>
    request<TaskRecord>('/tasks', { method: 'POST', body: JSON.stringify(body) }),
  pauseTask: (taskId: string) => request<TaskRecord>(`/tasks/${taskId}/pause`, { method: 'POST' }),
  resumeTask: (taskId: string) => request<TaskRecord>(`/tasks/${taskId}/resume`, { method: 'POST' }),
  cancelTask: (taskId: string) => request<TaskRecord>(`/tasks/${taskId}/cancel`, { method: 'POST' }),
  getDag: () => request<DagGraph>('/dag'),
  launchDemo: () => request<{ workflow_id: string; tasks: TaskRecord[] }>('/demo/launch', { method: 'POST' }),
  listApprovals: () => request<{ approvals: ApprovalRecord[]; count: number }>('/approvals'),
  decideApproval: (approvalId: string, approved: boolean, comment = '') =>
    request<ApprovalRecord>(`/approvals/${approvalId}/decide`, {
      method: 'POST',
      body: JSON.stringify({ approved, decided_by: 'operator', comment }),
    }),
  listMessages: () => request<{ messages: AgentMessageRecord[]; count: number }>('/messages?limit=50'),
  sendMessage: (body: Record<string, unknown>) =>
    request<AgentMessageRecord>('/messages', { method: 'POST', body: JSON.stringify(body) }),
  listLogs: () => request<{ logs: ExecutionLogRecord[]; count: number }>('/logs?limit=80'),
};
