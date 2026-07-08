import React from 'react';
import styles from './MiniBarChart.module.css';

export default function MiniBarChart({ data }) {
  // data: [{ label: "Mon", value: 2100 }, ...]
  
  if (!data || data.length === 0) return null;
  
  const maxValue = Math.max(...data.map(d => d.value));
  
  return (
    <div className={styles.chartContainer}>
      <div className={styles.barsArea}>
        {data.map((item, i) => {
          const heightPercent = maxValue > 0 ? (item.value / maxValue) * 100 : 0;
          return (
            <div key={i} className={styles.barGroup}>
              <div className={styles.barWrapper}>
                <div 
                  className={styles.barFill} 
                  style={{ height: `${heightPercent}%` }}
                >
                  <div className={styles.tooltip}>{item.value.toLocaleString()}</div>
                </div>
              </div>
              <span className={styles.label}>{item.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
