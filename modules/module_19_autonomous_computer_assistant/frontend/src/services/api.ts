export interface AssistantStatus {
  adapter: { adapter_name: string; simulated: boolean; active_window_id: string; cursor: { x: number; y: number } };
  estop_active: boolean;
  estop_reason: string;
  dry_run_mode: boolean;
  policy: Record<string, boolean>;
  pending_approvals: number;
  total_actions: number;
  uptime_seconds: number;
}

export interface ActionRecord {
  action_id: string;
  action_type: string;
  risk_level: 'low' | 'medium' | 'high';
  status: string;
  dry_run: boolean;
  simulated: boolean;
  params: Record<string, unknown>;
  result?: Record<string, unknown> | null;
  error?: string | null;
  duration_ms: number;
  created_at: string;
}

export interface ApprovalRecord {
  approval_id: string;
  action_id: string;
  action_type: string;
  risk_level: string;
  prompt: string;
  status: 'pending' | 'approved' | 'rejected';
  decided_by?: string | null;
}

const API = '/api/v1/computer-assistant';

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data?.error?.message || data?.detail || `HTTP ${res.status}`);
  return data as T;
}

export const computerAssistantApi = {
  getStatus: () => req<AssistantStatus>('/status'),
  listActions: () => req<{ actions: ActionRecord[]; count: number }>('/actions?limit=50'),
  listApprovals: () => req<{ approvals: ApprovalRecord[]; count: number }>('/approvals'),
  listWindows: () => req<{ windows: Array<{ window_id: string; title: string; focused: boolean }> }>('/windows'),
  executeAction: (action_type: string, params: Record<string, unknown>, dry_run?: boolean) =>
    req<ActionRecord>('/actions', { method: 'POST', body: JSON.stringify({ action_type, params, dry_run }) }),
  getScreenshot: (id: string) => req<{ screenshot_id: string; image_b64: string }>(`/screenshots/${id}`),
  engageEstop: (reason: string) => req<AssistantStatus>('/safety/estop', { method: 'POST', body: JSON.stringify({ reason }) }),
  resetEstop: () => req<AssistantStatus>('/safety/estop/reset', { method: 'POST' }),
  setDryRun: (enabled: boolean) => req<AssistantStatus>('/safety/dry-run', { method: 'PUT', body: JSON.stringify({ enabled }) }),
  decideApproval: (approvalId: string, approved: boolean) =>
    req<{ approval: ApprovalRecord; action: ActionRecord }>(`/approvals/${approvalId}/decide`, {
      method: 'POST',
      body: JSON.stringify({ approved, decided_by: 'operator' }),
    }),
  replay: (action_ids: string[], dry_run = true) =>
    req<{ replayed_count: number }>('/actions/replay', { method: 'POST', body: JSON.stringify({ action_ids, dry_run }) }),
};
