import React from 'react';
import styles from './Badge.module.css';
import { MemoryStick } from 'lucide-react'; // Placeholder for 'memory' icon if needed in pulse

export default function Badge({ 
  variant = 'solid', 
  color = 'primary', // primary, secondary, error, role-admin, role-professor, role-student
  children,
  icon: Icon
}) {
  // variants: 'solid' | 'outline-pill' | 'mono-chip' | 'pulse' | 'role'

  const badgeClass = `${styles.badge} ${styles[variant]} ${styles[color]}`;

  return (
    <div className={badgeClass}>
      {Icon && <Icon size={14} className={styles.icon} />}
      <span className={styles.label}>{children}</span>
    </div>
  );
}
