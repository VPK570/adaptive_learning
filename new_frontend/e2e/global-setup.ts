import { chromium, type FullConfig } from '@playwright/test';
import path from 'path';
import fs from 'fs';

const FRONTEND = 'http://localhost:3000';
const BACKEND = 'http://localhost:8001';
const AUTH_DIR = path.resolve('.auth');

const users = [
  { role: 'student', email: `pw-student-${Date.now()}@test.edu`, password: 'testpass123' },
  { role: 'faculty', email: `pw-faculty-${Date.now()}@test.edu`, password: 'testpass123' },
  { role: 'admin', email: `pw-admin-${Date.now()}@test.edu`, password: 'testpass123' },
];

async function registerUser(request: any, email: string, password: string, role: string) {
  const res = await request.post(`${BACKEND}/auth/register`, {
    data: { email, password, role },
  });
  if (res.status() === 409) return await res.json();
  if (!res.ok()) throw new Error(`register ${role} failed: ${res.status()} ${await res.text()}`);
  return await res.json();
}

async function globalSetup(_config: FullConfig) {
  fs.mkdirSync(AUTH_DIR, { recursive: true });

  const browser = await chromium.launch();
  const context = await browser.newContext();

  for (const u of users) {
    const page = await context.newPage();
    const body = await registerUser(page.request, u.email, u.password, u.role);
    const token = body.access_token;

    await page.goto(FRONTEND);
    await page.evaluate(({ token, email, role }) => {
      window.localStorage.setItem('uniauth', JSON.stringify({
        state: {
          token,
          user: { email, role, name: email.split('@')[0] },
          isAuthenticated: true,
        },
        version: 0,
      }));
    }, { token, email: u.email, role: u.role });
    await page.context().storageState({ path: path.join(AUTH_DIR, `${u.role}.json`) });
    await page.close();
  }

  await browser.close();
}

export default globalSetup;
