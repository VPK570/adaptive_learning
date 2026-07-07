import React from 'react';
import styles from './ProgressBar.module.css';

export default function ProgressBar({ percent = 0, intensity = 1, showGradient = false }) {
  // intensity is 0-1
  
  const fillStyle = {
    width: `${percent}%`,
    opacity: intensity
  };

  return (
    <div className={styles.track}>
      <div 
        className={`${styles.fill} ${showGradient ? styles.gradientFill : ''}`} 
        style={fillStyle} 
      />
    </div>
  );
}
