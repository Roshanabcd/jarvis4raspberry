import { test, expect } from '@playwright/test';

test.describe('JARVIS Module 18 — Multi-Agent Orchestrator E2E', () => {
  test('launches demo DAG and completes human approval flow', async ({ page }) => {
    await page.goto('http://localhost:8118/orchestrator');
    await expect(page.getByText('MULTI-AGENT ORCHESTRATOR')).toBeVisible();
    await expect(page.getByText('SIMULATION MODE: REFERENCE AGENTS')).toBeVisible();

    await page.getByRole('button', { name: 'Launch Demo DAG' }).click();
    await page.getByRole('button', { name: 'Approvals' }).click();
    await expect(page.getByRole('button', { name: 'Approve' }).first()).toBeVisible({ timeout: 10000 });
    await page.getByRole('button', { name: 'Approve' }).first().click();

    await page.getByRole('button', { name: 'Tasks & DAG' }).click();
    await expect(page.getByText('completed').first()).toBeVisible({ timeout: 10000 });
  });
});
