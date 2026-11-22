import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import DashboardPage from '../../frontend/src/pages/DashboardPage';

describe('DashboardPage', () => {
  it('renders the JARVIS Module 24 header and simulated badge', () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ emails: [] }) }))
    );
    render(<DashboardPage />);
    expect(screen.getByText(/Email & Calendar Assistant/i)).toBeTruthy();
    expect(screen.getByText(/SIMULATED MAIL\/CAL ADAPTER/i)).toBeTruthy();
  });
});
