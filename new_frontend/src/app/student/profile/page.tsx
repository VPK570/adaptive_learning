"use client";

import React from 'react';
import AppShell from '@/app/components/AppShell';

export default function StudentProfile() {
  return (
    <AppShell
      navRole="student"
      activeNavKey="profile"
      topBarVariant="search"
    >
      <div style={{ padding: 'var(--space-6)' }}>
        <h1 style={{ font: 'var(--text-heading-xl)', color: 'var(--color-on-surface)' }}>Student Profile</h1>
        <p style={{ color: 'var(--color-on-surface-variant)', marginTop: 'var(--space-2)' }}>This is the student profile page.</p>
      </div>
    </AppShell>
  );
}
