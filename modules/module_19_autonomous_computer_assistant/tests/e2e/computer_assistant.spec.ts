import { test, expect } from '@playwright/test';

test.describe('JARVIS Module 19 — Autonomous Computer Assistant E2E', () => {
  test('captures simulated screenshot and toggles E-STOP', async ({ page }) => {
    await page.goto('http://localhost:8119/computer-assistant');
    await expect(page.getByText('AUTONOMOUS COMPUTER ASSISTANT')).toBeVisible();
    await page.getByRole('button', { name: 'Capture Screenshot' }).click();
    await expect(page.locator('img[alt="Simulated desktop screenshot"]')).toBeVisible({ timeout: 10000 });
    await page.getByRole('button', { name: 'EMERGENCY STOP' }).click();
    await expect(page.getByText('E-STOP: ENGAGED')).toBeVisible();
  });
});
