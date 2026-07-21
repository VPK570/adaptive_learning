import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [['html', { open: 'never' }], ['list']],
  globalSetup: require.resolve('./e2e/global-setup.ts'),

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'noauth',
      testMatch: '**/auth*.spec.ts',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'student',
      testMatch: '**/student*.spec.ts',
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/student.json',
      },
    },
    {
      name: 'faculty',
      testMatch: '**/faculty*.spec.ts',
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/faculty.json',
      },
    },
    {
      name: 'admin',
      testMatch: '**/admin*.spec.ts',
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/admin.json',
      },
    },
    {
      name: 'diagnose-student',
      testMatch: '**/diagnose*',
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/student.json',
      },
    },
    {
      name: 'diagnose-faculty',
      testMatch: '**/diagnose*',
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/faculty.json',
      },
    },
  ],
});
