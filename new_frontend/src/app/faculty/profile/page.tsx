"use client";

import React from 'react';
import AppShell from '@/app/components/AppShell';
import { mockFacultyUser } from '@/lib/mockData';

export default function FacultyProfile() {
  return (
    <AppShell
      navRole="faculty"
      activeNavKey="profile"
      topBarVariant="search"
      user={mockFacultyUser}
    >
      <div style={{ padding: 'var(--space-6)' }}>
        <h1 style={{ font: 'var(--text-heading-xl)', color: 'var(--color-on-surface)' }}>Faculty Profile</h1>
        <p style={{ color: 'var(--color-on-surface-variant)', marginTop: 'var(--space-2)' }}>This is the faculty profile page.</p>
      </div>
    </AppShell>
  );
}
