import React from 'react';
import { Check } from 'lucide-react';
import styles from './CheckboxCard.module.css';

export default function CheckboxCard({ 
  checked, 
  onChange, 
  label, 
  description,
  color = 'primary' // primary, secondary, tertiary, etc.
}) {
  return (
    <label className={`${styles.card} ${checked ? styles.checked : ''} ${styles[color]}`}>
      <input 
        type="checkbox" 
        className={styles.hiddenInput} 
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
      />
      <div className={styles.header}>
        <div className={styles.checkbox}>
          {checked && <Check size={14} strokeWidth={3} className={styles.checkIcon} />}
        </div>
        <span className={styles.label}>{label}</span>
      </div>
      <p className={styles.description}>{description}</p>
    </label>
  );
}
