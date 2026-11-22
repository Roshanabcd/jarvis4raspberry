import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import DashboardPage from '../../frontend/src/pages/DashboardPage';

describe('DashboardPage', () => {
  it('renders the JARVIS Module 21 header and simulation badge', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ simulated: true, sessions: [], approvals: [], workflows: [] }),
        })
      )
    );
    render(<DashboardPage />);
    expect(screen.getByText(/Intelligent Browser Agent/i)).toBeTruthy();
    expect(screen.getByText(/SIMULATED ADAPTER/i)).toBeTruthy();
  });
});
