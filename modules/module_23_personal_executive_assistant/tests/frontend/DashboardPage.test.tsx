import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import DashboardPage from '../../frontend/src/pages/DashboardPage';

describe('DashboardPage', () => {
  it('renders the JARVIS Module 23 header and local synthesizer badge', () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ executive_summary: 'Brief ready', tasks: [] }),
        })
      )
    );
    render(<DashboardPage />);
    expect(screen.getByText(/Personal Executive Assistant/i)).toBeTruthy();
    expect(screen.getByText(/LOCAL BRIEF SYNTHESIZER/i)).toBeTruthy();
  });
});
