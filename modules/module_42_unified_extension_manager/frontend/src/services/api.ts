export interface ExtensionModule {
  module_id: string;
  name: string;
  version: string;
  category: string;
  source_archive: string | null;
  installed_location: string | null;
  integration_status: string;
  enabled: boolean;
  health_status: string;
  health_endpoint: string | null;
  dependencies: Record<string, unknown>;
  required_permissions: string[];
  config: Record<string, unknown>;
  compatibility: Record<string, unknown>;
  error_details: string | null;
}

export interface ManagerStatus {
  adapter: string;
  simulated: boolean;
  default_archives_dir: string;
  total_modules: number;
  enabled_modules: number;
  health_breakdown: Record<string, number>;
  pending_approvals: number;
  cross_module_conflicts: number;
  uptime_seconds: number;
}

const BASE = "/api/v1/extensions";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.error?.message || data?.detail?.message || `HTTP ${res.status}`);
  return data as T;
}

export const extensionApi = {
  getStatus: () => req<ManagerStatus>("/status"),
  listModules: () => req<{ modules: ExtensionModule[]; count: number }>("/modules"),
  scanFolder: (folder_path: string, target_arch = "arm64") =>
    req<Record<string, unknown>>("/scan", {
      method: "POST",
      body: JSON.stringify({ folder_path, register_discovered: true, target_arch }),
    }),
  toggleModule: (moduleId: string, enabled: boolean) =>
    req<ExtensionModule>(`/modules/${moduleId}/toggle`, { method: "POST", body: JSON.stringify({ enabled }) }),
  probeHealth: (moduleId: string) =>
    req<Record<string, unknown>>(`/modules/${moduleId}/health-check`, { method: "POST" }),
  buildPlan: (module_ids: string[] = []) =>
    req<Record<string, unknown>>("/plan", { method: "POST", body: JSON.stringify({ module_ids }) }),
  listLogs: () => req<{ logs: Array<{ log_id: number; event_type: string; message: string }>; count: number }>("/logs?limit=30"),
};
