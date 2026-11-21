import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DashboardPage } from '../../frontend/src/pages/DashboardPage';

describe('Module 20 DashboardPage', () => {
  it('switches between ARIA and ATLAS holographic avatars and shows lip-sync disclosure', () => {
    render(<DashboardPage />);
    expect(screen.getByText(/REAL-TIME CONVERSATIONAL AI/i)).toBeTruthy();
    expect(screen.getByText(/APPROXIMATE VISEME/i)).toBeTruthy();
    fireEvent.click(screen.getByText(/ATLAS \(Male\)/i));
    expect(screen.getByLabelText(/ATLAS holographic avatar/i)).toBeTruthy();
  });
});
