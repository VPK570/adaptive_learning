"use client";

import React from 'react';
import { Menu, Search, Bell, History, ArrowLeft, Sun, Moon } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import AvatarOrInitials from './AvatarOrInitials';
import Breadcrumbs from './Breadcrumbs';
import styles from './TopBar.module.css';
import { useTheme } from '../context/ThemeContext';

export default function TopBar({ 
  variant, 
  onMenuClick, 
  user,
  tabs = [], 
  activeTab = '',
  onTabChange,
  breadcrumbs = [],
  onBack
}) {
  const pathname = usePathname();
  const roleMatch = pathname ? pathname.match(/^\/(student|faculty|admin)/) : null;
  const role = roleMatch ? roleMatch[1] : 'student';
  const profileUrl = `/${role}/profile`;
  const { theme, toggleTheme } = useTheme();

  return (
    <header className={styles.topBar}>
      <div className={styles.leftSection}>
        <button className={styles.menuBtn} onClick={onMenuClick} aria-label="Open menu">
          <Menu size={24} />
        </button>

        {variant === 'search' && (
          <div className={styles.searchPill}>
            <Search size={18} className={styles.searchIcon} />
            <input 
              type="text" 
              placeholder="Search resources..." 
              className={styles.searchInput}
            />
          </div>
        )}

        {variant === 'tabs' && tabs.length > 0 && (
          <nav className={styles.tabNav}>
            {tabs.map(tab => (
              <button 
                key={tab.key}
                className={`${styles.tabBtn} ${activeTab === tab.key ? styles.activeTab : ''}`}
                onClick={() => onTabChange && onTabChange(tab.key)}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        )}

        {variant === 'breadcrumbBack' && (
          <div className={styles.breadcrumbBackWrapper}>
            <button className={styles.backBtn} onClick={onBack}>
              <ArrowLeft size={18} />
              <span>Back</span>
            </button>
            <div className={styles.divider}></div>
            {breadcrumbs.length > 0 && (
              <Breadcrumbs items={breadcrumbs} />
            )}
          </div>
        )}
      </div>

      <div className={styles.rightSection}>
        <button className={styles.iconBtn} aria-label="History">
          <History size={20} />
        </button>
        <button className={styles.iconBtn} aria-label="Notifications">
          <Bell size={20} />
          <span className={styles.unreadDot}></span>
        </button>
        <button className={styles.iconBtn} onClick={toggleTheme} aria-label="Toggle theme">
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>
        
        <div className={styles.avatarContainer}>
          <Link href={profileUrl} className={styles.profileLink} aria-label="View profile">
            <AvatarOrInitials 
              name={user?.name || 'User'} 
              avatarUrl={user?.avatarUrl} 
              initials={user?.initials}
            />
          </Link>
        </div>
      </div>
    </header>
  );
}
