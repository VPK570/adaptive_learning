import React from 'react';
import { FileText, File, MonitorPlay } from 'lucide-react';
import styles from './FileTypeIcon.module.css';

export default function FileTypeIcon({ filename, isProcessing }) {
  const getExtension = (name) => {
    if (!name) return '';
    const parts = name.split('.');
    return parts[parts.length - 1].toLowerCase();
  };

  const ext = getExtension(filename);
  
  let Icon = File;
  let colorClass = styles.defaultColor;

  if (ext === 'pdf') {
    Icon = FileText;
    colorClass = styles.pdfColor;
  } else if (ext === 'pptx' || ext === 'ppt') {
    Icon = MonitorPlay;
    colorClass = styles.pptColor;
  } else if (ext === 'docx' || ext === 'doc') {
    Icon = FileText;
    colorClass = styles.docColor;
  }

  return (
    <div className={`${styles.iconTile} ${colorClass} ${isProcessing ? styles.processing : ''}`}>
      <Icon size={20} />
      {isProcessing && <div className={styles.spinner}></div>}
    </div>
  );
}
