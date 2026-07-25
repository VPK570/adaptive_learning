import React, { useId } from 'react';
import styles from './FormField.module.css';

export default function FormField({ 
  label, type = "text", value, onChange, placeholder, min, max, required, autoComplete, className = ""
}) {
  const fieldId = useId();
  return (
    <div className={`${styles.fieldWrapper} ${className}`}>
      {label && <label htmlFor={fieldId} className={styles.label}>{label}</label>}
      <input 
        id={fieldId}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={styles.input}
        min={min}
        max={max}
        required={required}
        autoComplete={autoComplete}
      />
    </div>
  );
}