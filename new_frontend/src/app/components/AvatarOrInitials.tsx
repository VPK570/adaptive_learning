import React from 'react';
import { User } from 'lucide-react';
import styles from './AvatarOrInitials.module.css';

export default function AvatarOrInitials({ name, avatarUrl, initials, role }: { name?: any, avatarUrl?: any, initials?: any, role?: any }) {
  const getInitials = (nameStr) => {
    if (!nameStr) return '?';
    const parts = nameStr.split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return nameStr.substring(0, 2).toUpperCase();
  };

  const displayInitials = initials || getInitials(name);

  // Generate a consistent hue based on the name string for the background
  const getBgColor = (str) => {
    if (!str) return 'var(--color-primary-container)';
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    const h = Math.abs(hash) % 360;
    // use HSL to pick a nice soft tone
    return `hsl(${h}, 50%, 25%)`;
  };

  return (
    <div className={styles.avatarWrapper}>
      {avatarUrl ? (
        <img src={avatarUrl} alt={name} className={styles.avatarImage} />
      ) : (
        <div className={styles.initialsCircle} style={{ backgroundColor: getBgColor(name) }}>
          {displayInitials}
        </div>
      )}
    </div>
  );
}
