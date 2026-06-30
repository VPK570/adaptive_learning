import React from 'react';
import AppShell from '../components/AppShell';
import { Bot } from 'lucide-react';

export default function ChatPlaceholder() {
  return (
    <AppShell navRole="student" activeNavKey="ai-assistant" topBarVariant="search">
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
          <Bot size={40} />
        </div>
        <h1 style={{ font: 'var(--text-display-sm)', color: 'var(--color-on-background)' }}>AI Assistant</h1>
        <p style={{ font: 'var(--text-body-lg)', color: 'var(--color-on-surface-variant)', maxWidth: 400 }}>
          The general-purpose AI assistant is coming soon. For now, use the course-specific chat from any course page.
        </p>
      </div>
    </AppShell>
  );
}
