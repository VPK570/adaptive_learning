import React, { useMemo } from 'react';
import styles from './ActivityHeatmap.module.css';

export default function ActivityHeatmap({ rows = 4, cols = 7, heatmapData }) {
  
  // If no data provided, generate a sensible random fallback
  const data = useMemo(() => {
    if (heatmapData) return heatmapData;
    
    const count = rows * cols;
    const generated = [];
    for (let i = 0; i < count; i++) {
      // Generate intensity 0-4
      // Bias towards lower intensity
      const rand = Math.random();
      let intensity = 0;
      if (rand > 0.5) intensity = 1;
      if (rand > 0.75) intensity = 2;
      if (rand > 0.9) intensity = 3;
      if (rand > 0.95) intensity = 4;
      generated.push(intensity);
    }
    return generated;
  }, [rows, cols, heatmapData]);

  const getIntensityClass = (intensity) => {
    switch (intensity) {
      case 1: return styles.intensity1;
      case 2: return styles.intensity2;
      case 3: return styles.intensity3;
      case 4: return styles.intensity4;
      default: return styles.intensity0;
    }
  };

  return (
    <div className={styles.heatmapContainer}>
      <div 
        className={styles.grid}
        style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}
      >
        {data.map((intensity, index) => (
          <div 
            key={index} 
            className={`${styles.cell} ${getIntensityClass(intensity)}`} 
          />
        ))}
      </div>
      
      <div className={styles.legend}>
        <span className={styles.legendText}>Less</span>
        <div className={styles.legendScale}>
          <div className={`${styles.legendCell} ${styles.intensity0}`} />
          <div className={`${styles.legendCell} ${styles.intensity1}`} />
          <div className={`${styles.legendCell} ${styles.intensity2}`} />
          <div className={`${styles.legendCell} ${styles.intensity3}`} />
          <div className={`${styles.legendCell} ${styles.intensity4}`} />
        </div>
        <span className={styles.legendText}>More</span>
      </div>
    </div>
  );
}
