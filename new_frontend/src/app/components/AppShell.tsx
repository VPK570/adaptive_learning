"use client";

import React, { useState } from 'react';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import styles from './AppShell.module.css';
import { useAuthStore } from '@/lib/store/authStore';

export default function AppShell({ 
  children, 
  navRole = 'student', 
  activeNavKey = 'dashboard', 
  topBarVariant = 'search',
  user = { name: 'Demo User', initials: 'DU' },
  tabs,
  activeTab,
  onTabChange,
  breadcrumbs,
  onBack
}) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const storeUser = useAuthStore((s) => s.user);
  const activeUser = user?.name ? user : storeUser ?? { name: 'User', initials: 'U' };

  return (
    <div className={styles.appContainer}>
      <Sidebar 
        navRole={navRole} 
        activeNavKey={activeNavKey} 
        isOpen={isMobileMenuOpen} 
        onClose={() => setIsMobileMenuOpen(false)} 
      />
      
      <div className={styles.mainContent}>
        <TopBar 
          variant={topBarVariant}
          onMenuClick={() => setIsMobileMenuOpen(true)}
          user={activeUser}
          tabs={tabs}
          activeTab={activeTab}
          onTabChange={onTabChange}
          breadcrumbs={breadcrumbs}
          onBack={onBack}
        />
        <main className={styles.pageContent}>
          {children}
        </main>
      </div>
    </div>
  );
}
