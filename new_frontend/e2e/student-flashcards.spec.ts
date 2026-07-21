import { test, expect } from '@playwright/test';

test.describe('Student Flashcards', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/student/flashcards');
  });

  test('config screen renders', async ({ page }) => {
    await expect(page.getByText('Flashcard Generator')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Select Course')).toBeVisible();
    await expect(page.getByText('Topic Focus')).toBeVisible();
    await expect(page.getByText('Card Count')).toBeVisible();
    await expect(page.getByText('Cognitive Level')).toBeVisible();
  });

  test('card count increment works', async ({ page }) => {
    await expect(page.getByText('15')).toBeVisible();
    await page.getByRole('button', { name: '+' }).click();
    await expect(page.getByText('16')).toBeVisible();
    await page.getByRole('button', { name: '-' }).click();
    await expect(page.getByText('15')).toBeVisible();
  });

  test('course selector has options', async ({ page }) => {
    const select = page.locator('select').first();
    await expect(select).toBeVisible();
    const options = await select.locator('option').allTextContents();
    expect(options.length).toBeGreaterThanOrEqual(3);
  });

  test('history panel shows empty state', async ({ page }) => {
    await expect(page.getByText('Recent Study Sets')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('No saved sets yet.')).toBeVisible();
  });

  test('generate button exists', async ({ page }) => {
    await expect(page.getByText('Generate Smart Deck')).toBeVisible();
  });
});
