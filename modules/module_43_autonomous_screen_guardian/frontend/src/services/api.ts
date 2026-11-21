export interface GuardianStatus {
  adapter: string;
  simulated: boolean;
  monitoring: {
    state: string;
    consent_granted: boolean;
    selected_monitor: string;
    interval_sec: number;
    frames_captured: number;
    frames_skipped_unchanged: number;
    last_error: string | null;
  };
  ocr_available: boolean;
  ocr_engine: string;
  coding_agents: Array<{ agent_id: string; name: string; available: boolean; status: string; version: string | null }>;
  active_errors: number;
  unread_notifications: number;
  total_repairs: number;
  telemetry: {
    architecture: string;
    memory: { total_mb: number; used_pct: number };
    disk: { total_gb: number; used_pct: number };
  };
}

const BASE = "/api/v1/screen-guardian";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { headers: { "Content-Type": "application/json" }, ...init });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.error?.message || data?.detail?.message || `HTTP ${res.status}`);
  return data as T;
}

export const guardianApi = {
  getStatus: () => req<GuardianStatus>("/status"),
  startMonitor: (explicit_consent: boolean, monitor_id = "primary", interval_sec = 2.0) =>
    req("/monitor/start", { method: "POST", body: JSON.stringify({ explicit_consent, monitor_id, interval_sec }) }),
  pauseMonitor: () => req("/monitor/pause", { method: "POST" }),
  resumeMonitor: () => req("/monitor/resume", { method: "POST" }),
  stopMonitor: () => req("/monitor/stop", { method: "POST" }),
  listNotifications: () => req<{ notifications: Array<Record<string, unknown>> }>("/notifications"),
  notificationAction: (id: string, action: string) =>
    req(`/notifications/${id}/action`, { method: "POST", body: JSON.stringify({ action }) }),
  listRepairs: () => req<{ repairs: Array<Record<string, unknown>> }>("/repairs"),
  createRepair: (body: Record<string, unknown>) => req("/repairs", { method: "POST", body: JSON.stringify(body) }),
  approveRepair: (id: string, decision: "approve" | "reject") =>
    req(`/repairs/${id}/approve`, { method: "POST", body: JSON.stringify({ decision, reviewer: "ui-operator" }) }),
  executeRepair: (id: string) => req(`/repairs/${id}/execute`, { method: "POST" }),
  sendVoice: (utterance: string) =>
    req("/voice/command", { method: "POST", body: JSON.stringify({ utterance, speaker_source: "user_mic" }) }),
};
