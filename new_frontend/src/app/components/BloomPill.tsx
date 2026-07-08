import React from 'react';
import styles from './BloomPill.module.css';

export default function BloomPill({ tier }) {
  // tier: "Remember" | "Understand" | "Apply" | "Analyze" | "Evaluate" | "Create"
  
  const getTierClass = (t) => {
    switch (t.toLowerCase()) {
      case 'remember': return styles.remember;
      case 'understand': return styles.understand;
      case 'apply': return styles.apply;
      case 'analyze': return styles.analyze;
      case 'evaluate': return styles.evaluate;
      case 'create': return styles.create;
      default: return styles.default;
    }
  };

  return (
    <span className={`${styles.pill} ${getTierClass(tier)}`}>
      {tier}
    </span>
  );
}
