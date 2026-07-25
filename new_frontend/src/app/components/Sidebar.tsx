import React from 'react';
import Link from 'next/link';
import { LayoutDashboard, Bot, ClipboardCheck, Layers, Activity, BarChart2, LogOut } from 'lucide-react';
import { useAuthStore } from '@/lib/store/authStore';
import styles from './Sidebar.module.css';

export default function Sidebar({ navRole, activeNavKey, isOpen, onClose }) {
  const logout = useAuthStore(s => s.logout);

  const navItems = [];
  if (navRole === 'student') {
    navItems.push(
      { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, href: '/student/dashboard' },
      { key: 'quiz', label: 'AI Quiz', icon: ClipboardCheck, href: '/student/quiz' },
      { key: 'flashcards', label: 'Flashcards', icon: Layers, href: '/student/flashcards' },
      { key: 'progress', label: 'Progress', icon: Activity, href: '/student/progress' },
    );
  } else if (navRole === 'faculty') {
    navItems.push(
      { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, href: '/faculty/dashboard' },
      { key: 'analytics', label: 'Analytics', icon: BarChart2, href: '/faculty/analytics' },
    );
  } else if (navRole === 'admin') {
    navItems.push(
      { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, href: '/admin/dashboard' },
    );
  }

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
          <span className={styles.brandName}>Vbook LM</span>
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
              <button onClick={() => { if (window.confirm('Are you sure you want to log out?')) logout(); }} className={styles.navLink} style={{ width: '100%', background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 'var(--space-3)', padding: 'var(--space-3) var(--space-4)', borderRadius: 'var(--radius-md)', color: 'var(--color-error)', font: 'inherit', fontSize: 'inherit' }}>
                <LogOut size={20} className={styles.navIcon} />
                <span>Logout</span>
              </button>
            </li>
          </ul>
        </div>
      </aside>
    </>
  );
}
