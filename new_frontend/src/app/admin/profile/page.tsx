"use client";

import React, { useEffect, useState } from 'react';
import AppShell from '@/app/components/AppShell';
import { usersApi } from '@/lib/api/users';
import { useAuthStore } from '@/lib/store/authStore';
import type { User } from '@/lib/api/types';

export default function AdminProfile() {
  const storeUser = useAuthStore(s => s.user);
  const [profile, setProfile] = useState<User | null>(null);
  const [name, setName] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    usersApi.getMe().then(p => {
      setProfile(p);
      setName(p.name);
    });
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await usersApi.updateMe({ name });
      setProfile(updated);
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppShell navRole="admin" activeNavKey="profile" topBarVariant="search" user={storeUser ?? undefined}>
      <div style={{ padding: 'var(--space-6)', maxWidth: 480 }}>
        <h1 style={{ font: 'var(--text-heading-xl)', color: 'var(--color-on-surface)' }}>Admin Profile</h1>
        {profile && (
          <div style={{ marginTop: 'var(--space-6)', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <div>
              <label style={{ font: 'var(--text-label-lg)', color: 'var(--color-on-surface-variant)' }}>Email</label>
              <p style={{ font: 'var(--text-body-lg)', color: 'var(--color-on-surface)' }}>{profile.email}</p>
            </div>
            <div>
              <label style={{ font: 'var(--text-label-lg)', color: 'var(--color-on-surface-variant)' }}>Role</label>
              <p style={{ font: 'var(--text-body-lg)', color: 'var(--color-on-surface)' }}>{profile.role}</p>
            </div>
            <div>
              <label style={{ font: 'var(--text-label-lg)', color: 'var(--color-on-surface-variant)' }}>Display Name</label>
              <input
                value={name}
                onChange={e => setName(e.target.value)}
                style={{
                  display: 'block', width: '100%', marginTop: 'var(--space-2)',
                  padding: 'var(--space-3)', borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--color-outline-variant)',
                  font: 'var(--text-body-lg)', background: 'var(--color-surface-container-low)',
                  color: 'var(--color-on-surface)',
                }}
              />
            </div>
            <button
              onClick={handleSave}
              disabled={saving}
              style={{
                padding: 'var(--space-3) var(--space-6)', borderRadius: 'var(--radius-md)',
                border: 'none', background: 'var(--color-primary)', color: 'var(--color-on-primary)',
                font: 'var(--text-label-lg)', cursor: 'pointer', alignSelf: 'flex-start',
              }}
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        )}
      </div>
    </AppShell>
  );
}
