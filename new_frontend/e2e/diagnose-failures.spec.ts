import { test } from '@playwright/test';

const PAGES = [
  { url: '/student/flashcards', checks: ['Flashcard Generator', 'Topic Focus', 'Card Count', 'Cognitive Level', 'Generate Smart Deck'] },
  { url: '/student/quiz', checks: ['AI Assessment Lab', 'Advanced Algorithms', 'Discrete Mathematics', 'Performance History'] },
  { url: '/student/progress', checks: ['Learning Progress', 'Track your growth', 'Overall Mastery', 'Study Time'] },
  { url: '/faculty/analytics', checks: ['Faculty Analytics', 'Total Questions', 'Weak Topics'] },
  { url: '/faculty/generate', checks: ['Question Paper Generator', "Bloom's Taxonomy Levels", 'Paper Summary'] },
];

for (const { url, checks } of PAGES) {
  test(`diagnose: ${url}`, async ({ page }) => {
    console.log(`\n=== ${url} ===`);
    await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 }).catch(e => console.log('goto failed:', e.message?.slice(0, 200)));
    await page.waitForTimeout(2000);

    console.log('FINAL URL:', page.url());
    console.log('REDIRECTED:', !page.url().includes(url.split('/')[1]));

    const ls = await page.evaluate(() => localStorage.getItem('uniauth'));
    console.log('TOKEN IN LS:', ls ? (JSON.parse(ls).state?.token ? 'YES' : 'KEY_PRESENT_NO_TOKEN') : 'MISSING');

    const bodyText = await page.locator('body').innerText().catch(() => '<error>');
    console.log('BODY TEXT (first 1000):', bodyText.substring(0, 1000));

    const err = await page.getByText(/error|failed|incorrect/i).first().isVisible().catch(() => false);
    console.log('ERROR_TEXT_VISIBLE:', err);
    if (err) console.log('ERROR_TEXT:', (await page.getByText(/error|failed|incorrect/i).first().textContent().catch(() => ''))?.substring(0, 200));

    for (const text of checks) {
      const visible = await page.getByText(text).isVisible().catch(() => 'THREW');
      console.log(`  "${text}":`, visible);
    }
  });
}
