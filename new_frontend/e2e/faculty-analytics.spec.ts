import { test, expect } from '@playwright/test';

test.describe('Faculty Analytics', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/faculty/analytics');
  });

  test('page renders with title', async ({ page }) => {
    await expect(page.getByText('Faculty Analytics')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/deep insights into student engagement/i)).toBeVisible();
  });

  test('course selector works', async ({ page }) => {
    const select = page.locator('select').first();
    await expect(select).toBeVisible();
    await select.selectOption('CS402');
    await expect(select).toHaveValue('CS402');
  });

  test('stat tiles render', async ({ page }) => {
    await expect(page.getByText('Total Questions').first()).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Weak Topics').first()).toBeVisible();
    await expect(page.getByText('Suggested Revisions').first()).toBeVisible();
  });

  test('period toggle buttons exist', async ({ page }) => {
    await expect(page.getByText('7D')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('30D')).toBeVisible();
  });

  test('trending questions section renders', async ({ page }) => {
    await expect(page.getByText('Trending Questions')).toBeVisible({ timeout: 15000 });
  });

  test('live queries stream table renders', async ({ page }) => {
    await expect(page.getByText('Live Queries Stream')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Live Now')).toBeVisible();
  });

  test('conceptual gaps section renders', async ({ page }) => {
    await expect(page.getByText('Conceptual Gaps')).toBeVisible({ timeout: 15000 });
  });

  test('AI suggested actions section renders', async ({ page }) => {
    await expect(page.getByText('AI Suggested Actions')).toBeVisible({ timeout: 15000 });
  });
});
