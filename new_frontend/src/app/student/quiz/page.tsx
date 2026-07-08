import React from 'react';
import AppShell from '@/app/components/AppShell';
import { ClipboardCheck } from 'lucide-react';

export default function QuizPlaceholder() {
  return (
    <AppShell navRole="student" activeNavKey="dashboard" topBarVariant="search">
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: 'calc(100vh - 200px)',
        gap: 'var(--space-6)',
        textAlign: 'center'
      }}>
        <div style={{
          width: 80,
          height: 80,
          borderRadius: 'var(--radius-full)',
          backgroundColor: 'var(--color-surface-container)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-tertiary)'
        }}>
          <ClipboardCheck size={40} />
        </div>
        <h1 style={{ font: 'var(--text-display-sm)', color: 'var(--color-on-background)' }}>Practice Quizzes</h1>
        <p style={{ font: 'var(--text-body-lg)', color: 'var(--color-on-surface-variant)', maxWidth: 400 }}>
          Adaptive quizzes tailored to your learning gaps. This feature is under development.
        </p>
      </div>
    </AppShell>
  );
}
