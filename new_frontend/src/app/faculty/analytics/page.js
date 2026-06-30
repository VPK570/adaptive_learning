import React from 'react';
import AppShell from '../../components/AppShell';
import { BarChart2 } from 'lucide-react';

export default function FacultyAnalyticsPlaceholder() {
  return (
    <AppShell navRole="faculty" activeNavKey="analytics" topBarVariant="search">
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
          color: 'var(--color-primary)'
        }}>
          <BarChart2 size={40} />
        </div>
        <h1 style={{ font: 'var(--text-display-sm)', color: 'var(--color-on-background)' }}>Faculty Analytics</h1>
        <p style={{ font: 'var(--text-body-lg)', color: 'var(--color-on-surface-variant)', maxWidth: 400 }}>
          Detailed engagement analytics, student performance breakdowns, and AI usage insights. Coming soon.
        </p>
      </div>
    </AppShell>
  );
}
