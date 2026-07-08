"use client";

import React from 'react';
import AppShell from '@/app/components/AppShell';
import { mockAdminUser } from '@/lib/mockData';

export default function AdminProfile() {
  return (
    <AppShell
      navRole="admin"
      activeNavKey="profile"
      topBarVariant="search"
      user={mockAdminUser}
    >
      <div style={{ padding: 'var(--space-6)' }}>
        <h1 style={{ font: 'var(--text-heading-xl)', color: 'var(--color-on-surface)' }}>Admin Profile</h1>
        <p style={{ color: 'var(--color-on-surface-variant)', marginTop: 'var(--space-2)' }}>This is the admin profile page.</p>
      </div>
    </AppShell>
  );
}
