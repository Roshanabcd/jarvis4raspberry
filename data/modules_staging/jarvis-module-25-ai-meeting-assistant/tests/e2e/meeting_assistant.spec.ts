import { test, expect } from '@playwright/test';

test.describe('Module 25 — AI Meeting Assistant E2E', () => {
  test('loads control UI and creates a meeting session', async ({ page }) => {
    await page.goto('http://127.0.0.1:8125/meeting-assistant');
    await expect(page.locator('h1')).toContainText('AI Meeting Assistant');
    await page.fill('#mTitle', 'E2E Architecture Sync');
    await page.click('button:has-text("+ Create Meeting")');
    await expect(page.locator('#activeTitle')).toContainText('E2E Architecture Sync');
  });
});
