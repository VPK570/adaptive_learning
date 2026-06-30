"use client";

import React, { useState } from 'react';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import styles from './AppShell.module.css';

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
          user={user}
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
