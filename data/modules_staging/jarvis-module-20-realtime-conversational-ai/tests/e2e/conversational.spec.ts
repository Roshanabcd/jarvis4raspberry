import { test, expect } from '@playwright/test';

test.describe('JARVIS Module 20 — Real-Time Conversational AI E2E', () => {
  test('renders holographic avatar, switches persona, and streams a reply', async ({ page }) => {
    await page.goto('http://localhost:8120/conversational-ai');
    await expect(page.getByText('REAL-TIME CONVERSATIONAL AI')).toBeVisible();
    await page.getByRole('button', { name: 'ATLAS (Male)' }).click();
    await page.fill('#chatInput', 'Hello ATLAS');
    await page.getByRole('button', { name: 'Send' }).click();
    await expect(page.locator('#subtitleBox')).toContainText('ATLAS', { timeout: 10000 });
  });
});
