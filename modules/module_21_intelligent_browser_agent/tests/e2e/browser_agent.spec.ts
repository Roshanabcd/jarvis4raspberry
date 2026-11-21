import { test, expect } from '@playwright/test';

test('Module 21 standalone UI renders and enforces simulation label', async ({ page }) => {
  await page.goto('http://127.0.0.1:8121/browser-agent');
  await expect(page.getByText('INTELLIGENT BROWSER AGENT')).toBeVisible();
  await expect(page.getByText('SIMULATED ADAPTER')).toBeVisible();
});
