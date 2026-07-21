import { test, expect } from '@playwright/test';

test.describe('Student Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/student/dashboard');
  });

  test('page loads with greeting and sidebar', async ({ page }) => {
    await expect(page.getByText(/welcome back/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Vbook LM')).toBeVisible();
    await expect(page.getByText('AI Quiz')).toBeVisible();
    await expect(page.getByText('Flashcards')).toBeVisible();
    await expect(page.getByText('Progress')).toBeVisible();
  });

  test('stats section renders', async ({ page }) => {
    await expect(page.getByText('OVERALL')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Current Streak')).toBeVisible();
    await expect(page.getByText('Topics Completed')).toBeVisible();
    await expect(page.getByText('Quizzes Taken')).toBeVisible();
  });

  test('continue learning section shows loading then courses or empty', async ({ page }) => {
    await expect(page.getByText('Continue Learning')).toBeVisible({ timeout: 10000 });
  });

  test('sidebar nav links navigate correctly', async ({ page }) => {
    await page.getByText('AI Quiz').click();
    await expect(page).toHaveURL(/\/student\/quiz/);
  });
});
