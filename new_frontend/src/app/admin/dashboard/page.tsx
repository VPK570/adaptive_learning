"use client";

import React, { useState } from 'react';
import AppShell from '@/app/components/AppShell';
import StatTile from '@/app/components/StatTile';
import DataTable from '@/app/components/DataTable';
import Badge from '@/app/components/Badge';
import AvatarOrInitials from '@/app/components/AvatarOrInitials';
import { useQuery } from '@tanstack/react-query';
import { adminApi, type AdminUser, type AdminStats } from '@/lib/api/admin';
import { useAuthStore } from '@/lib/store/authStore';
import styles from './Admin.module.css';

const userColumns = [
  {
    key: 'name', label: 'User',
    render: (val: string, row: AdminUser) => (
      <div className={styles.userCell}>
        <AvatarOrInitials name={row.name} />
        <div className={styles.userInfo}>
          <span className={styles.userName}>{val}</span>
          <span className={styles.userEmail}>{row.email}</span>
        </div>
      </div>
    ),
  },
  {
    key: 'role', label: 'Role',
    render: (val: string) => <Badge variant="role" color={val}>{val}</Badge>,
  },
  {
    key: 'status', label: 'Status',
    render: (val: string) => (
      <span className={`${styles.statusDot} ${val === 'active' ? styles.active : styles.offline}`}>
        {val}
      </span>
    ),
  },
];

export default function AdminDashboard() {
  const _user = useAuthStore(s => s.user);
  const user = _user ? { ..._user, initials: (_user.name?.split(' ').map((s: string) => s[0]).join('') || 'U').toUpperCase() } : null;
  const [activeTab, setActiveTab] = useState('overview');

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => adminApi.getStats(),
    staleTime: 30_000,
  });
  const { data: users = [], isLoading: usersLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => adminApi.listUsers(),
    staleTime: 30_000,
  });
  const loading = statsLoading || usersLoading;

  const tabs = [
    { key: 'overview', label: 'Overview' },
    { key: 'users', label: 'Users' },
  ];

  const statTiles = stats ? [
    { icon: 'Users', value: String(stats.total_users), label: 'Total Users', accent: 'primary', trend: '' },
    { icon: 'Library', value: String(stats.total_courses), label: 'Total Courses', accent: 'tertiary', trend: '' },
    { icon: 'FileText', value: String(stats.total_documents), label: 'Docs Processed', accent: 'secondary', trend: '' },
    { icon: 'MessagesSquare', value: String(stats.total_conversations), label: 'AI Conversations', accent: 'primary-container', trend: '' },
  ] : [];

  return (
    <AppShell
      navRole="admin"
      activeNavKey="dashboard"
      topBarVariant="tabs"
      tabs={tabs}
      activeTab={activeTab}
      onTabChange={setActiveTab}
      user={user ?? undefined}
    >
      <div className={styles.container}>
        <header className={styles.header}>
          <h1 className={styles.pageTitle}>Admin Dashboard</h1>
          <p className={styles.pageSubtitle}>Platform health, user management, and analytics overview.</p>
        </header>

        {activeTab === 'overview' && (
          <>
            <section className={styles.statsRow}>
              {loading ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 'var(--space-4)' }}>
                  {[1,2,3,4].map(i => <div key={i} style={{ height: 100, borderRadius: 'var(--radius-md)', background: 'var(--color-surface-container)', animation: 'pulse 1.5s infinite' }} />)}
                </div>
              ) : (
                statTiles.map((s, i) => (
                  <StatTile key={i} iconName={s.icon} value={s.value} label={s.label} trend={s.trend} accent={s.accent} />
                ))
              )}
            </section>

            {!loading && (
              <section className={styles.usersSection}>
                <h2 className={styles.sectionTitle}>All Users</h2>
                <DataTable
                  columns={userColumns}
                  data={users}
                  onViewAll={() => setActiveTab('users')}
                  viewAllLabel="View All Users"
                />
              </section>
            )}
          </>
        )}

        {activeTab === 'users' && (
          <section className={styles.usersSection}>
            <h2 className={styles.sectionTitle}>All Users</h2>
            <DataTable
              columns={userColumns}
              data={users}
            />
          </section>
        )}
      </div>
    </AppShell>
  );
}
