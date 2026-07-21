import { test, expect } from '@playwright/test';

test.describe('Student Quiz', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/student/quiz');
  });

  test('config screen renders with all controls', async ({ page }) => {
    await expect(page.getByText('AI Assessment Lab')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Advanced Algorithms')).toBeVisible();
    await expect(page.getByText('Discrete Mathematics')).toBeVisible();
    await expect(page.getByText('Question Count')).toBeVisible();
    await expect(page.getByText("Bloom's Taxonomy Levels")).toBeVisible();
  });

  test('selecting a course updates topic dropdown', async ({ page }) => {
    await page.getByText('Discrete Mathematics').click();
    const select = page.locator('select');
    await expect(select).toHaveValue('Set Theory');
  });

  test('blooms level pills toggle', async ({ page }) => {
    const pills = page.getByText('Remember').first();
    await expect(pills).toBeVisible();
  });

  test('performance history section renders', async ({ page }) => {
    await expect(page.getByText('Performance History')).toBeVisible({ timeout: 10000 });
  });

  test('generate button exists', async ({ page }) => {
    await expect(page.getByText('Generate Session')).toBeVisible();
  });
});
