import React from 'react';
import Link from 'next/link';
import { ChevronRight } from 'lucide-react';
import styles from './Breadcrumbs.module.css';

export default function Breadcrumbs({ items }) {
  // items: [{ label: 'Dashboard', href: '/dashboard' }, { label: 'My Courses' }]
  return (
    <nav className={styles.breadcrumbs} aria-label="Breadcrumb">
      <ol className={styles.breadcrumbList}>
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          return (
            <li key={index} className={styles.breadcrumbItem}>
              {item.href && !isLast ? (
                <Link href={item.href} className={styles.breadcrumbLink}>
                  {item.label}
                </Link>
              ) : (
                <span className={styles.breadcrumbCurrent}>{item.label}</span>
              )}
              {!isLast && <ChevronRight className={styles.separator} size={16} />}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
