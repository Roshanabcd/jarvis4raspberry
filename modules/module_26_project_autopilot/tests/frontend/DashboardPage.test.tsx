import { describe, it, expect } from 'vitest';
import { DashboardPage } from '../../frontend/src/pages/DashboardPage';

describe('Module 26 — Project Autopilot DashboardPage', () => {
  it('exports a valid React component', () => {
    expect(typeof DashboardPage).toBe('function');
  });
});
