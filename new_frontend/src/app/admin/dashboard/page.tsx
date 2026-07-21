"use client";

import React, { useEffect, useState } from 'react';
import AppShell from '@/app/components/AppShell';
import StatTile from '@/app/components/StatTile';
import DataTable from '@/app/components/DataTable';
import Badge from '@/app/components/Badge';
import AvatarOrInitials from '@/app/components/AvatarOrInitials';
import { adminApi, type AdminUser, type AdminStats } from '@/lib/api/admin';
import { useAuthStore } from '@/lib/store/authStore';
import styles from './Admin.module.css';

export default function AdminDashboard() {
  const _user = useAuthStore(s => s.user);
  const user = _user ? { ..._user, initials: (_user.name?.split(' ').map((s: string) => s[0]).join('') || 'U').toUpperCase() } : null;
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const c = new AbortController();
    Promise.all([
      adminApi.getStats(),
      adminApi.listUsers(),
    ])
      .then(([s, u]) => { if (!c.signal.aborted) { setStats(s); setUsers(u); } })
      .catch(() => { if (!c.signal.aborted) {} })
      .finally(() => { if (!c.signal.aborted) setLoading(false); });
    return () => c.abort();
  }, []);

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
                <p>Loading...</p>
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
