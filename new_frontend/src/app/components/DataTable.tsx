import React from 'react';
import { MoreHorizontal, Edit, Edit2, Pencil } from 'lucide-react';
import Badge from './Badge';
import styles from './DataTable.module.css';

export default function DataTable({ 
  columns, 
  data, 
  onViewAll,
  viewAllLabel = 'View All'
}) {
  // columns: [{ key: 'name', label: 'Name' }, ...]
  
  return (
    <div className={styles.tableContainer}>
      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              {columns.map(col => (
                <th key={col.key} className={styles.th}>{col.label}</th>
              ))}
              <th className={styles.th}></th> {/* For trailing actions */}
            </tr>
          </thead>
          <tbody>
            {data.length === 0 ? (
              <tr>
                <td colSpan={columns.length + 1} style={{ textAlign: 'center', padding: 'var(--space-10)', color: 'var(--color-on-surface-variant)', font: 'var(--text-body-md)' }}>
                  No data yet.
                </td>
              </tr>
            ) : (
              data.map((row, i) => (
                <tr key={row.id || i} className={styles.tr}>
                  {columns.map(col => (
                    <td key={col.key} className={styles.td}>
                      {col.render ? col.render(row[col.key], row) : row[col.key]}
                    </td>
                  ))}
                  <td className={`${styles.td} ${styles.actionCell}`}>
                    <button className={styles.actionBtn}>
                      <Pencil size={16} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {onViewAll && (
        <div className={styles.footer}>
          <button className={styles.viewAllBtn} onClick={onViewAll}>
            {viewAllLabel}
          </button>
        </div>
      )}
    </div>
  );
}
