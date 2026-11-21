import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DashboardPage } from '../../frontend/src/pages/DashboardPage';
import { computerAssistantApi } from '../../frontend/src/services/api';

vi.mock('../../frontend/src/services/api', () => ({
  computerAssistantApi: {
    getStatus: vi.fn(),
    listActions: vi.fn(),
    listApprovals: vi.fn(),
    executeAction: vi.fn(),
    getScreenshot: vi.fn(),
    engageEstop: vi.fn(),
    resetEstop: vi.fn(),
    setDryRun: vi.fn(),
    decideApproval: vi.fn(),
    replay: vi.fn(),
  },
}));

describe('Module 19 DashboardPage', () => {
  beforeEach(() => {
    vi.mocked(computerAssistantApi.getStatus).mockResolvedValue({
      adapter: { adapter_name: 'safe_demo_virtual_desktop', simulated: true, active_window_id: 'win-01', cursor: { x: 100, y: 100 } },
      estop_active: false,
      estop_reason: '',
      dry_run_mode: false,
      policy: {},
      pending_approvals: 0,
      total_actions: 0,
      uptime_seconds: 5,
    });
    vi.mocked(computerAssistantApi.listActions).mockResolvedValue({ actions: [], count: 0 });
    vi.mocked(computerAssistantApi.listApprovals).mockResolvedValue({ approvals: [], count: 0 });
  });

  it('renders safety banner and emergency stop control', async () => {
    render(<DashboardPage />);
    expect(await screen.findByText(/AUTONOMOUS COMPUTER ASSISTANT/i)).toBeTruthy();
    expect(screen.getByText(/SAFE DEMO ADAPTER/i)).toBeTruthy();
    expect(screen.getByText(/EMERGENCY STOP/i)).toBeTruthy();
  });
});
