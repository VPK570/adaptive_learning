import React from 'react';
import styles from './FormField.module.css';

export default function FormField({ 
  label, 
  type = "text", 
  value, 
  onChange, 
  placeholder,
  min,
  max,
  className = ""
}) {
  return (
    <div className={`${styles.fieldWrapper} ${className}`}>
      {label && <label className={styles.label}>{label}</label>}
      <input 
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={styles.input}
        min={min}
        max={max}
      />
    </div>
  );
}
