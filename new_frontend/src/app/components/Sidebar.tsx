import React from 'react';
import Link from 'next/link';
import { LayoutDashboard, BookOpen, Bot, Activity, BarChart2, Settings, HelpCircle, Plus } from 'lucide-react';
import styles from './Sidebar.module.css';

export default function Sidebar({ navRole, activeNavKey, isOpen, onClose }) {
  // navRole: "student" | "faculty" | "admin"
  
  const navItems = [
    { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, href: navRole === 'admin' ? '/admin/dashboard' : navRole === 'faculty' ? '/faculty/dashboard' : '/student/dashboard' },
    { key: 'courses', label: 'My Courses', icon: BookOpen, href: navRole === 'faculty' ? '/faculty/dashboard' : '/student/dashboard' }, // simplified generic routes for now
    { key: 'ai-assistant', label: 'AI Assistant', icon: Bot, href: '/student/chat' },
    { key: 'progress', label: 'Progress', icon: Activity, href: '/student/progress' },
    { key: 'analytics', label: 'Analytics', icon: BarChart2, href: '/faculty/analytics' },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && <div className={styles.backdrop} onClick={onClose} aria-hidden="true" />}
      
      <aside className={`${styles.sidebar} ${isOpen ? styles.open : ''}`}>
        <div className={styles.brandBlock}>
          <div className={styles.logo}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>
              <path d="M6 12v5c3 3 9 3 12 0v-5"/>
            </svg>
          </div>
          <span className={styles.brandName}>UniAI</span>
        </div>

        <div className={styles.actionBlock}>
          <button className={styles.newSessionBtn}>
            <Plus size={18} />
            <span>New Research Session</span>
          </button>
        </div>

        <nav className={styles.navMain}>
          <ul className={styles.navList}>
            {navItems.map((item) => {
              const isActive = activeNavKey === item.key;
              const Icon = item.icon;
              return (
                <li key={item.key} className={styles.navItem}>
                  <Link href={item.href} className={`${styles.navLink} ${isActive ? styles.active : ''}`}>
                    <Icon size={20} className={styles.navIcon} />
                    <span>{item.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className={styles.footerBlock}>
          <ul className={styles.navList}>
            <li className={styles.navItem}>
              <Link href="#" className={styles.navLink}>
                <Settings size={20} className={styles.navIcon} />
                <span>Settings</span>
              </Link>
            </li>
            <li className={styles.navItem}>
              <Link href="#" className={styles.navLink}>
                <HelpCircle size={20} className={styles.navIcon} />
                <span>Help & Support</span>
              </Link>
            </li>
          </ul>
        </div>
      </aside>
    </>
  );
}
