import React from 'react';
import styles from './RadialProgress.module.css';

export default function RadialProgress({ percent = 0, label = 'OVERALL' }) {
  const radius = 60;
  const stroke = 12;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (percent / 100) * circumference;

  return (
    <div className={styles.radialContainer}>
      <svg
        height={radius * 2}
        width={radius * 2}
        className={styles.svg}
      >
        <circle
          className={styles.track}
          strokeWidth={stroke}
          r={normalizedRadius}
          cx={radius}
          cy={radius}
        />
        <circle
          className={styles.fill}
          strokeWidth={stroke}
          strokeDasharray={circumference + ' ' + circumference}
          style={{ strokeDashoffset }}
          strokeLinecap="round"
          r={normalizedRadius}
          cx={radius}
          cy={radius}
        />
      </svg>
      <div className={styles.content}>
        <span className={styles.percent}>{percent}%</span>
        <span className={styles.label}>{label}</span>
      </div>
    </div>
  );
}
