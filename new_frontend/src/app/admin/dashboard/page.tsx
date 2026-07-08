"use client";

import React, { useState } from 'react';
import AppShell from '@/app/components/AppShell';
import StatTile from '@/app/components/StatTile';
import DataTable from '@/app/components/DataTable';
import MiniBarChart from '@/app/components/MiniBarChart';
import Badge from '@/app/components/Badge';
import AvatarOrInitials from '@/app/components/AvatarOrInitials';
import { mockAdminUser, adminStats, adminUsers, platformActivity, recentSignups } from '@/lib/mockData';
import styles from './Admin.module.css';

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('overview');

  const tabs = [
    { key: 'overview', label: 'Overview' },
    { key: 'users', label: 'Users' },
    { key: 'courses', label: 'Courses' }
  ];

  const userColumns = [
    {
      key: 'name',
      label: 'User',
      render: (val, row) => (
        <div className={styles.userCell}>
          <AvatarOrInitials name={row.name} />
          <div className={styles.userInfo}>
            <span className={styles.userName}>{val}</span>
            <span className={styles.userEmail}>{row.email}</span>
          </div>
        </div>
      )
    },
    {
      key: 'role',
      label: 'Role',
      render: (val) => <Badge variant="role" color={val}>{val}</Badge>
    },
    {
      key: 'status',
      label: 'Status',
      render: (val) => (
        <span className={`${styles.statusDot} ${val === 'active' ? styles.active : styles.offline}`}>
          {val}
        </span>
      )
    }
  ];

  return (
    <AppShell
      navRole="admin"
      activeNavKey="dashboard"
      topBarVariant="tabs"
      tabs={tabs}
      activeTab={activeTab}
      onTabChange={setActiveTab}
      user={mockAdminUser}
    >
      <div className={styles.container}>
        <header className={styles.header}>
          <h1 className={styles.pageTitle}>Admin Dashboard</h1>
          <p className={styles.pageSubtitle}>Platform health, user management, and analytics overview.</p>
        </header>

        <section className={styles.statsRow}>
          {adminStats.map((stat, i) => (
            <StatTile
              key={i}
              iconName={stat.icon}
              value={stat.value}
              label={stat.label}
              trend={stat.trend}
              accent={stat.accent}
            />
          ))}
        </section>

        <section className={styles.middleRow}>
          <div className={styles.chartColumn}>
            <h2 className={styles.sectionTitle}>Platform Activity (7d)</h2>
            <div className={styles.chartWrapper}>
              <MiniBarChart data={platformActivity} />
            </div>
          </div>

          <div className={styles.signupsColumn}>
            <h2 className={styles.sectionTitle}>Recent Sign-ups</h2>
            <div className={styles.signupsList}>
              {recentSignups.map((person, i) => (
                <div key={i} className={styles.signupItem}>
                  <AvatarOrInitials name={person.name} avatarUrl={person.avatarUrl} initials={person.initials} />
                  <div className={styles.signupInfo}>
                    <span className={styles.signupName}>{person.name}</span>
                    <span className={styles.signupTime}>{person.time}</span>
                  </div>
                  <Badge variant="role" color={person.role}>{person.role}</Badge>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className={styles.usersSection}>
          <h2 className={styles.sectionTitle}>All Users</h2>
          <DataTable
            columns={userColumns}
            data={adminUsers}
            onViewAll={() => console.log('View all users')}
            viewAllLabel="View All Users"
          />
        </section>
      </div>
    </AppShell>
  );
}
