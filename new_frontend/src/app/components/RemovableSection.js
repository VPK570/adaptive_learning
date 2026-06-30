import React from 'react';
import { X } from 'lucide-react';
import styles from './RemovableSection.module.css';

export default function RemovableSection({ title, onRemove, children }) {
  return (
    <div className={styles.section}>
      <div className={styles.header}>
        <h3 className={styles.title}>{title}</h3>
        {onRemove && (
          <button className={styles.removeBtn} onClick={onRemove} aria-label="Remove section">
            <X size={18} />
          </button>
        )}
      </div>
      <div className={styles.content}>
        {children}
      </div>
    </div>
  );
}
