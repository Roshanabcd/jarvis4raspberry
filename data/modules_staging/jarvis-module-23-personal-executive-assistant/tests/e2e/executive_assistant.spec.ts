import { test, expect } from '@playwright/test';

test('Module 23 standalone UI renders header and briefing banner', async ({ page }) => {
  await page.goto('http://127.0.0.1:8123/executive-assistant');
  await expect(page.getByText('PERSONAL EXECUTIVE ASSISTANT')).toBeVisible();
  await expect(page.getByText('LOCAL BRIEF SYNTHESIZER')).toBeVisible();
});
