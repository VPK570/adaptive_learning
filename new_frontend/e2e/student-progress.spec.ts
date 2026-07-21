import { test, expect } from '@playwright/test';

test.describe('Student Progress', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/student/progress');
  });

  test('page renders with title and subtitle', async ({ page }) => {
    await expect(page.getByText('Learning Progress')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/track your growth/i)).toBeVisible();
  });

  test('stats tiles render', async ({ page }) => {
    await expect(page.getByText('Overall Mastery')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Study Time')).toBeVisible();
    await expect(page.getByText('Courses Enrolled')).toBeVisible();
  });

  test('weak topics section renders', async ({ page }) => {
    await expect(page.getByText('Weak Topics')).toBeVisible({ timeout: 10000 });
  });

  test('revision section renders', async ({ page }) => {
    await expect(page.getByText('Recommended for Revision')).toBeVisible({ timeout: 10000 });
  });
});
