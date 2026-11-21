import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import DashboardPage from '../../frontend/src/pages/DashboardPage';

describe('DashboardPage', () => {
  it('renders the JARVIS Module 22 header and simulation badge', () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ simulated: true, models: [] }),
        })
      )
    );
    render(<DashboardPage />);
    expect(screen.getByText(/Intelligent AI Model Router/i)).toBeTruthy();
    expect(screen.getByText(/SIMULATED ADAPTER/i)).toBeTruthy();
  });
});
