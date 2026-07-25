import React from 'react';
import { Download, RefreshCcw } from 'lucide-react';
import BloomPill from './BloomPill';
import Badge from './Badge';
import styles from './PaperPreview.module.css';

export default function PaperPreview({ courseTitle, questions = [] }) {
  return (
    <div className={styles.paperContainer}>
      <div className={styles.actionBar}>
        <span className={styles.docTitle}>{courseTitle} - Question Paper</span>
        <div className={styles.actions}>
          <button className={styles.actionBtn}>
            <RefreshCcw size={16} />
            <span>Regenerate All</span>
          </button>
          <button className={styles.primaryBtn}>
            <Download size={16} />
            <span>Export PDF</span>
          </button>
        </div>
      </div>
      
      {questions.length === 0 ? (
        <div className={styles.documentWrapper}>
          <div className={styles.document}>
            <p style={{ textAlign: 'center', color: 'var(--color-on-surface-variant)', padding: 'var(--space-10)' }}>No questions generated yet.</p>
          </div>
        </div>
      ) : (
        <div className={styles.documentWrapper}>
          <div className={styles.document}>
            <h1 className={styles.paperTitle}>{courseTitle}</h1>
            <h2 className={styles.paperSubtitle}>Generated Question Paper</h2>
            
            <div className={styles.questionList}>
              {questions.map((q, i) => (
                <div key={i} className={styles.questionBlock}>
                  <div className={styles.questionHeader}>
                    <span className={styles.qNumber}>Q{i + 1}.</span>
                    <div className={styles.qMeta}>
                      <BloomPill tier={q.bloomTier} />
                      {q.chunks && <Badge variant="mono-chip">{q.chunks} chunks</Badge>}
                    </div>
                  </div>
                  <p className={styles.qText}>{q.text}</p>
                  <div className={styles.qActions}>
                    <button className={styles.textBtn}>Regenerate</button>
                    <button className={styles.textBtn}>Edit</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
