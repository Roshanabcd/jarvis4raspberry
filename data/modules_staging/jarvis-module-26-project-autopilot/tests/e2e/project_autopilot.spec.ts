import { test, expect } from '@playwright/test';

test.describe('Module 26 — Project Autopilot E2E', () => {
  test('loads control UI and creates an autopilot project', async ({ page }) => {
    await page.goto('http://127.0.0.1:8126/project-autopilot');
    await expect(page.locator('h1')).toContainText('Project Autopilot');
    await page.fill('#pName', 'E2E Telemetry Service');
    await page.fill('#pGoal', 'Build an autonomous telemetry collector.');
    await page.click('button:has-text("+ Create & Auto-Plan")');
    await expect(page.locator('#activeTitle')).toContainText('E2E Telemetry Service');
  });
});
