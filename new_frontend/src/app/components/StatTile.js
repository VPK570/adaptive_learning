import React from 'react';
import * as Icons from 'lucide-react';
import styles from './StatTile.module.css';

export default function StatTile({ 
  iconName, 
  value, 
  label, 
  caption, 
  trend, 
  accent = 'primary',
  iconPosition = 'left' // 'left' or 'right'
}) {
  const Icon = Icons[iconName] || Icons.HelpCircle;

  return (
    <div className={`${styles.statTile} ${styles[accent]}`}>
      {/* Optional faint background glow for some tiles (like streak) */}
      <div className={styles.glow} />
      
      <div className={`${styles.header} ${iconPosition === 'right' ? styles.headerReverse : ''}`}>
        <div className={styles.iconWrapper}>
          <Icon size={24} />
        </div>
        {(caption || trend) && (
          <div className={styles.meta}>
            {caption && <span className={styles.caption}>{caption}</span>}
          </div>
        )}
      </div>

      <div className={styles.body}>
        <div className={styles.value}>{value}</div>
        <div className={styles.label}>{label}</div>
      </div>

      {trend && (
        <div className={styles.trendRow}>
          <Icons.TrendingUp size={14} className={styles.trendIcon} />
          <span className={styles.trendText}>{trend}</span>
        </div>
      )}
    </div>
  );
}
