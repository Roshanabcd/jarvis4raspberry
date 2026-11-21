import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DashboardPage } from '../../frontend/src/pages/DashboardPage';
import { orchestratorApi } from '../../frontend/src/services/api';

vi.mock('../../frontend/src/services/api', () => ({
  orchestratorApi: {
    getStatus: vi.fn(),
    listAgents: vi.fn(),
    listTasks: vi.fn(),
    listApprovals: vi.fn(),
    listMessages: vi.fn(),
    listLogs: vi.fn(),
    getDag: vi.fn(),
    launchDemo: vi.fn(),
    pauseEngine: vi.fn(),
    resumeEngine: vi.fn(),
    setMaxConcurrency: vi.fn(),
    createTask: vi.fn(),
    decideApproval: vi.fn(),
  },
}));

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.mocked(orchestratorApi.getStatus).mockResolvedValue({
      engine_state: 'running',
      paused: false,
      simulation_mode: true,
      max_concurrency: 4,
      active_workers: 0,
      agent_count: 4,
      task_counts: { completed: 2, queued: 1 },
      pending_approvals: 1,
      total_messages: 3,
      uptime_seconds: 12.5,
    });
    vi.mocked(orchestratorApi.listAgents).mockResolvedValue({ agents: [], count: 0 });
    vi.mocked(orchestratorApi.listTasks).mockResolvedValue({ tasks: [], count: 0 });
    vi.mocked(orchestratorApi.listApprovals).mockResolvedValue({ approvals: [], count: 0 });
    vi.mocked(orchestratorApi.listMessages).mockResolvedValue({ messages: [], count: 0 });
    vi.mocked(orchestratorApi.listLogs).mockResolvedValue({ logs: [], count: 0 });
    vi.mocked(orchestratorApi.getDag).mockResolvedValue({ workflow_id: 'all', nodes: [], edges: [] });
  });

  it('renders JARVIS header, simulation badge, and navigation tabs', async () => {
    render(<DashboardPage />);
    expect(await screen.findByText(/MULTI-AGENT ORCHESTRATOR/i)).toBeTruthy();
    expect(screen.getByText(/SIMULATION MODE/i)).toBeTruthy();
    fireEvent.click(screen.getByText(/Agent Registry/i));
    await waitFor(() => expect(screen.getByText(/REGISTERED AGENTS/i)).toBeTruthy());
  });
});
