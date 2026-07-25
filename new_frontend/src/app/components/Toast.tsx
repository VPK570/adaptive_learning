'use client'

import { CheckCircle, AlertCircle, Info, X } from 'lucide-react'
import styles from './Toast.module.css'

const icons = { success: CheckCircle, error: AlertCircle, info: Info }

export default function Toast({ message, type, onClose }: { message: string; type: 'success' | 'error' | 'info'; onClose: () => void }) {
  const Icon = icons[type]
  return (
    <div className={`${styles.toast} ${styles[type]}`} role="alert">
      <Icon size={18} className={styles.icon} />
      <span className={styles.message}>{message}</span>
      <button className={styles.close} onClick={onClose} aria-label="Close"><X size={16} /></button>
    </div>
  )
}
